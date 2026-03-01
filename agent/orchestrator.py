"""
agent/orchestrator.py — OrchestratorAgent: 7-step pipeline execution.

STRICT ORDER (never skip or reorder):
1. create_ticket
2+3. get_customer_history + search_knowledge_base (parallel)
4. analyze_sentiment
5. decide_escalation
    5a. (conditional) escalate_to_human
6. format_response (skipped if escalated)
7. send_response

Error handling per error taxonomy:
- E001: timeout → retry once after 500ms
- E002: not found → return None, proceed
- E003: guardrail → escalate
- E004: format fail → reformat once
- E005: auth → alert + escalate
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agent.sub_agents.escalation_agent import EscalationAgent
from agent.sub_agents.kb_agent import KBAgent
from agent.sub_agents.sentiment_agent import SentimentAgent
from agent.tools.create_ticket import CreateTicketInput, create_ticket
from agent.tools.escalate_to_human import escalate_to_human
from agent.tools.format_for_channel import format_for_channel
from agent.tools.get_customer_history import get_customer_history
from agent.tools.send_response import SendResult, compute_response_hash, send_response
from channels.webform.handler import IntakeEvent
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
openai_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)

# Circuit breaker: track consecutive failures per tool
_circuit_breaker: dict[str, int] = {}
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_RESET_AFTER = 60  # seconds
_circuit_open_until: dict[str, float] = {}


@dataclass
class PipelineResult:
    """Full result of a pipeline execution."""
    ticket_id: Optional[uuid.UUID]
    customer_id: Optional[uuid.UUID]
    channel: str
    response_text: Optional[str]
    escalated: bool
    escalation_rule: Optional[str]
    pipeline_log: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    total_duration_ms: int = 0


async def call_tool_with_retry(
    tool_fn,
    *args,
    tool_name: str = "unknown",
    timeout: float = 3.0,
    **kwargs,
):
    """
    Wrapper that handles tool execution with error taxonomy:
    - E001 (timeout): retry once after 500ms
    - E002 (not found): return None, do not raise
    - E003 (guardrail): re-raise for escalation handling
    - E004 (format fail): caller handles
    - E005 (auth fail): alert and re-raise
    """
    # Check circuit breaker
    now = time.monotonic()
    if tool_name in _circuit_open_until:
        if now < _circuit_open_until[tool_name]:
            logger.warning("Circuit breaker OPEN for %s — skipping", tool_name)
            return None
        else:
            # Reset circuit breaker
            del _circuit_open_until[tool_name]
            _circuit_breaker[tool_name] = 0

    async def _execute():
        return await asyncio.wait_for(tool_fn(*args, **kwargs), timeout=timeout)

    try:
        result = await _execute()
        # Reset failure count on success
        _circuit_breaker[tool_name] = 0
        return result

    except asyncio.TimeoutError:
        logger.warning("E001: %s timed out, retrying after 500ms...", tool_name)
        await asyncio.sleep(0.5)
        try:
            result = await _execute()
            _circuit_breaker[tool_name] = 0
            return result
        except asyncio.TimeoutError:
            _circuit_breaker[tool_name] = _circuit_breaker.get(tool_name, 0) + 1
            if _circuit_breaker[tool_name] >= CIRCUIT_BREAKER_THRESHOLD:
                _circuit_open_until[tool_name] = now + CIRCUIT_BREAKER_RESET_AFTER
                logger.error(
                    "Circuit breaker OPENED for %s after %d consecutive failures",
                    tool_name,
                    CIRCUIT_BREAKER_THRESHOLD,
                )
            raise TimeoutError(f"E001: {tool_name} timed out after retry")

    except Exception as e:
        error_str = str(e).lower()
        if "authentication" in error_str or "auth" in error_str or "credentials" in error_str:
            logger.critical("E005: Auth failure in %s — escalating", tool_name)
            raise
        elif "not found" in error_str or "no result" in error_str:
            logger.debug("E002: %s returned not-found — proceeding with None", tool_name)
            return None
        else:
            _circuit_breaker[tool_name] = _circuit_breaker.get(tool_name, 0) + 1
            raise


async def _generate_ai_response(
    raw_message: str,
    kb_results: list,
    customer_history,
    channel: str,
) -> str:
    """
    Generate AI response using GPT-4o with KB context and customer history.
    """
    # Build context from KB results
    kb_context = ""
    if kb_results:
        kb_context = "\n\nRelevant knowledge base articles:\n"
        for i, kb in enumerate(kb_results[:3], 1):
            kb_context += f"\n{i}. {kb.title}:\n{kb.content[:500]}\n"

    # Build customer context
    customer_context = ""
    if customer_history and customer_history.customer:
        name = customer_history.customer.display_name
        if name:
            customer_context = f"\nCustomer name: {name}"
        if customer_history.open_ticket_count > 0:
            customer_context += f"\nCustomer has {customer_history.open_ticket_count} open ticket(s)"

    # Channel-appropriate response guidance
    channel_guidance = {
        "email": "Write a formal, detailed response. Use proper paragraphs.",
        "whatsapp": "Write a brief, conversational response. Maximum 2-3 short sentences.",
        "webform": "Write a clear, helpful response. Use bullet points if explaining steps.",
    }

    system_prompt = f"""You are a helpful customer success AI agent. Answer the customer's question accurately and helpfully.

Channel: {channel}
Style: {channel_guidance.get(channel, 'helpful and professional')}
{customer_context}

Important rules:
- Only answer based on the provided knowledge base content
- If the KB doesn't cover the question, acknowledge and offer to connect with a specialist
- Do NOT make up features or pricing
- Do NOT mention competitors
- Be empathetic and professional
- Do NOT include greetings or sign-offs (these are added separately){kb_context}"""

    response = await openai_client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_message},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()


class OrchestratorAgent:
    """
    7-step pipeline orchestrator for customer support inquiries.

    Enforces strict step ordering, parallel execution for steps 2+3,
    and escalation guardrails at step 5.
    """

    def __init__(self):
        self.sentiment_agent = SentimentAgent()
        self.kb_agent = KBAgent()
        self.escalation_agent = EscalationAgent()

    async def run(
        self,
        session: AsyncSession,
        intake_event: IntakeEvent,
        kafka_producer=None,
    ) -> PipelineResult:
        """
        Execute the full 7-step pipeline for an intake event.

        Steps 2+3 run in parallel (asyncio.gather).
        Pipeline halts at step 5 if escalation is triggered.
        All step results are logged to pipeline_log.
        """
        pipeline_start = time.monotonic()
        pipeline_log = []
        customer_id = intake_event.customer_id
        ticket_id = None
        channel = intake_event.channel

        try:
            # =================================================================
            # STEP 1: Create Ticket
            # =================================================================
            step1_start = time.monotonic()
            pipeline_log.append({"step": 1, "name": "create_ticket", "status": "starting"})

            from database.repositories.customer_repo import resolve_or_create_customer
            if not customer_id:
                customer_id, was_created = await resolve_or_create_customer(
                    session=session,
                    identifiers=intake_event.customer_identifiers,
                    display_name=intake_event.customer_name,
                )
                intake_event.customer_id = customer_id

            ticket_input = CreateTicketInput(
                customer_id=customer_id,
                channel=channel,
                raw_content=intake_event.raw_content,
                content_hash=intake_event.content_hash,
                subject=intake_event.channel_metadata.subject if intake_event.channel_metadata else None,
            )

            ticket_result = await call_tool_with_retry(
                create_ticket,
                session,
                ticket_input,
                kafka_producer,
                tool_name="create_ticket",
                timeout=5.0,
            )

            if not ticket_result:
                raise RuntimeError("Step 1 (create_ticket) returned None — cannot proceed")

            ticket_id = ticket_result.ticket_id
            intake_event.ticket_id = ticket_id

            pipeline_log.append({
                "step": 1, "name": "create_ticket", "status": "success",
                "ticket_id": str(ticket_id),
                "duplicate": ticket_result.duplicate,
                "duration_ms": int((time.monotonic() - step1_start) * 1000),
            })

            # =================================================================
            # STEPS 2+3: Customer History + KB Search (PARALLEL)
            # =================================================================
            steps23_start = time.monotonic()
            pipeline_log.append({"step": "2+3", "name": "parallel_gather", "status": "starting"})

            history_task = get_customer_history(
                session=session,
                customer_id=customer_id,
                kafka_producer=kafka_producer,
            )
            kb_task = self.kb_agent.run(
                query=intake_event.raw_content,
                session=session,
                ticket_id=ticket_id,
                kafka_producer=kafka_producer,
            )

            customer_history, kb_result = await asyncio.gather(
                history_task, kb_task, return_exceptions=True
            )

            # Handle exceptions from gather (E002: proceed with None)
            if isinstance(customer_history, Exception):
                logger.warning("Step 2 failed: %s", customer_history)
                customer_history = None
            if isinstance(kb_result, Exception):
                logger.warning("Step 3 failed: %s", kb_result)
                kb_result = None

            pipeline_log.append({
                "step": "2+3", "name": "parallel_gather", "status": "success",
                "history_found": customer_history is not None and customer_history.customer is not None,
                "kb_miss": kb_result.kb_miss if kb_result else True,
                "kb_results_count": len(kb_result.results) if kb_result and not kb_result.kb_miss else 0,
                "duration_ms": int((time.monotonic() - steps23_start) * 1000),
            })

            # =================================================================
            # STEP 4: Analyze Sentiment
            # =================================================================
            step4_start = time.monotonic()
            pipeline_log.append({"step": 4, "name": "analyze_sentiment", "status": "starting"})

            try:
                sentiment_result = await self.sentiment_agent.run(
                    text=intake_event.raw_content,
                    ticket_id=ticket_id,
                    kafka_producer=kafka_producer,
                )
            except Exception as e:
                logger.warning("Step 4 (sentiment) failed, defaulting to neutral: %s", e)
                from agent.tools.analyze_sentiment import SentimentResult
                sentiment_result = SentimentResult(
                    score=0.5, label="neutral", profanity_detected=False, escalate=False
                )

            pipeline_log.append({
                "step": 4, "name": "analyze_sentiment", "status": "success",
                "score": sentiment_result.score,
                "label": sentiment_result.label,
                "escalate": sentiment_result.escalate,
                "duration_ms": int((time.monotonic() - step4_start) * 1000),
            })

            # =================================================================
            # STEP 5: Decide Escalation
            # =================================================================
            step5_start = time.monotonic()
            pipeline_log.append({"step": 5, "name": "decide_escalation", "status": "starting"})

            escalation_decision = await self.escalation_agent.run(
                text=intake_event.raw_content,
                sentiment_score=sentiment_result.score,
                profanity_detected=sentiment_result.profanity_detected,
            )

            pipeline_log.append({
                "step": 5, "name": "decide_escalation", "status": "success",
                "should_escalate": escalation_decision.should_escalate,
                "trigger_rule": escalation_decision.trigger_rule,
                "priority": escalation_decision.priority,
                "duration_ms": int((time.monotonic() - step5_start) * 1000),
            })

            # =================================================================
            # STEP 5a: Escalate (conditional)
            # =================================================================
            if escalation_decision.should_escalate:
                return await self._handle_escalation(
                    session=session,
                    ticket_id=ticket_id,
                    customer_id=customer_id,
                    channel=channel,
                    escalation_decision=escalation_decision,
                    sentiment_result=sentiment_result,
                    customer_history=customer_history,
                    pipeline_log=pipeline_log,
                    pipeline_start=pipeline_start,
                    kafka_producer=kafka_producer,
                )

            # =================================================================
            # STEP 6: Format Response
            # =================================================================
            step6_start = time.monotonic()
            pipeline_log.append({"step": 6, "name": "format_response", "status": "starting"})

            # Generate AI response
            kb_articles = kb_result.results if kb_result and not kb_result.kb_miss else []
            raw_ai_response = await _generate_ai_response(
                raw_message=intake_event.raw_content,
                kb_results=kb_articles,
                customer_history=customer_history,
                channel=channel,
            )

            # Get customer name for email greeting
            customer_name = None
            if intake_event.customer_name:
                customer_name = intake_event.customer_name
            elif customer_history and customer_history.customer:
                customer_name = customer_history.customer.display_name

            # Format for channel
            formatted = format_for_channel(
                raw=raw_ai_response,
                channel=channel,
                customer_name=customer_name,
            )

            # E004: If format failed after retry, escalate
            if not formatted.within_limits:
                logger.warning("E004: Format failed for ticket %s — escalating", ticket_id)
                from agent.sub_agents.escalation_agent import EscalationDecision
                return await self._handle_escalation(
                    session=session,
                    ticket_id=ticket_id,
                    customer_id=customer_id,
                    channel=channel,
                    escalation_decision=EscalationDecision(
                        should_escalate=True,
                        trigger_rule="undocumented",
                        trigger_detail="Response format failed: " + (formatted.error or ""),
                        priority="P3",
                    ),
                    sentiment_result=sentiment_result,
                    customer_history=customer_history,
                    pipeline_log=pipeline_log,
                    pipeline_start=pipeline_start,
                    kafka_producer=kafka_producer,
                )

            pipeline_log.append({
                "step": 6, "name": "format_response", "status": "success",
                "within_limits": formatted.within_limits,
                "word_count": formatted.word_count,
                "char_count": formatted.char_count,
                "duration_ms": int((time.monotonic() - step6_start) * 1000),
            })

            # =================================================================
            # STEP 7: Send Response
            # =================================================================
            step7_start = time.monotonic()
            pipeline_log.append({"step": 7, "name": "send_response", "status": "starting"})

            response_hash = compute_response_hash(formatted.text)
            kb_article_ids = [str(kb.article_id) for kb in kb_articles]

            send_result = await call_tool_with_retry(
                send_response,
                session,
                ticket_id,
                channel,
                formatted.text,
                response_hash,
                {
                    "kb_article_ids": kb_article_ids,
                    "sentiment_score": sentiment_result.score,
                    "is_escalation_holding_message": False,
                },
                kafka_producer,
                tool_name="send_response",
                timeout=5.0,
            )

            pipeline_log.append({
                "step": 7, "name": "send_response", "status": "success",
                "message_id": send_result.message_id if send_result else None,
                "duplicate": send_result.duplicate if send_result else False,
                "duration_ms": int((time.monotonic() - step7_start) * 1000),
            })

            total_duration_ms = int((time.monotonic() - pipeline_start) * 1000)
            logger.info(
                '{"event":"pipeline_complete","ticket_id":"%s","channel":"%s",'
                '"escalated":false,"total_duration_ms":%d}',
                ticket_id,
                channel,
                total_duration_ms,
            )

            return PipelineResult(
                ticket_id=ticket_id,
                customer_id=customer_id,
                channel=channel,
                response_text=formatted.text,
                escalated=False,
                escalation_rule=None,
                pipeline_log=pipeline_log,
                total_duration_ms=total_duration_ms,
            )

        except Exception as e:
            total_duration_ms = int((time.monotonic() - pipeline_start) * 1000)
            logger.error(
                '{"event":"pipeline_error","ticket_id":"%s","channel":"%s",'
                '"error":"%s","total_duration_ms":%d}',
                str(ticket_id) if ticket_id else "none",
                channel,
                str(e)[:200],
                total_duration_ms,
            )
            pipeline_log.append({
                "step": "error",
                "error": str(e)[:200],
                "duration_ms": total_duration_ms,
            })
            return PipelineResult(
                ticket_id=ticket_id,
                customer_id=customer_id,
                channel=channel,
                response_text=None,
                escalated=True,
                escalation_rule="system_error",
                pipeline_log=pipeline_log,
                error=str(e),
                total_duration_ms=total_duration_ms,
            )

    async def _handle_escalation(
        self,
        session: AsyncSession,
        ticket_id: uuid.UUID,
        customer_id: uuid.UUID,
        channel: str,
        escalation_decision,
        sentiment_result,
        customer_history,
        pipeline_log: list,
        pipeline_start: float,
        kafka_producer=None,
    ) -> PipelineResult:
        """Execute escalation path (step 5a + step 7 with holding message)."""
        step5a_start = time.monotonic()

        # Build conversation context for human agent
        context_parts = []
        if customer_history and customer_history.customer:
            context_parts.append(
                f"Customer: {customer_history.customer.display_name or 'Unknown'}"
            )
            context_parts.append(
                f"Prior tickets: {len(customer_history.tickets)}"
            )
        context_parts.append(f"Trigger: {escalation_decision.trigger_rule}")
        context_parts.append(f"Sentiment: {sentiment_result.score:.3f}")

        escalation_result = await escalate_to_human(
            session=session,
            ticket_id=ticket_id,
            trigger_rule=escalation_decision.trigger_rule,
            trigger_detail=escalation_decision.trigger_detail or "",
            sentiment_score=sentiment_result.score,
            priority=escalation_decision.priority,
            channel=channel,
            conversation_context="\n".join(context_parts),
            kafka_producer=kafka_producer,
        )

        pipeline_log.append({
            "step": "5a", "name": "escalate_to_human", "status": "success",
            "escalation_id": escalation_result.escalation_id,
            "already_escalated": escalation_result.already_escalated,
            "duration_ms": int((time.monotonic() - step5a_start) * 1000),
        })

        # Step 7: Send holding message
        holding_message = escalation_result.customer_message
        if not holding_message:
            # Fallback holding message
            from agent.tools.escalate_to_human import _build_holding_message
            holding_message = _build_holding_message(channel, ticket_id)

        step7_start = time.monotonic()
        response_hash = compute_response_hash(holding_message)

        try:
            await send_response(
                session=session,
                ticket_id=ticket_id,
                channel=channel,
                response_text=holding_message,
                response_hash=response_hash,
                metadata={
                    "sentiment_score": sentiment_result.score,
                    "is_escalation_holding_message": True,
                },
                kafka_producer=kafka_producer,
            )
        except Exception as e:
            logger.warning("Failed to send escalation holding message: %s", e)

        pipeline_log.append({
            "step": 7, "name": "send_response (holding)", "status": "success",
            "duration_ms": int((time.monotonic() - step7_start) * 1000),
        })

        total_duration_ms = int((time.monotonic() - pipeline_start) * 1000)
        logger.info(
            '{"event":"pipeline_escalated","ticket_id":"%s","channel":"%s",'
            '"trigger_rule":"%s","priority":"%s","total_duration_ms":%d}',
            ticket_id,
            channel,
            escalation_decision.trigger_rule,
            escalation_decision.priority,
            total_duration_ms,
        )

        return PipelineResult(
            ticket_id=ticket_id,
            customer_id=customer_id,
            channel=channel,
            response_text=holding_message,
            escalated=True,
            escalation_rule=escalation_decision.trigger_rule,
            pipeline_log=pipeline_log,
            total_duration_ms=total_duration_ms,
        )
