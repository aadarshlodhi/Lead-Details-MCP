from fastmcp import FastMCP
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "leads.db")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

mcp = FastMCP("Lead Details")

# ─────────────────────────────────────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                email       TEXT NOT NULL,
                phone       TEXT DEFAULT '',
                company     TEXT DEFAULT '',
                source      TEXT DEFAULT '',
                status      TEXT DEFAULT 'New',
                date_added  TEXT NOT NULL,
                notes       TEXT DEFAULT ''
            )
        """)

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# Lead Management Tools
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def add_lead(name: str, email: str, phone: str = "", company: str = "",
             source: str = "", status: str = "New", notes: str = "") -> dict:
    """Add a new lead to the database.
    
    Args:
        name: Full name of the lead
        email: Email address of the lead
        phone: Phone number (optional)
        company: Company name (optional)
        source: Lead source e.g. Website, Referral, LinkedIn, Cold Call (optional)
        status: Lead status - New, Contacted, Qualified, Closed (default: New)
        notes: Any additional notes about the lead (optional)
    """
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO leads (name, email, phone, company, source, status, date_added, notes) VALUES (?,?,?,?,?,?,?,?)",
            (name, email, phone, company, source, status, today, notes)
        )
        return {"status": "ok", "message": f"Lead '{name}' added successfully.", "id": cur.lastrowid}


@mcp.tool()
def list_all_leads() -> dict:
    """List every lead in the database with all their details and a grand total count."""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT * FROM leads ORDER BY date_added DESC, id DESC").fetchall()
        leads = [dict(r) for r in rows]
        return {"total_leads": len(leads), "leads": leads}


@mcp.tool()
def search_lead_by_name(name: str) -> dict:
    """Search for leads by name. Supports partial matches (case-insensitive).
    
    Args:
        name: Full or partial name to search for
    """
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM leads WHERE name LIKE ? ORDER BY date_added DESC",
            (f"%{name}%",)
        ).fetchall()
        leads = [dict(r) for r in rows]
        return {"total_found": len(leads), "leads": leads}


@mcp.tool()
def get_leads_by_date(start_date: str, end_date: str) -> dict:
    """Get all leads added within a date range (inclusive).
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM leads WHERE date_added BETWEEN ? AND ? ORDER BY date_added ASC",
            (start_date, end_date)
        ).fetchall()
        leads = [dict(r) for r in rows]
        return {"total_found": len(leads), "date_range": f"{start_date} to {end_date}", "leads": leads}


@mcp.tool()
def get_leads_by_status(status: str) -> dict:
    """Filter leads by their current status.
    
    Args:
        status: One of: New, Contacted, Qualified, Closed
    """
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY date_added DESC",
            (status,)
        ).fetchall()
        leads = [dict(r) for r in rows]
        return {"status_filter": status, "total_found": len(leads), "leads": leads}


@mcp.tool()
def update_lead_status(lead_id: int, status: str, notes: str = "") -> dict:
    """Update the status of an existing lead by their ID.
    
    Args:
        lead_id: The ID of the lead to update
        status: New status - New, Contacted, Qualified, or Closed
        notes: Optional notes to append to the lead record
    """
    with sqlite3.connect(DB_PATH) as c:
        if notes:
            c.execute(
                "UPDATE leads SET status = ?, notes = notes || '\n' || ? WHERE id = ?",
                (status, notes, lead_id)
            )
        else:
            c.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
        
        if c.execute("SELECT changes()").fetchone()[0] == 0:
            return {"status": "error", "message": f"No lead found with ID {lead_id}"}
        return {"status": "ok", "message": f"Lead #{lead_id} status updated to '{status}'"}

@mcp.tool()
def get_lead_summary() -> dict:
    """Get a quick summary of all leads grouped by status and source."""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        by_status = [dict(r) for r in c.execute(
            "SELECT status, COUNT(*) as count FROM leads GROUP BY status ORDER BY count DESC"
        ).fetchall()]
        by_source = [dict(r) for r in c.execute(
            "SELECT source, COUNT(*) as count FROM leads WHERE source != '' GROUP BY source ORDER BY count DESC"
        ).fetchall()]
        total = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        return {
            "total_leads": total,
            "by_status": by_status,
            "by_source": by_source
        }


# ─────────────────────────────────────────────────────────────────────────────
# Email Tools
# ─────────────────────────────────────────────────────────────────────────────

def _send_smtp_email(to_address: str, subject: str, body: str) -> dict:
    """Internal helper to send an email via SMTP."""
    if not EMAIL_ADDRESS or EMAIL_ADDRESS == "your@gmail.com":
        return {
            "status": "error",
            "message": "Email not configured. Please fill in EMAIL_ADDRESS and EMAIL_PASSWORD in the .env file at e:\\download\\MCP\\expense-tracker-mcp-server\\.env"
        }
    
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_address, msg.as_string())

    return {"status": "ok", "message": f"Email sent successfully to {to_address}"}


@mcp.tool()
def send_email_to_lead(lead_id: int, subject: str, body: str) -> dict:
    """Send an email to a specific lead using their stored email address.
    
    Args:
        lead_id: The ID of the lead to email
        subject: Email subject line
        body: Email body text
    """
    with sqlite3.connect(DB_PATH) as c:
        row = c.execute("SELECT name, email FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not row:
            return {"status": "error", "message": f"No lead found with ID {lead_id}"}
        name, email = row

    try:
        result = _send_smtp_email(email, subject, body)
        if result["status"] == "ok":
            # Log the email in notes
            with sqlite3.connect(DB_PATH) as c:
                c.execute(
                    "UPDATE leads SET notes = notes || '\n[Email sent] Subject: ' || ? WHERE id = ?",
                    (subject, lead_id)
                )
        return {**result, "lead_name": name, "lead_email": email}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def send_custom_email(to_email: str, subject: str, body: str) -> dict:
    """Send an email to any email address with a custom subject and body.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body text
    """
    try:
        return _send_smtp_email(to_email, subject, body)
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
