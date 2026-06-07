"""Pre-built documentation templates for the knowledge base."""


TEMPLATES = {
    "how-to": {
        "title": "How-To: [Title]",
        "category": "how-to",
        "body": """# How-To: [Title]

## Overview
Brief description of what this guide covers.

## Prerequisites
- Requirement 1
- Requirement 2

## Steps

### Step 1: [Description]
Details for step 1.

```
# Commands or code if applicable
```

### Step 2: [Description]
Details for step 2.

### Step 3: [Description]
Details for step 3.

## Verification
How to verify the procedure was successful.

## Troubleshooting
Common issues and their solutions.

## Related
- Link to related documentation
""",
    },
    "troubleshooting": {
        "title": "Troubleshooting: [Issue]",
        "category": "troubleshooting",
        "body": """# Troubleshooting: [Issue]

## Symptoms
Describe what the user observes when this issue occurs.

- Symptom 1
- Symptom 2

## Root Cause
Explanation of what causes this issue.

## Diagnosis Steps

### Step 1: Check [Component]
```
# Diagnostic command
```
Expected output vs. problematic output.

### Step 2: Verify [Configuration]
What to look for.

## Solution

### Quick Fix
Immediate steps to resolve the issue.

### Permanent Fix
Long-term solution to prevent recurrence.

## Prevention
Steps to prevent this issue from happening again.

## Related Issues
- Similar issue 1
- Similar issue 2
""",
    },
    "runbook": {
        "title": "Runbook: [Procedure]",
        "category": "runbook",
        "body": """# Runbook: [Procedure]

## Summary
| Field | Value |
|-------|-------|
| **Owner** | [Team/Person] |
| **Last Updated** | [Date] |
| **Frequency** | [Daily/Weekly/As-needed] |
| **Estimated Time** | [Duration] |
| **Risk Level** | [Low/Medium/High] |

## Purpose
Why this procedure exists and when to execute it.

## Pre-Conditions
- [ ] Condition 1 verified
- [ ] Condition 2 verified
- [ ] Backups taken (if applicable)

## Procedure

### Phase 1: Preparation
1. Step 1
2. Step 2

### Phase 2: Execution
1. Step 1
   ```
   # Command
   ```
2. Step 2

### Phase 3: Verification
1. Verify step 1
2. Verify step 2

## Rollback Plan
Steps to revert if something goes wrong.

1. Rollback step 1
2. Rollback step 2

## Post-Execution
- [ ] Notify stakeholders
- [ ] Update monitoring
- [ ] Document any deviations

## Contacts
| Role | Name | Contact |
|------|------|---------|
| Primary | | |
| Escalation | | |
""",
    },
}


def get_template_names() -> list[str]:
    """Get list of available template names."""
    return list(TEMPLATES.keys())


def get_template(template_name: str) -> dict | None:
    """Get a template by name. Returns dict with title, category, body."""
    return TEMPLATES.get(template_name)
