# Gmail Operator Skill

**Purpose:** Process incoming emails from Gmail, classify intent, draft responses, and manage approval workflow.

**Location:** `/Skills/gmail_operator/`

---

## Workflow

### 1. Scan Needs_Action Folder

Scan `/02_Needs_Actions` for files with YAML frontmatter containing:
```yaml
type: email
status: pending
```

### 2. Classify Email Intent

For each email found, classify into one of these categories:

| Intent | Description | Action |
|--------|-------------|--------|
| `inquiry` | Information request | Draft response with requested info |
| `meeting_request` | Meeting/call invitation | Check calendar, propose times |
| `complaint` | Customer complaint | Escalate, draft apology |
| `feedback` | Product/service feedback | Acknowledge, forward to team |
| `sales` | Sales inquiry | Forward to sales team |
| `spam` | Unwanted email | Mark as spam, archive |
| `newsletter` | Subscription content | Archive or summarize |
| `approval_needed` | Requires decision | Create approval request |
| `action_required` | Task assignment | Create task, assign owner |

### 3. Create Plan

For each classified email, create a plan file in `/Plans/`:

**Filename:** `PLAN_EMAIL_{gmail_id}_{timestamp}.md`

**Template:**
```markdown
---
type: email_plan
email_id: {gmail_id}
original_subject: {subject}
intent: {classified_intent}
priority: {priority}
created: {timestamp}
status: pending
---

# Email Processing Plan

## Original Email

**From:** {from}  
**Subject:** {subject}  
**Received:** {received}

## Classified Intent

**Intent:** {intent}  
**Confidence:** {confidence_score}%  
**Priority:** {priority}

## Proposed Action

{Describe the proposed action - e.g., "Draft response with product information"}

## Draft Response

```
To: {from}
Subject: Re: {subject}

{Draft body content}
```

## Approval Required

- [ ] Review classified intent
- [ ] Approve draft response
- [ ] Authorize sending

---

*Move this file to /04_Approved to send, or /08_Rejected to cancel.*
```

### 4. Create Approval File

Create approval file in `/03_Pending_Approval/`:

**Filename:** `APPROVAL_EMAIL_{gmail_id}.md`

**Template:**
```markdown
---
type: email_approval
email_id: {gmail_id}
action: send_email
to: {recipient}
subject: {subject}
status: pending_approval
created: {timestamp}
---

# Email Approval Request

## Action Required

Please review and approve the following email before sending:

**To:** {to}  
**Subject:** {subject}

## Email Content

{Full email body}

---

## Approval Instructions

1. Review the email content above
2. If approved: Move this file to `/04_Approved/`
3. If rejected: Move this file to `/08_Rejected/`

---

*This is an automated approval request from Gmail Operator*
```

### 5. Wait for Approval

The orchestrator monitors `/03_Pending_Approval/` and `/04_Approved/` folders:

- **If moved to `/04_Approved/`:** Call MCP `send_email` tool
- **If moved to `/08_Rejected/`:** Cancel action, log rejection

### 6. On Approval → Call MCP

When approval file appears in `/04_Approved/`:

1. Parse approval file for email details
2. Call MCP `send_email` tool with parameters
3. Log the action
4. Move original email file to `/05_Done/`
5. Move approval file to `/05_Done/`

### 7. Move Completed Items to Done

After successful send:

1. Move original email from `/02_Needs_Actions/` → `/05_Done/`
2. Move approval file from `/04_Approved/` → `/05_Done/`
3. Update plan status to `completed`
4. Log completion

---

## Example Classification Rules

### Inquiry Detection
```python
inquiry_keywords = ['question', 'ask', 'wondering', 'information', 'how to', 'help']
if any(keyword in subject.lower() or keyword in body.lower() for keyword in inquiry_keywords):
    intent = 'inquiry'
```

### Meeting Request Detection
```python
meeting_keywords = ['meeting', 'call', 'schedule', 'available', 'time', 'zoom', 'teams']
if any(keyword in subject.lower() for keyword in meeting_keywords):
    intent = 'meeting_request'
```

### Complaint Detection
```python
complaint_keywords = ['complaint', 'unhappy', 'disappointed', 'issue', 'problem', 'wrong', 'broken']
if any(keyword in subject.lower() or keyword in body.lower() for keyword in complaint_keywords):
    intent = 'complaint'
    priority = 'high'
```

---

## Error Handling

### If Classification Fails
- Set intent to `unknown`
- Create approval file for manual review
- Log classification failure

### If MCP Call Fails
- Log error with details
- Move approval file to `/08_Rejected/` with error note
- Notify administrator

### If Rate Limit Reached
- Pause processing for 1 hour
- Log rate limit event
- Resume after cooldown

---

## Logging

All actions logged to `/Logs/gmail_operator_{YYYY-MM-DD}.json`:

```json
{
  "timestamp": "2026-02-23T18:00:00Z",
  "action": "classify_email",
  "email_id": "abc123",
  "intent": "inquiry",
  "confidence": 0.92,
  "result": "success"
}
```

---

## Testing

### Test Classification
```bash
cd gmail-integration
python test_classification.py --email "test@example.com" --subject "Question about pricing"
```

### Test Approval Flow
1. Create test email in `/02_Needs_Actions/`
2. Run skill manually
3. Move approval file to `/04_Approved/`
4. Verify email sent (or DRY_RUN log)

---

## Security Notes

- Never send emails without approval
- Validate all email addresses before sending
- Respect DRY_RUN mode in all operations
- Log all actions for audit trail
- Rate limit: max 10 emails/hour

---

*Skill Version: 1.0*  
*Last Updated: 2026-02-23*
