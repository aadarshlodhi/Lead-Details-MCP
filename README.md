# Lead Details MCP

A **Lead Generation MCP Server** for Claude Desktop that lets you manage leads and send emails directly from Claude chat.

## 🛠️ Tools Available

| Tool | Description |
|---|---|
| `add_lead` | Add a new lead (name, email, phone, company, source, status) |
| `list_all_leads` | List every lead in the database |
| `search_lead_by_name` | Search leads by name (partial match) |
| `get_leads_by_date` | Filter leads by date range |
| `get_leads_by_status` | Filter by status (New / Contacted / Qualified / Closed) |
| `update_lead_status` | Update a lead's status by ID |
| `get_lead_summary` | Summary of all leads by status and source |
| `send_email_to_lead` | Send email to a lead using their stored email |
| `send_custom_email` | Send email to any address |

## 🚀 Setup

### 1. Install dependencies
```bash
pip install fastmcp python-dotenv
```

### 2. Configure email
Create a `.env` file in the project root:
```env
EMAIL_ADDRESS=your@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```
> For Gmail: Generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

### 3. Add to Claude Desktop config
Edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "lead-details": {
      "command": "C:\\Path\\To\\python.exe",
      "args": ["path\\to\\main.py"]
    }
  }
}
```

### 4. Restart Claude Desktop
The **lead-details** server will appear in Claude's Connectors panel.

## 💬 Example Claude Prompts

- *"Add lead: John Doe, john@acme.com, Acme Corp, from LinkedIn"*
- *"Show me all leads"*
- *"Search for leads named John"*
- *"List all Qualified leads"*
- *"Send email to lead #1 subject Hello body Nice to meet you"*

## 📋 Requirements
- Python 3.10+
- fastmcp
- python-dotenv
