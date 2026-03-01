"""
database/repositories/customer_repo.py — Customer identity resolution and CRUD.

Core function: resolve_or_create_customer
  - Normalises identifiers (email lowercase, phone E.164, wa_id strip prefix)
  - Looks up by any provided identifier
  - Creates new customer if not found
  - Links any new identifiers to existing customer if found
  - Uses SELECT FOR UPDATE to prevent race conditions
"""

import logging
import uuid
from typing import Optional

import phonenumbers
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Customer, CustomerIdentifier

logger = logging.getLogger(__name__)


def normalise_email(email: str) -> str:
    """Normalise email: lowercase and strip whitespace."""
    return email.lower().strip()


def normalise_phone(phone: str) -> Optional[str]:
    """
    Normalise phone number to E.164 format using phonenumbers library.
    Returns None if the phone number is invalid.

    Examples:
        "+1 (415) 555-1234" -> "+14155551234"
        "4155551234"        -> "+14155551234" (assumes US)
        "+44 20 7946 0958"  -> "+442079460958"
    """
    if not phone:
        return None
    try:
        # Try parsing as-is first (works if country code is included)
        parsed = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed):
            # Try with US as default country
            parsed = phonenumbers.parse(phone, "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except phonenumbers.NumberParseException:
        try:
            # Last attempt: assume US
            parsed = phonenumbers.parse(phone, "US")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                )
        except phonenumbers.NumberParseException:
            pass
    return None


def normalise_whatsapp_id(wa_id: str) -> str:
    """
    Strip 'whatsapp:' prefix from WhatsApp ID.
    Twilio sends numbers as "whatsapp:+14155552671".
    """
    if wa_id.startswith("whatsapp:"):
        wa_id = wa_id[len("whatsapp:"):]
    return wa_id.strip()


def normalise_identifiers(raw_identifiers: dict) -> dict[str, str]:
    """
    Normalise all provided identifiers.
    Returns only non-None, non-empty normalised values.
    """
    normalised = {}

    if email := raw_identifiers.get("email"):
        normalised["email"] = normalise_email(email)

    if phone := raw_identifiers.get("phone"):
        e164 = normalise_phone(phone)
        if e164:
            normalised["phone"] = e164

    if wa_id := raw_identifiers.get("whatsapp_id"):
        normalised["whatsapp_id"] = normalise_whatsapp_id(wa_id)

    if session_id := raw_identifiers.get("web_session"):
        normalised["web_session"] = session_id.strip()

    return normalised


async def resolve_or_create_customer(
    session: AsyncSession,
    identifiers: dict,
    display_name: Optional[str] = None,
    company: Optional[str] = None,
) -> tuple[uuid.UUID, bool]:
    """
    Resolve or create a customer based on provided identifiers.

    Algorithm:
    1. Normalise all identifiers
    2. SELECT FOR UPDATE lookup in customer_identifiers
    3a. Found: link any new identifiers, return existing customer_id
    3b. Not found: INSERT new customer + all identifiers, return new id

    Returns:
        (customer_id, was_created)
        was_created=True means a new customer record was created
        was_created=False means an existing customer was found

    Thread safety: SELECT FOR UPDATE prevents duplicate creation
    under concurrent requests from the same customer.
    """
    normalised = normalise_identifiers(identifiers)

    if not normalised:
        raise ValueError("At least one identifier must be provided")

    # Build list of (type, value) pairs for lookup
    lookup_pairs = list(normalised.items())  # [(id_type, id_value), ...]

    # Step 1: Look up by any of the provided identifiers using OR expansion.
    # asyncpg does not support tuple-IN binding, so we expand into OR clauses
    # with numbered bind parameters and append FOR UPDATE for row-level locking.
    conditions = " OR ".join(
        f"(identifier_type = :type_{i} AND identifier_value = :value_{i})"
        for i in range(len(lookup_pairs))
    )
    params: dict = {}
    for i, (id_type, id_value) in enumerate(lookup_pairs):
        params[f"type_{i}"] = id_type
        params[f"value_{i}"] = id_value

    raw_stmt = text(f"""
        SELECT customer_id
        FROM customer_identifiers
        WHERE {conditions}
        LIMIT 1
        FOR UPDATE
    """)

    result = await session.execute(raw_stmt, params)
    row = result.fetchone()

    if row:
        # Customer found — link any missing identifiers
        customer_id = row[0]
        await _link_missing_identifiers(session, customer_id, normalised)
        logger.debug("Resolved existing customer %s", customer_id)
        return customer_id, False
    else:
        # Customer not found — create new customer + identifiers
        customer_id = await _create_customer(
            session, normalised, display_name, company
        )
        logger.info("Created new customer %s", customer_id)
        return customer_id, True


async def _create_customer(
    session: AsyncSession,
    normalised: dict[str, str],
    display_name: Optional[str],
    company: Optional[str],
) -> uuid.UUID:
    """Create a new customer record with all provided identifiers."""
    new_id = uuid.uuid4()

    customer = Customer(
        id=new_id,
        display_name=display_name,
        company=company,
        primary_email=normalised.get("email"),
        primary_phone=normalised.get("phone") or normalised.get("whatsapp_id"),
    )
    session.add(customer)
    await session.flush()  # Get the ID without committing

    # Create all identifier records
    for id_type, id_value in normalised.items():
        identifier = CustomerIdentifier(
            customer_id=new_id,
            identifier_type=id_type,
            identifier_value=id_value,
        )
        session.add(identifier)

    await session.commit()
    return new_id


async def _link_missing_identifiers(
    session: AsyncSession,
    customer_id: uuid.UUID,
    normalised: dict[str, str],
) -> None:
    """Add any identifiers not yet linked to this customer."""
    for id_type, id_value in normalised.items():
        # Check if this identifier already exists for this customer
        existing = await session.execute(
            select(CustomerIdentifier).where(
                CustomerIdentifier.customer_id == customer_id,
                CustomerIdentifier.identifier_type == id_type,
                CustomerIdentifier.identifier_value == id_value,
            )
        )
        if not existing.scalar_one_or_none():
            # Also check if this identifier belongs to another customer
            other = await session.execute(
                select(CustomerIdentifier).where(
                    CustomerIdentifier.identifier_type == id_type,
                    CustomerIdentifier.identifier_value == id_value,
                )
            )
            if not other.scalar_one_or_none():
                session.add(
                    CustomerIdentifier(
                        customer_id=customer_id,
                        identifier_type=id_type,
                        identifier_value=id_value,
                    )
                )

    await session.commit()


async def get_customer_by_id(
    session: AsyncSession, customer_id: uuid.UUID
) -> Optional[Customer]:
    """Fetch a customer record by ID."""
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    return result.scalar_one_or_none()
