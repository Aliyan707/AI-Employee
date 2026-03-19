"""
AI Employee Operations Hub — Full-Stack Dashboard
Flask backend + Single-Page App frontend
Port: 5501
"""

import os, re, json, shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, Response, jsonify, request

VAULT = Path(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

def read_file(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="ignore")
    except:
        return ""

def list_files(folder, ext=".md"):
    d = VAULT / folder
    if not d.exists():
        return []
    return sorted([f for f in d.iterdir() if f.suffix == ext], reverse=True)

def list_files_recursive(folder, ext=".md"):
    d = VAULT / folder
    if not d.exists():
        return []
    return sorted(d.rglob(f"*{ext}"), reverse=True)

# ── API: Dashboard ────────────────────────────────────────────────────────────

@app.route("/api/dashboard")
def api_dashboard():
    raw = read_file(VAULT / "Dashboard.md")
    def pick(pattern, fallback="—"):
        m = re.search(pattern, raw)
        return m.group(1).strip() if m else fallback

    social_done = list_files_recursive("Done/Social")
    pending_files = list_files_recursive("Pending_Approval")
    log_files = list_files("Logs")
    agent_files = list(( VAULT / ".claude/agents").glob("*.md")) if (VAULT / ".claude/agents").exists() else []

    return jsonify({
        "last_active":        pick(r"Last Active:\s*(.+)"),
        "pending_approvals":  pick(r"Pending Approvals:\s*(.+)"),
        "errors_today":       pick(r"Errors Today:\s*(.+)"),
        "revenue_mtd":        pick(r"Current MTD:\s*(.+)"),
        "monthly_goal":       pick(r"Monthly Goal:\s*(.+)"),
        "q1_target":          pick(r"Q1 Target:\s*(.+)"),
        "pipeline":           pick(r"Pipeline:\s*(.+)"),
        "social_queue":       pick(r"Items in Social Queue:\s*(.+)"),
        "uptime":             pick(r"Uptime:\s*(.+)"),
        "health":             pick(r"filesystem_watcher:\s*(.+)"),
        "violations":         pick(r"Constitutional Violations:\s*(.+)"),
        "stats": {
            "social_posted":    len(social_done),
            "pending_count":    len(pending_files),
            "log_count":        len(log_files),
            "agent_count":      len(agent_files),
        }
    })

# ── API: Approvals ────────────────────────────────────────────────────────────

@app.route("/api/approvals")
def api_approvals():
    items = []
    for f in list_files_recursive("Pending_Approval"):
        content = read_file(f)
        rel = str(f.relative_to(VAULT)).replace("\\", "/")
        m = re.search(r"sensitivity:\s*(\w+)", content)
        sensitivity = m.group(1) if m else "medium"
        m2 = re.search(r"platform:\s*(\w+)", content)
        platform = m2.group(1) if m2 else "general"
        stat = f.stat()
        age_h = round((datetime.now().timestamp() - stat.st_mtime) / 3600, 1)
        preview = content[:200].replace("\n", " ").strip()
        items.append({
            "filename": f.name,
            "path": rel,
            "sensitivity": sensitivity,
            "platform": platform,
            "age_hours": age_h,
            "preview": preview,
            "size": stat.st_size,
        })
    return jsonify(items)

@app.route("/api/approvals/approve", methods=["POST"])
def approve_item():
    data = request.json
    src = VAULT / data.get("path", "")
    if not src.exists():
        return jsonify({"ok": False, "error": "File not found"})
    rel = str(src.relative_to(VAULT / "Pending_Approval")).replace("\\", "/")
    dst_dir = VAULT / "Approved" / Path(rel).parent
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.move(str(src), str(dst))
    return jsonify({"ok": True, "moved_to": str(dst.relative_to(VAULT))})

@app.route("/api/approvals/reject", methods=["POST"])
def reject_item():
    data = request.json
    src = VAULT / data.get("path", "")
    if not src.exists():
        return jsonify({"ok": False, "error": "File not found"})
    dst_dir = VAULT / "Done" / "Rejected"
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst_dir / src.name))
    return jsonify({"ok": True})

# ── API: Logs ─────────────────────────────────────────────────────────────────

@app.route("/api/logs")
def api_logs():
    items = []
    for f in list_files("Logs"):
        content = read_file(f)
        items.append({"filename": f.name, "content": content[:3000], "size": f.stat().st_size})
    return jsonify(items)

# ── API: AI Bots ──────────────────────────────────────────────────────────────

@app.route("/api/bots")
def api_bots():
    agents_dir = VAULT / ".claude" / "agents"
    bots = []
    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            content = read_file(f)
            desc_m = re.search(r"description:\s*(.+)", content)
            desc = desc_m.group(1).strip() if desc_m else content[:120].strip()
            bots.append({"name": f.stem, "description": desc, "file": f.name})
    return jsonify(bots)

# ── API: Social ───────────────────────────────────────────────────────────────

@app.route("/api/social")
def api_social():
    posted, pending = [], []
    for f in list_files_recursive("Done/Social"):
        c = read_file(f)
        m = re.search(r"platform:\s*(\w[\w/X]*)", c)
        plat = m.group(1) if m else f.stem.split("_")[0].upper()
        posted.append({"filename": f.name, "platform": plat,
                        "date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "preview": c[:150].replace("\n"," ").strip()})
    for f in list_files_recursive("Pending_Approval/Social") if (VAULT/"Pending_Approval/Social").exists() else []:
        c = read_file(f)
        m = re.search(r"platform:\s*(\w[\w/X]*)", c)
        plat = m.group(1) if m else "unknown"
        pending.append({"filename": f.name, "platform": plat,
                         "preview": c[:150].replace("\n"," ").strip()})
    return jsonify({"posted": posted, "pending": pending})

@app.route("/api/social/draft", methods=["POST"])
def social_draft():
    data = request.json
    platform = data.get("platform", "linkedin")
    content  = data.get("content", "")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"DRAFT_{platform.upper()}_{ts}.md"
    out = VAULT / "Pending_Approval" / "Social" / fname
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""---
platform: {platform}
post_type: manual_draft
sensitivity: medium
requires_hitl: true
timestamp: {datetime.now().isoformat()}
---

{content}
""", encoding="utf-8")
    return jsonify({"ok": True, "file": fname})

# ── API: Email ────────────────────────────────────────────────────────────────

@app.route("/api/email/send", methods=["POST"])
def email_send():
    data = request.json
    dry_run = data.get("dry_run", True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"EMAIL_DRAFT_{ts}.md"
    out = VAULT / "Needs_Action" / "Email" / fname
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""---
type: email_draft
to: {data.get('to','')}
subject: {data.get('subject','')}
sensitivity: medium
requires_hitl: true
dry_run: {str(dry_run).lower()}
created: {datetime.now().isoformat()}
---

{data.get('body','')}
""", encoding="utf-8")
    return jsonify({"ok": True, "file": fname, "dry_run": dry_run,
                    "message": f"{'[DRY RUN] ' if dry_run else ''}Draft saved to Needs_Action/Email/{fname}"})

# ── API: Finance ──────────────────────────────────────────────────────────────

@app.route("/api/finance")
def api_finance():
    raw = read_file(VAULT / "Dashboard.md")
    def pick(pattern, fallback="—"):
        m = re.search(pattern, raw)
        return m.group(1).strip() if m else fallback
    briefings = []
    for f in list_files("Briefings"):
        briefings.append({"filename": f.name,
                           "date": f.stem,
                           "preview": read_file(f)[:400].replace("\n"," ").strip()})
    return jsonify({
        "revenue_mtd":   pick(r"Current MTD:\s*(.+)"),
        "monthly_goal":  pick(r"Monthly Goal:\s*(.+)"),
        "q1_target":     pick(r"Q1 Target:\s*(.+)"),
        "pipeline":      pick(r"Pipeline:\s*(.+)"),
        "briefings":     briefings,
    })

# ── API: CEO Report ───────────────────────────────────────────────────────────

@app.route("/api/ceo-report")
def api_ceo_report():
    reports = []
    for f in list_files("Briefings"):
        reports.append({"filename": f.name, "date": f.stem, "content": read_file(f)})
    if not reports:
        reports.append({"filename": "pending.md", "date": "Pending",
                         "content": "# CEO Briefing\n\nNo briefings generated yet.\nRun `/ceo-briefing-generator` to generate the first report."})
    return jsonify(reports)

# ── API: Webhooks (stubs) ─────────────────────────────────────────────────────

@app.route("/api/webhooks")
def api_webhooks():
    return jsonify([
        {"name": "Gmail Watcher",      "url": "/webhooks/gmail",      "status": "active",   "last_trigger": "2026-02-20 12:19 PKT", "triggers": 14},
        {"name": "Filesystem Watcher", "url": "/webhooks/filesystem",  "status": "active",   "last_trigger": "2026-02-20 21:45 PKT", "triggers": 32},
        {"name": "Odoo Invoice Hook",  "url": "/webhooks/odoo",        "status": "inactive", "last_trigger": "Never",                "triggers": 0},
        {"name": "WhatsApp Trigger",   "url": "/webhooks/whatsapp",    "status": "inactive", "last_trigger": "Never",                "triggers": 0},
    ])

# ── API: WhatsApp (stub) ──────────────────────────────────────────────────────

@app.route("/api/whatsapp")
def api_whatsapp():
    return jsonify({
        "status": "not_configured",
        "messages": [],
        "note": "WhatsApp watcher not yet configured. Add credentials to watchers/whatsapp_watcher.py"
    })

# ── API: Bank Monitor (stub) ──────────────────────────────────────────────────

@app.route("/api/bank")
def api_bank():
    return jsonify({
        "status": "not_connected",
        "balance": "—",
        "currency": "PKR",
        "transactions": [],
        "note": "Bank API integration pending. Configure bank credentials in .env"
    })

# ── Frontend ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return Response(FRONTEND, mimetype="text/html")

# ─────────────────────────────────────────────────────────────────────────────
FRONTEND = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Employee — Operations Hub</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
/* ── Reset & Tokens ── */
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:    #0b0f1a;
  --navy2:   #0f1623;
  --card:    #131b2e;
  --card2:   #192035;
  --border:  rgba(255,255,255,0.07);
  --border2: rgba(255,255,255,0.12);
  --purple:  #7c3aed;
  --purple2: #8b5cf6;
  --purple3: #a78bfa;
  --purple4: #c4b5fd;
  --cyan:    #06b6d4;
  --green:   #10b981;
  --orange:  #f59e0b;
  --red:     #ef4444;
  --text:    #e2e8f0;
  --muted:   #64748b;
  --muted2:  #94a3b8;
  --sidebar: 220px;
}
html,body{height:100%;background:var(--navy);color:var(--text);font-family:'Inter',sans-serif;font-size:14px}
a{text-decoration:none;color:inherit}
button{cursor:pointer;font-family:inherit}
input,textarea,select{font-family:inherit}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(124,58,237,.4);border-radius:3px}

/* ── Live/DryRun Banner ── */
#banner{
  position:fixed;top:0;left:0;right:0;z-index:200;
  height:38px;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 16px;
  background:linear-gradient(90deg,rgba(11,15,26,0.97),rgba(15,22,35,0.97));
  border-bottom:1px solid var(--border);
  backdrop-filter:blur(12px);
}
.banner-left{display:flex;align-items:center;gap:12px}
.banner-logo{font-size:13px;font-weight:700;letter-spacing:.5px;color:var(--purple3)}
.banner-version{font-size:10px;color:var(--muted);padding:2px 7px;background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.25);border-radius:10px}
.banner-right{display:flex;align-items:center;gap:14px}
.mode-toggle{
  display:flex;align-items:center;gap:8px;
  background:var(--card);border:1px solid var(--border2);border-radius:20px;
  padding:3px;
}
.mode-btn{
  padding:3px 12px;border-radius:16px;font-size:11px;font-weight:600;
  letter-spacing:.4px;border:none;background:transparent;
  color:var(--muted);transition:all .2s;
}
.mode-btn.active-live{background:rgba(16,185,129,.15);color:var(--green);border:1px solid rgba(16,185,129,.3)}
.mode-btn.active-dry{background:rgba(245,158,11,.15);color:var(--orange);border:1px solid rgba(245,158,11,.3)}
#banner-clock{font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums}
.live-dot{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 6px var(--green);animation:pulse 2s infinite;display:inline-block;margin-right:4px}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* ── Shell ── */
.shell{display:flex;height:100vh;padding-top:38px}

/* ── Sidebar ── */
.sidebar{
  width:var(--sidebar);min-width:var(--sidebar);
  background:var(--navy2);
  border-right:1px solid var(--border);
  display:flex;flex-direction:column;
  overflow-y:auto;
  position:fixed;top:38px;left:0;bottom:0;
  z-index:100;
}
.sidebar-header{
  padding:20px 16px 12px;
  border-bottom:1px solid var(--border);
}
.sidebar-title{font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:var(--muted)}
.nav-section{padding:12px 8px 4px}
.nav-section-label{font-size:10px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--muted);padding:0 10px;margin-bottom:4px}
.nav-item{
  display:flex;align-items:center;gap:10px;
  padding:8px 12px;border-radius:8px;
  cursor:pointer;transition:all .18s;
  color:var(--muted2);font-size:13px;font-weight:500;
  position:relative;
}
.nav-item:hover{background:rgba(124,58,237,.1);color:var(--text)}
.nav-item.active{background:rgba(124,58,237,.18);color:var(--purple3)}
.nav-item.active::before{
  content:'';position:absolute;left:0;top:50%;transform:translateY(-50%);
  width:3px;height:20px;border-radius:0 2px 2px 0;
  background:var(--purple2);
}
.nav-icon{font-size:15px;width:20px;text-align:center;flex-shrink:0}
.nav-badge{
  margin-left:auto;font-size:10px;font-weight:700;
  padding:1px 6px;border-radius:8px;
  background:rgba(239,68,68,.2);color:var(--red);
  border:1px solid rgba(239,68,68,.3);
}
.nav-badge.purple{background:rgba(124,58,237,.2);color:var(--purple3);border-color:rgba(124,58,237,.3)}
.sidebar-footer{margin-top:auto;padding:12px 8px;border-top:1px solid var(--border)}

/* ── Main ── */
.main{
  margin-left:var(--sidebar);
  flex:1;display:flex;flex-direction:column;
  min-width:0;
}
/* ── Topbar ── */
.topbar{
  height:54px;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;
  background:rgba(11,15,26,.95);
  border-bottom:1px solid var(--border);
  backdrop-filter:blur(8px);
  flex-shrink:0;
  position:sticky;top:0;z-index:50;
}
.topbar-left h1{font-size:16px;font-weight:700;color:var(--text)}
.topbar-left p{font-size:11px;color:var(--muted);margin-top:1px}
.topbar-right{display:flex;align-items:center;gap:10px}
.top-btn{
  display:flex;align-items:center;gap:6px;
  padding:6px 14px;border-radius:8px;font-size:12px;font-weight:600;
  border:1px solid var(--border2);background:var(--card);
  color:var(--muted2);transition:all .2s;
}
.top-btn:hover{border-color:var(--purple2);color:var(--purple3);background:rgba(124,58,237,.1)}
.top-btn.primary{background:var(--purple);border-color:var(--purple2);color:#fff}
.top-btn.primary:hover{background:var(--purple2)}

/* ── Content ── */
.content{flex:1;overflow-y:auto;padding:24px}

/* ── Page ── */
.page{display:none}
.page.active{display:block}

/* ── Grid ── */
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
@media(max-width:1200px){.grid-4{grid-template-columns:repeat(2,1fr)}.grid-3{grid-template-columns:repeat(2,1fr)}}
@media(max-width:800px){.grid-4,.grid-3,.grid-2{grid-template-columns:1fr}}

/* ── Cards ── */
.card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:12px;
  padding:20px;
  transition:border-color .2s;
}
.card:hover{border-color:rgba(124,58,237,.3)}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.card-title{font-size:12px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted2)}
.card-icon{
  width:32px;height:32px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:14px;
}
.kpi-value{font-size:28px;font-weight:800;line-height:1;color:var(--text)}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:6px}
.kpi-change{font-size:11px;font-weight:600;margin-top:4px}

/* ── Status chip ── */
.chip{
  display:inline-flex;align-items:center;gap:5px;
  padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;letter-spacing:.3px;
}
.chip.green{background:rgba(16,185,129,.12);color:var(--green);border:1px solid rgba(16,185,129,.25)}
.chip.red{background:rgba(239,68,68,.1);color:var(--red);border:1px solid rgba(239,68,68,.2)}
.chip.orange{background:rgba(245,158,11,.1);color:var(--orange);border:1px solid rgba(245,158,11,.2)}
.chip.purple{background:rgba(124,58,237,.15);color:var(--purple3);border:1px solid rgba(124,58,237,.3)}
.chip.cyan{background:rgba(6,182,212,.1);color:var(--cyan);border:1px solid rgba(6,182,212,.2)}
.chip.muted{background:rgba(100,116,139,.1);color:var(--muted2);border:1px solid var(--border)}

/* ── Table ── */
.table-wrap{overflow-x:auto;margin-top:4px}
table{width:100%;border-collapse:collapse}
th{font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);padding:10px 12px;text-align:left;border-bottom:1px solid var(--border)}
td{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.04);font-size:12.5px;color:var(--muted2)}
td:first-child{color:var(--text);font-weight:500}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(124,58,237,.04)}

/* ── Progress bar ── */
.progress{height:6px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden;margin-top:10px}
.progress-fill{height:100%;border-radius:3px;transition:width 1s cubic-bezier(.4,0,.2,1)}

/* ── Section header ── */
.section-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.section-hd h2{font-size:16px;font-weight:700}
.section-hd p{font-size:12px;color:var(--muted);margin-top:2px}

/* ── Alert ── */
.alert{
  display:flex;gap:12px;align-items:flex-start;
  padding:14px 16px;border-radius:10px;margin-bottom:12px;
}
.alert.red{background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2)}
.alert.orange{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2)}
.alert.green{background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2)}
.alert.purple{background:rgba(124,58,237,.08);border:1px solid rgba(124,58,237,.2)}
.alert-icon{font-size:16px;flex-shrink:0;margin-top:1px}
.alert-body .alert-title{font-size:13px;font-weight:600}
.alert-body .alert-text{font-size:11.5px;color:var(--muted2);margin-top:3px;line-height:1.5}

/* ── Approval cards ── */
.approval-card{
  background:var(--card2);border:1px solid var(--border);
  border-radius:10px;padding:14px 16px;margin-bottom:10px;
  transition:border-color .2s;
}
.approval-card:hover{border-color:rgba(124,58,237,.3)}
.approval-top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}
.approval-filename{font-size:12px;font-weight:700;color:var(--purple3);font-family:monospace}
.approval-meta{display:flex;align-items:center;gap:8px;margin-top:8px;flex-wrap:wrap}
.approval-preview{font-size:11px;color:var(--muted);margin-top:8px;line-height:1.5;font-style:italic}
.approval-actions{display:flex;gap:8px;margin-top:12px}
.btn{
  padding:6px 16px;border-radius:7px;font-size:12px;font-weight:600;
  border:1px solid transparent;transition:all .18s;
}
.btn-approve{background:rgba(16,185,129,.15);color:var(--green);border-color:rgba(16,185,129,.3)}
.btn-approve:hover{background:rgba(16,185,129,.25)}
.btn-reject{background:rgba(239,68,68,.1);color:var(--red);border-color:rgba(239,68,68,.2)}
.btn-reject:hover{background:rgba(239,68,68,.2)}
.btn-view{background:var(--card);color:var(--muted2);border-color:var(--border)}
.btn-view:hover{color:var(--text);border-color:var(--border2)}
.btn-primary{background:var(--purple);color:#fff;border-color:var(--purple2)}
.btn-primary:hover{background:var(--purple2)}
.btn-secondary{background:var(--card);color:var(--muted2);border-color:var(--border2)}
.btn-secondary:hover{color:var(--text)}

/* ── Log viewer ── */
.log-entry{
  background:var(--card2);border:1px solid var(--border);
  border-radius:10px;margin-bottom:10px;overflow:hidden;
}
.log-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 14px;cursor:pointer;transition:background .18s;
}
.log-header:hover{background:rgba(124,58,237,.06)}
.log-filename{font-size:12px;font-weight:600;color:var(--purple3);font-family:monospace}
.log-body{
  padding:12px 14px;border-top:1px solid var(--border);
  font-size:11.5px;color:var(--muted2);line-height:1.7;
  white-space:pre-wrap;font-family:monospace;
  max-height:300px;overflow-y:auto;display:none;
}
.log-body.open{display:block}

/* ── Bot cards ── */
.bot-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:1100px){.bot-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:700px){.bot-grid{grid-template-columns:1fr}}
.bot-card{
  background:var(--card2);border:1px solid var(--border);
  border-radius:10px;padding:16px;
  transition:all .2s;
}
.bot-card:hover{border-color:rgba(124,58,237,.35);background:rgba(124,58,237,.05)}
.bot-icon{
  width:40px;height:40px;border-radius:10px;
  background:linear-gradient(135deg,rgba(124,58,237,.25),rgba(139,92,246,.15));
  border:1px solid rgba(124,58,237,.3);
  display:flex;align-items:center;justify-content:center;
  font-size:18px;margin-bottom:12px;
}
.bot-name{font-size:13px;font-weight:700;color:var(--text);margin-bottom:4px}
.bot-desc{font-size:11px;color:var(--muted);line-height:1.5}

/* ── Form ── */
.form-group{margin-bottom:14px}
.form-label{font-size:11px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:var(--muted2);display:block;margin-bottom:6px}
.form-input,.form-textarea,.form-select{
  width:100%;padding:9px 12px;
  background:var(--navy2);border:1px solid var(--border2);
  border-radius:8px;color:var(--text);font-size:13px;
  outline:none;transition:border-color .2s;
}
.form-input:focus,.form-textarea:focus,.form-select:focus{border-color:var(--purple2);box-shadow:0 0 0 3px rgba(124,58,237,.1)}
.form-textarea{resize:vertical;min-height:120px;line-height:1.6}
.form-select{appearance:none}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.form-hint{font-size:10px;color:var(--muted);margin-top:4px}

/* ── Social platform tabs ── */
.platform-tabs{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}
.platform-tab{
  padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;
  background:var(--card2);border:1px solid var(--border);
  color:var(--muted2);cursor:pointer;transition:all .2s;
}
.platform-tab:hover{border-color:var(--purple2);color:var(--purple3)}
.platform-tab.active{background:rgba(124,58,237,.2);border-color:var(--purple2);color:var(--purple3)}

/* ── Timeline ── */
.timeline{display:flex;flex-direction:column;gap:0}
.tl-item{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.tl-item:last-child{border-bottom:none}
.tl-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:5px}
.tl-text{font-size:12px;color:var(--muted2);line-height:1.55}
.tl-text strong{color:var(--text)}

/* ── Webhook rows ── */
.webhook-row{
  display:flex;align-items:center;justify-content:space-between;
  padding:12px 16px;background:var(--card2);border:1px solid var(--border);
  border-radius:10px;margin-bottom:8px;gap:12px;
}
.webhook-info{flex:1;min-width:0}
.webhook-name{font-size:13px;font-weight:600}
.webhook-url{font-size:11px;color:var(--muted);font-family:monospace;margin-top:2px}
.webhook-stats{display:flex;gap:16px;flex-shrink:0}
.webhook-stat{text-align:right}
.webhook-stat .ws-val{font-size:13px;font-weight:700;color:var(--purple3)}
.webhook-stat .ws-lbl{font-size:10px;color:var(--muted)}

/* ── Finance chart placeholder ── */
.chart-placeholder{
  height:140px;background:var(--navy2);border:1px dashed var(--border2);
  border-radius:8px;display:flex;align-items:center;justify-content:center;
  color:var(--muted);font-size:12px;margin-top:12px;
}

/* ── Empty state ── */
.empty{
  text-align:center;padding:48px 24px;
  color:var(--muted);
}
.empty-icon{font-size:36px;margin-bottom:12px;opacity:.5}
.empty-title{font-size:14px;font-weight:600;color:var(--muted2);margin-bottom:4px}
.empty-sub{font-size:12px}

/* ── Toast ── */
#toast{
  position:fixed;bottom:24px;right:24px;z-index:9999;
  background:var(--card2);border:1px solid var(--border2);
  border-radius:10px;padding:12px 18px;
  font-size:13px;color:var(--text);
  box-shadow:0 8px 32px rgba(0,0,0,.4);
  transform:translateY(80px);opacity:0;
  transition:all .3s cubic-bezier(.4,0,.2,1);
  max-width:340px;
}
#toast.show{transform:translateY(0);opacity:1}
#toast.success{border-left:3px solid var(--green)}
#toast.error{border-left:3px solid var(--red)}
#toast.info{border-left:3px solid var(--purple2)}

/* ── Markdown renderer ── */
.md-content{font-size:13px;line-height:1.7;color:var(--muted2)}
.md-content h1{font-size:18px;font-weight:800;color:var(--text);margin:0 0 12px}
.md-content h2{font-size:15px;font-weight:700;color:var(--purple3);margin:16px 0 8px;border-left:3px solid var(--purple);padding-left:10px}
.md-content h3{font-size:13px;font-weight:700;color:var(--text);margin:12px 0 6px}
.md-content p{margin:6px 0}
.md-content ul,.md-content ol{padding-left:20px;margin:6px 0}
.md-content li{margin:3px 0}
.md-content code{background:var(--navy2);color:var(--purple3);padding:1px 6px;border-radius:4px;font-size:11.5px;font-family:monospace}
.md-content table{width:100%;border-collapse:collapse;margin:10px 0;font-size:12px}
.md-content th{background:var(--navy2);color:var(--muted2);padding:6px 10px;border:1px solid var(--border);font-weight:600}
.md-content td{padding:6px 10px;border:1px solid var(--border);color:var(--muted2)}

/* ── Stat ring ── */
.stat-ring{display:flex;align-items:center;gap:14px}
.ring-svg{flex-shrink:0}
.ring-track{fill:none;stroke:rgba(255,255,255,.07);stroke-width:5}
.ring-arc{fill:none;stroke-width:5;stroke-linecap:round;transition:stroke-dashoffset 1.2s ease}
</style>
</head>
<body>

<!-- ── Banner ── -->
<div id="banner">
  <div class="banner-left">
    <span class="banner-logo">AI EMPLOYEE</span>
    <span class="banner-version">v2.0 Gold Tier</span>
    <span class="live-dot"></span>
    <span style="font-size:11px;color:var(--muted2)">Operations Hub</span>
  </div>
  <div class="banner-right">
    <div class="mode-toggle">
      <button class="mode-btn active-live" id="btn-live" onclick="setMode('live')">LIVE</button>
      <button class="mode-btn" id="btn-dry" onclick="setMode('dry')">DRY RUN</button>
    </div>
    <span id="banner-clock" style="font-size:11px;color:var(--muted)">--:--:--</span>
    <span id="banner-date" style="font-size:10px;color:var(--muted)"></span>
  </div>
</div>

<div class="shell">
<!-- ── Sidebar ── -->
<nav class="sidebar">
  <div class="sidebar-header">
    <div class="sidebar-title">Navigation</div>
  </div>

  <div class="nav-section">
    <div class="nav-section-label">Main</div>
    <div class="nav-item active" data-page="dashboard">
      <span class="nav-icon">⬡</span> Dashboard
    </div>
    <div class="nav-item" data-page="approvals">
      <span class="nav-icon">✓</span> Approvals
      <span class="nav-badge" id="badge-approvals">—</span>
    </div>
    <div class="nav-item" data-page="logs">
      <span class="nav-icon">≡</span> Activity Logs
    </div>
    <div class="nav-item" data-page="bots">
      <span class="nav-icon">◈</span> AI Bots
      <span class="nav-badge purple" id="badge-bots">—</span>
    </div>
  </div>

  <div class="nav-section">
    <div class="nav-section-label">Comms</div>
    <div class="nav-item" data-page="email">
      <span class="nav-icon">✉</span> Send Email
    </div>
    <div class="nav-item" data-page="social">
      <span class="nav-icon">◎</span> Social Media
    </div>
    <div class="nav-item" data-page="whatsapp">
      <span class="nav-icon">◻</span> WhatsApp
    </div>
    <div class="nav-item" data-page="webhooks">
      <span class="nav-icon">⟳</span> Webhooks
    </div>
  </div>

  <div class="nav-section">
    <div class="nav-section-label">Finance</div>
    <div class="nav-item" data-page="finance">
      <span class="nav-icon">◆</span> Finance
    </div>
    <div class="nav-item" data-page="bank">
      <span class="nav-icon">⬒</span> Bank Monitor
    </div>
    <div class="nav-item" data-page="ceo">
      <span class="nav-icon">★</span> CEO Report
    </div>
  </div>

  <div class="sidebar-footer">
    <div style="font-size:10px;color:var(--muted);text-align:center">
      Auto-refresh: 15s<br>
      <span id="last-refresh" style="font-size:10px;color:var(--muted)">Never</span>
    </div>
  </div>
</nav>

<!-- ── Main ── -->
<div class="main">
  <header class="topbar">
    <div class="topbar-left">
      <h1 id="topbar-title">Dashboard</h1>
      <p id="topbar-sub">Live metrics and system overview</p>
    </div>
    <div class="topbar-right">
      <span id="mode-chip" class="chip green">LIVE</span>
      <button class="top-btn" onclick="refreshCurrent()">↺ Refresh</button>
    </div>
  </header>

  <div class="content">

    <!-- ════ DASHBOARD ════ -->
    <div id="page-dashboard" class="page active">
      <div class="alert red" id="dash-alert" style="display:none">
        <div class="alert-icon">🚨</div>
        <div class="alert-body">
          <div class="alert-title">Critical — EMAIL_002 Overdue</div>
          <div class="alert-text" id="dash-alert-text">Loading…</div>
        </div>
      </div>

      <div class="grid-4" style="margin-bottom:16px">
        <div class="card">
          <div class="card-header">
            <div class="card-title">Revenue MTD</div>
            <div class="card-icon" style="background:rgba(124,58,237,.15)">💰</div>
          </div>
          <div class="kpi-value text-purple" id="d-rev">—</div>
          <div class="kpi-sub">Goal: <span id="d-goal">—</span></div>
          <div class="progress"><div class="progress-fill" id="d-rev-bar" style="width:0%;background:linear-gradient(90deg,var(--purple),var(--purple3))"></div></div>
        </div>
        <div class="card">
          <div class="card-header">
            <div class="card-title">Pipeline</div>
            <div class="card-icon" style="background:rgba(6,182,212,.12)">📊</div>
          </div>
          <div class="kpi-value" style="font-size:13px;color:var(--cyan);line-height:1.4" id="d-pipeline">—</div>
          <div class="kpi-sub">Active deals</div>
        </div>
        <div class="card">
          <div class="card-header">
            <div class="card-title">Pending Approvals</div>
            <div class="card-icon" style="background:rgba(245,158,11,.12)">⏳</div>
          </div>
          <div class="kpi-value" style="color:var(--orange)" id="d-pending">—</div>
          <div class="kpi-sub">Awaiting review</div>
        </div>
        <div class="card">
          <div class="card-header">
            <div class="card-title">Active Errors</div>
            <div class="card-icon" style="background:rgba(239,68,68,.12)">⚠</div>
          </div>
          <div class="kpi-value" style="color:var(--red)" id="d-errors">—</div>
          <div class="kpi-sub">Requires action</div>
        </div>
      </div>

      <div class="grid-3" style="margin-bottom:16px">
        <div class="card">
          <div class="card-header"><div class="card-title">Social Posts</div></div>
          <div class="kpi-value" style="color:var(--green)" id="d-social-count">—</div>
          <div class="kpi-sub">Live posts published</div>
          <div style="margin-top:12px;display:flex;gap:6px;flex-wrap:wrap" id="d-social-chips"></div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">AI Agents</div></div>
          <div class="kpi-value" style="color:var(--purple3)" id="d-agent-count">—</div>
          <div class="kpi-sub">Registered bots</div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">System Health</div></div>
          <div id="d-health" style="font-size:12px;color:var(--muted2);line-height:1.6">—</div>
          <div style="margin-top:8px" id="d-health-chip"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><div class="card-title">Last Active</div></div>
        <div style="font-size:13px;color:var(--muted2)" id="d-last-active">—</div>
      </div>
    </div>

    <!-- ════ APPROVALS ════ -->
    <div id="page-approvals" class="page">
      <div class="section-hd">
        <div><h2>Human-in-the-Loop Queue</h2><p>Review and approve or reject pending AI actions</p></div>
        <button class="top-btn" onclick="loadApprovals()">↺ Refresh</button>
      </div>
      <div id="approvals-list">
        <div style="color:var(--muted);font-size:13px">Loading…</div>
      </div>
    </div>

    <!-- ════ LOGS ════ -->
    <div id="page-logs" class="page">
      <div class="section-hd">
        <div><h2>Activity Logs</h2><p>Daily audit trail from agent operations</p></div>
        <button class="top-btn" onclick="loadLogs()">↺ Refresh</button>
      </div>
      <div id="logs-list">
        <div style="color:var(--muted);font-size:13px">Loading…</div>
      </div>
    </div>

    <!-- ════ BOTS ════ -->
    <div id="page-bots" class="page">
      <div class="section-hd">
        <div><h2>AI Bots</h2><p>Registered agents and their capabilities</p></div>
      </div>
      <div class="bot-grid" id="bots-grid">
        <div style="color:var(--muted);font-size:13px">Loading…</div>
      </div>
    </div>

    <!-- ════ EMAIL ════ -->
    <div id="page-email" class="page">
      <div class="section-hd">
        <div><h2>Send Email</h2><p>Compose and queue outbound emails via Gmail MCP</p></div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-title" style="margin-bottom:16px">Compose Email</div>
          <div class="form-group">
            <label class="form-label">To</label>
            <input class="form-input" id="email-to" placeholder="recipient@example.com" type="email">
          </div>
          <div class="form-group">
            <label class="form-label">Subject</label>
            <input class="form-input" id="email-subject" placeholder="Email subject">
          </div>
          <div class="form-group">
            <label class="form-label">Body</label>
            <textarea class="form-textarea" id="email-body" placeholder="Write your email here…"></textarea>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <button class="btn btn-primary" onclick="sendEmail()">Queue Email</button>
            <button class="btn btn-secondary" onclick="clearEmail()">Clear</button>
            <span id="email-mode-note" class="chip orange" style="margin-left:auto">DRY RUN</span>
          </div>
          <div class="form-hint" style="margin-top:8px">Email will be saved to Needs_Action/Email/ and requires HITL approval before sending.</div>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:16px">Guidelines</div>
          <div class="alert purple">
            <div class="alert-icon">🔒</div>
            <div class="alert-body">
              <div class="alert-title">HITL Mandatory</div>
              <div class="alert-text">All emails require human approval before sending. New contacts are always flagged.</div>
            </div>
          </div>
          <div style="margin-top:12px;font-size:12px;color:var(--muted2);line-height:1.8">
            <div>✓ Known contacts — auto-approve eligible</div>
            <div>⚠ New contacts — always requires approval</div>
            <div>⚠ Attachments — always requires approval</div>
            <div>✓ Draft saved to Needs_Action/Email/</div>
            <div>✓ Sent via Gmail API (email-mcp)</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ════ SOCIAL ════ -->
    <div id="page-social" class="page">
      <div class="section-hd">
        <div><h2>Social Media</h2><p>LinkedIn · Facebook · Instagram · Twitter/X</p></div>
      </div>
      <div class="platform-tabs">
        <div class="platform-tab active" onclick="socialTab('all',this)">All Platforms</div>
        <div class="platform-tab" onclick="socialTab('linkedin',this)">LinkedIn</div>
        <div class="platform-tab" onclick="socialTab('facebook',this)">Facebook</div>
        <div class="platform-tab" onclick="socialTab('instagram',this)">Instagram</div>
        <div class="platform-tab" onclick="socialTab('twitter',this)">Twitter/X</div>
      </div>
      <div class="grid-2" style="margin-bottom:16px">
        <div class="card">
          <div class="card-title" style="margin-bottom:14px">Draft New Post</div>
          <div class="form-group">
            <label class="form-label">Platform</label>
            <select class="form-select" id="social-platform">
              <option value="linkedin">LinkedIn</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="twitter">Twitter/X</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Post Content</label>
            <textarea class="form-textarea" id="social-content" placeholder="Write your post content…&#10;&#10;#hashtags"></textarea>
          </div>
          <button class="btn btn-primary" onclick="draftPost()">Save to Pending Approval</button>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:14px">Live Posts</div>
          <div id="social-posted-list">
            <div style="color:var(--muted);font-size:12px">Loading…</div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-title" style="margin-bottom:14px">Pending Posts</div>
        <div id="social-pending-list">
          <div style="color:var(--muted);font-size:12px">Loading…</div>
        </div>
      </div>
    </div>

    <!-- ════ WHATSAPP ════ -->
    <div id="page-whatsapp" class="page">
      <div class="section-hd">
        <div><h2>WhatsApp</h2><p>Incoming messages and conversation triggers</p></div>
      </div>
      <div class="alert orange">
        <div class="alert-icon">⚙</div>
        <div class="alert-body">
          <div class="alert-title">Not Configured</div>
          <div class="alert-text">WhatsApp watcher not yet set up. Add WhatsApp session credentials and configure <code>watchers/whatsapp_watcher.py</code> to enable.</div>
        </div>
      </div>
      <div class="card" style="margin-top:16px">
        <div class="card-title" style="margin-bottom:14px">Setup Steps</div>
        <div style="font-size:13px;color:var(--muted2);line-height:2">
          <div>1. Install <code>whatsapp-web.js</code> or <code>selenium</code> WhatsApp scraper</div>
          <div>2. Configure session in <code>mcp-servers/social-mcp/.env</code></div>
          <div>3. Add <code>WHATSAPP_PHONE</code> to your environment</div>
          <div>4. Run <code>python watchers/whatsapp_watcher.py</code></div>
          <div>5. Incoming messages will appear as tasks in <code>Needs_Action/</code></div>
        </div>
      </div>
    </div>

    <!-- ════ WEBHOOKS ════ -->
    <div id="page-webhooks" class="page">
      <div class="section-hd">
        <div><h2>Webhooks</h2><p>Active watchers and inbound event triggers</p></div>
        <button class="top-btn" onclick="loadWebhooks()">↺ Refresh</button>
      </div>
      <div id="webhooks-list">
        <div style="color:var(--muted);font-size:13px">Loading…</div>
      </div>
    </div>

    <!-- ════ FINANCE ════ -->
    <div id="page-finance" class="page">
      <div class="section-hd">
        <div><h2>Finance</h2><p>Revenue tracking, Odoo ERP, business metrics</p></div>
      </div>
      <div class="grid-3" style="margin-bottom:16px">
        <div class="card">
          <div class="card-title" style="margin-bottom:10px">Revenue MTD</div>
          <div class="kpi-value" style="color:var(--purple3)" id="fin-rev">—</div>
          <div class="kpi-sub">Monthly goal: <span id="fin-goal">—</span></div>
          <div class="progress"><div class="progress-fill" id="fin-bar" style="width:0%;background:linear-gradient(90deg,var(--purple),var(--cyan))"></div></div>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:10px">Q1 Target</div>
          <div class="kpi-value" style="color:var(--cyan)" id="fin-q1">—</div>
          <div class="kpi-sub">Quarterly target</div>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:10px">Pipeline</div>
          <div style="font-size:13px;color:var(--orange);font-weight:600;line-height:1.5" id="fin-pipeline">—</div>
          <div class="kpi-sub" style="margin-top:6px">Active opportunities</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title" style="margin-bottom:12px">Odoo Integration</div>
        <div class="alert purple">
          <div class="alert-icon">⚡</div>
          <div class="alert-body">
            <div class="alert-title">Odoo Community 19+ Connected</div>
            <div class="alert-text">MCP server at <code>mcp-servers/odoo-mcp/server.py</code> — invoices, payments and journal entries via JSON-RPC.</div>
          </div>
        </div>
        <div class="chart-placeholder">Revenue chart — connect Odoo invoices to populate</div>
      </div>
    </div>

    <!-- ════ BANK ════ -->
    <div id="page-bank" class="page">
      <div class="section-hd">
        <div><h2>Bank Monitor</h2><p>Transaction feed and anomaly detection</p></div>
      </div>
      <div class="alert orange">
        <div class="alert-icon">🏦</div>
        <div class="alert-body">
          <div class="alert-title">Bank API Not Connected</div>
          <div class="alert-text">Configure bank API credentials in <code>.env</code> to enable live transaction monitoring and anomaly detection.</div>
        </div>
      </div>
      <div class="grid-3" style="margin-top:16px">
        <div class="card">
          <div class="card-title" style="margin-bottom:8px">Balance</div>
          <div class="kpi-value" style="color:var(--muted)">—</div>
          <div class="kpi-sub">Not connected</div>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:8px">Transactions (MTD)</div>
          <div class="kpi-value" style="color:var(--muted)">—</div>
          <div class="kpi-sub">No data</div>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:8px">Anomalies Detected</div>
          <div class="kpi-value" style="color:var(--muted)">—</div>
          <div class="kpi-sub">Inactive</div>
        </div>
      </div>
    </div>

    <!-- ════ CEO REPORT ════ -->
    <div id="page-ceo" class="page">
      <div class="section-hd">
        <div><h2>CEO Report</h2><p>Monday Morning Briefing — generated every Sunday 18:00 PKT</p></div>
        <button class="top-btn btn-primary" onclick="showToast('Trigger saved — briefing will generate Sunday 18:00 PKT','info')">Schedule Briefing</button>
      </div>
      <div id="ceo-content">
        <div style="color:var(--muted);font-size:13px">Loading…</div>
      </div>
    </div>

  </div><!-- /content -->
</div><!-- /main -->
</div><!-- /shell -->

<div id="toast"></div>

<script>
// ── State ─────────────────────────────────────────────────────────────────
let mode = 'live';
let currentPage = 'dashboard';
const pageCache = {};

// ── Mode toggle ───────────────────────────────────────────────────────────
function setMode(m) {
  mode = m;
  document.getElementById('btn-live').className = 'mode-btn' + (m==='live'?' active-live':'');
  document.getElementById('btn-dry').className  = 'mode-btn' + (m==='dry'?'  active-dry':'');
  const chip = document.getElementById('mode-chip');
  if(m==='live'){chip.className='chip green';chip.textContent='LIVE'}
  else{chip.className='chip orange';chip.textContent='DRY RUN'}
  document.getElementById('email-mode-note').style.display = m==='dry'?'inline-flex':'none';
}

// ── Clock ─────────────────────────────────────────────────────────────────
function tick(){
  const n=new Date();
  document.getElementById('banner-clock').textContent=n.toLocaleTimeString('en-GB',{hour12:false});
  document.getElementById('banner-date').textContent=n.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});
}
setInterval(tick,1000); tick();

// ── Navigation ────────────────────────────────────────────────────────────
const pageMeta = {
  dashboard: ['Dashboard','Live metrics and system overview'],
  approvals:  ['Approvals','Human-in-the-loop review queue'],
  logs:       ['Activity Logs','Daily audit trail'],
  bots:       ['AI Bots','Registered agent definitions'],
  email:      ['Send Email','Compose and queue outbound email'],
  social:     ['Social Media','LinkedIn · Facebook · Instagram · Twitter/X'],
  whatsapp:   ['WhatsApp','Incoming messages and triggers'],
  webhooks:   ['Webhooks','Active watchers and event hooks'],
  finance:    ['Finance','Revenue, Odoo ERP, business metrics'],
  bank:       ['Bank Monitor','Transaction feed and anomaly detection'],
  ceo:        ['CEO Report','Monday Morning Briefing'],
};

document.querySelectorAll('.nav-item[data-page]').forEach(el=>{
  el.addEventListener('click',()=>{
    const pg = el.dataset.page;
    document.querySelectorAll('.nav-item').forEach(e=>e.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
    document.getElementById('page-'+pg).classList.add('active');
    const meta = pageMeta[pg]||[pg,''];
    document.getElementById('topbar-title').textContent = meta[0];
    document.getElementById('topbar-sub').textContent   = meta[1];
    currentPage = pg;
    loadPage(pg);
  });
});

function loadPage(pg){
  if(pg==='dashboard')    loadDashboard();
  else if(pg==='approvals') loadApprovals();
  else if(pg==='logs')    loadLogs();
  else if(pg==='bots')    loadBots();
  else if(pg==='social')  loadSocial();
  else if(pg==='webhooks') loadWebhooks();
  else if(pg==='finance') loadFinance();
  else if(pg==='ceo')     loadCEO();
}

function refreshCurrent(){ loadPage(currentPage); }

// ── Toast ─────────────────────────────────────────────────────────────────
function showToast(msg, type='info'){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  setTimeout(()=>t.className='', 3500);
}

// ── API helpers ───────────────────────────────────────────────────────────
async function get(url){
  const r = await fetch(url);
  return r.json();
}
async function post(url, body){
  const r = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  return r.json();
}

// ── Dashboard ─────────────────────────────────────────────────────────────
async function loadDashboard(){
  const d = await get('/api/dashboard');
  document.getElementById('d-rev').textContent    = d.revenue_mtd||'—';
  document.getElementById('d-goal').textContent   = d.monthly_goal||'—';
  document.getElementById('d-pipeline').textContent = d.pipeline||'—';
  document.getElementById('d-pending').textContent  = d.pending_approvals||'—';
  document.getElementById('d-errors').textContent   = d.errors_today||'0';
  document.getElementById('d-last-active').textContent = d.last_active||'—';
  document.getElementById('d-social-count').textContent = d.stats?.social_posted||'—';
  document.getElementById('d-agent-count').textContent  = d.stats?.agent_count||'—';
  document.getElementById('d-health').textContent       = d.health||'—';

  // Health chip
  const hc = document.getElementById('d-health-chip');
  const ok = (d.health||'').toLowerCase().includes('stable')||(d.health||'').toLowerCase().includes('active');
  hc.innerHTML = `<span class="chip ${ok?'green':'orange'}">${ok?'Stable':'Degraded'}</span>`;

  // Social chips
  const sc = document.getElementById('d-social-chips');
  ['LinkedIn','Facebook','Instagram','Twitter/X'].forEach(p=>{
    const span = document.createElement('span');
    span.className='chip green';span.textContent=p;
    sc.appendChild(span);
  });

  // Alert
  if((d.errors_today||'').includes('ACTIVE')){
    document.getElementById('dash-alert').style.display='flex';
    document.getElementById('dash-alert-text').textContent =
      'EMAIL_002_enterprise_rfp.md — TechCorp RFP $25k–$40k USD — immediate review required. '+d.errors_today;
  }

  // Badges
  const pa = d.stats?.pending_count||0;
  document.getElementById('badge-approvals').textContent = pa||'0';
  document.getElementById('badge-bots').textContent      = d.stats?.agent_count||'0';

  document.getElementById('last-refresh').textContent = new Date().toLocaleTimeString('en-GB',{hour12:false});
}

// ── Approvals ─────────────────────────────────────────────────────────────
async function loadApprovals(){
  const items = await get('/api/approvals');
  const el = document.getElementById('approvals-list');
  document.getElementById('badge-approvals').textContent = items.length||'0';
  if(!items.length){
    el.innerHTML=`<div class="empty"><div class="empty-icon">✓</div><div class="empty-title">All clear</div><div class="empty-sub">No items pending approval</div></div>`;
    return;
  }
  el.innerHTML = items.map(i=>{
    const age = i.age_hours > 24 ? `<span class="chip red">${i.age_hours}h old</span>` : `<span class="chip muted">${i.age_hours}h old</span>`;
    const sens = i.sensitivity==='high'?'<span class="chip red">HIGH</span>':'<span class="chip orange">'+i.sensitivity.toUpperCase()+'</span>';
    return `<div class="approval-card" id="acard-${btoa(i.path).replace(/=/g,'')}">
      <div class="approval-top">
        <span class="approval-filename">${i.filename}</span>
        ${sens}
      </div>
      <div class="approval-meta">${age}<span class="chip cyan">${i.platform}</span><span class="chip muted">${i.size}B</span></div>
      <div class="approval-preview">${i.preview.substring(0,180)}…</div>
      <div class="approval-actions">
        <button class="btn btn-approve" onclick="approveItem('${i.path}','${i.filename}')">✓ Approve</button>
        <button class="btn btn-reject"  onclick="rejectItem('${i.path}','${i.filename}')">✕ Reject</button>
      </div>
    </div>`;
  }).join('');
}

async function approveItem(path, name){
  const r = await post('/api/approvals/approve',{path});
  if(r.ok){ showToast(`Approved: ${name}`,'success'); loadApprovals(); }
  else showToast('Error: '+r.error,'error');
}
async function rejectItem(path, name){
  const r = await post('/api/approvals/reject',{path});
  if(r.ok){ showToast(`Rejected: ${name}`,'info'); loadApprovals(); }
  else showToast('Error: '+r.error,'error');
}

// ── Logs ──────────────────────────────────────────────────────────────────
async function loadLogs(){
  const items = await get('/api/logs');
  const el = document.getElementById('logs-list');
  if(!items.length){
    el.innerHTML=`<div class="empty"><div class="empty-icon">≡</div><div class="empty-title">No logs yet</div><div class="empty-sub">Logs appear in Logs/YYYY-MM-DD.md</div></div>`;
    return;
  }
  el.innerHTML = items.map((l,i)=>`
    <div class="log-entry">
      <div class="log-header" onclick="toggleLog(${i})">
        <span class="log-filename">${l.filename}</span>
        <span class="chip muted">${(l.size/1024).toFixed(1)}KB</span>
      </div>
      <div class="log-body" id="logbody-${i}">${l.content}</div>
    </div>`).join('');
}
function toggleLog(i){
  const b=document.getElementById('logbody-'+i);
  b.classList.toggle('open');
}

// ── Bots ──────────────────────────────────────────────────────────────────
const botIcons = {
  'gold-main-orchestrator':'⬡','email':'✉','social':'◎','accounting':'◆',
  'finance':'💰','triage':'⚡','planner':'📋','approval':'✓',
  'comms':'📡','file':'📁','classifier':'🔍','sub':'◈'
};
async function loadBots(){
  const bots = await get('/api/bots');
  document.getElementById('badge-bots').textContent = bots.length||'0';
  document.getElementById('d-agent-count').textContent = bots.length||'—';
  const el = document.getElementById('bots-grid');
  if(!bots.length){el.innerHTML='<div style="color:var(--muted)">No agents found in .claude/agents/</div>';return;}
  el.innerHTML = bots.map(b=>{
    const icon = Object.entries(botIcons).find(([k])=>b.name.includes(k))?.[1]||'◈';
    return `<div class="bot-card">
      <div class="bot-icon">${icon}</div>
      <div class="bot-name">${b.name}</div>
      <div class="bot-desc">${b.description.substring(0,120)}</div>
    </div>`;
  }).join('');
}

// ── Social ────────────────────────────────────────────────────────────────
let socialFilter = 'all';
function socialTab(f,el){
  socialFilter=f;
  document.querySelectorAll('.platform-tab').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  loadSocial();
}
async function loadSocial(){
  const d = await get('/api/social');
  const platColors={'linkedin':'#0077b5','facebook':'#1877f2','instagram':'#e1306c','twitter':'#1da1f2','twitter/x':'#1da1f2'};
  const posted = d.posted.filter(p=>socialFilter==='all'||p.platform.toLowerCase().includes(socialFilter));
  const pending = d.pending.filter(p=>socialFilter==='all'||p.platform.toLowerCase().includes(socialFilter));

  const pl = document.getElementById('social-posted-list');
  pl.innerHTML = posted.length ? posted.map(p=>{
    const c=platColors[p.platform.toLowerCase()]||'var(--purple3)';
    return `<div style="padding:8px 10px;background:var(--navy2);border:1px solid var(--border);border-radius:8px;margin-bottom:6px">
      <div style="display:flex;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:12px;font-weight:600;color:${c}">${p.platform}</span>
        <span class="chip green">POSTED</span>
      </div>
      <div style="font-size:11px;color:var(--muted)">${p.date}</div>
      <div style="font-size:11px;color:var(--muted2);margin-top:4px">${p.preview.substring(0,100)}</div>
    </div>`;
  }).join('') : '<div style="color:var(--muted);font-size:12px">No posted content</div>';

  const penl = document.getElementById('social-pending-list');
  penl.innerHTML = pending.length ? pending.map(p=>`
    <div style="padding:8px 10px;background:var(--navy2);border:1px solid var(--border);border-radius:8px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;gap:8px">
      <div>
        <div style="font-size:12px;font-weight:600">${p.filename}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:2px">${p.preview.substring(0,100)}</div>
      </div>
      <span class="chip orange">PENDING</span>
    </div>`).join('') : '<div style="color:var(--muted);font-size:12px">No pending posts</div>';
}
async function draftPost(){
  const platform = document.getElementById('social-platform').value;
  const content  = document.getElementById('social-content').value.trim();
  if(!content){showToast('Post content is required','error');return;}
  const r = await post('/api/social/draft',{platform,content});
  if(r.ok){showToast(`Draft saved: ${r.file}`,'success');document.getElementById('social-content').value='';}
  else showToast('Failed to save draft','error');
}

// ── Email ─────────────────────────────────────────────────────────────────
async function sendEmail(){
  const to      = document.getElementById('email-to').value.trim();
  const subject = document.getElementById('email-subject').value.trim();
  const body    = document.getElementById('email-body').value.trim();
  if(!to||!subject||!body){showToast('All fields required','error');return;}
  const r = await post('/api/email/send',{to,subject,body,dry_run:mode==='dry'});
  if(r.ok) showToast(r.message,'success');
  else     showToast('Error sending','error');
}
function clearEmail(){
  ['email-to','email-subject','email-body'].forEach(id=>document.getElementById(id).value='');
}

// ── Webhooks ──────────────────────────────────────────────────────────────
async function loadWebhooks(){
  const hooks = await get('/api/webhooks');
  document.getElementById('webhooks-list').innerHTML = hooks.map(h=>`
    <div class="webhook-row">
      <div class="webhook-info">
        <div class="webhook-name">${h.name}</div>
        <div class="webhook-url">${h.url}</div>
        <div style="margin-top:6px"><span class="chip ${h.status==='active'?'green':'muted'}">${h.status.toUpperCase()}</span></div>
      </div>
      <div class="webhook-stats">
        <div class="webhook-stat"><div class="ws-val">${h.triggers}</div><div class="ws-lbl">triggers</div></div>
        <div class="webhook-stat"><div class="ws-val" style="font-size:10px;font-weight:500;color:var(--muted)">${h.last_trigger}</div><div class="ws-lbl">last fired</div></div>
      </div>
    </div>`).join('');
}

// ── Finance ───────────────────────────────────────────────────────────────
async function loadFinance(){
  const d = await get('/api/finance');
  document.getElementById('fin-rev').textContent      = d.revenue_mtd||'—';
  document.getElementById('fin-goal').textContent     = d.monthly_goal||'—';
  document.getElementById('fin-q1').textContent       = d.q1_target||'—';
  document.getElementById('fin-pipeline').textContent = d.pipeline||'—';
}

// ── CEO Report ────────────────────────────────────────────────────────────
async function loadCEO(){
  const reports = await get('/api/ceo-report');
  const el = document.getElementById('ceo-content');
  el.innerHTML = reports.map(r=>`
    <div class="card" style="margin-bottom:14px">
      <div class="card-header">
        <div class="card-title">${r.date}</div>
        <span class="chip purple">Briefing</span>
      </div>
      <div class="md-content">${simpleMarkdown(r.content)}</div>
    </div>`).join('');
}

// ── Simple Markdown renderer ──────────────────────────────────────────────
function simpleMarkdown(md){
  return md
    .replace(/^### (.+)/gm,'<h3>$1</h3>')
    .replace(/^## (.+)/gm,'<h2>$1</h2>')
    .replace(/^# (.+)/gm,'<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/`(.+?)`/g,'<code>$1</code>')
    .replace(/^[-*] (.+)/gm,'<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs,'<ul>$1</ul>')
    .replace(/^\|.+/gm,s=>`<tr>${s.split('|').filter(c=>c.trim()&&!c.match(/^[-: ]+$/)).map(c=>`<td>${c.trim()}</td>`).join('')}</tr>`)
    .replace(/(<tr>.*<\/tr>)/gs,'<table>$1</table>')
    .replace(/\n\n/g,'</p><p>')
    .replace(/^([^<\n].+)$/gm,'<p>$1</p>');
}

// ── Auto-refresh ──────────────────────────────────────────────────────────
setInterval(()=>{ if(currentPage==='dashboard') loadDashboard(); }, 15000);

// ── Init ──────────────────────────────────────────────────────────────────
loadDashboard();
setMode('live');
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("\n  AI Employee Operations Hub")
    print("  --> http://localhost:5501\n")
    app.run(host="0.0.0.0", port=5501, debug=False)
