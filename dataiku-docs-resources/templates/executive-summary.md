# Executive Summary Template

> **How to use this template**: Fill in each section with information about your Dataiku project. Keep language non-technical and focus on business value.

---

# [PROJECT_NAME] - Executive Summary

**Document Version**: [X.X]
**Last Updated**: [DATE]
**Document Owner**: [ROLE]

---

## What This Project Does

> *Describe the project's purpose in 2-3 sentences that a business executive would understand. Focus on WHAT the project accomplishes, not HOW it works technically.*

[Write a clear, jargon-free description of the project's function]

**Example:**
> This project combines customer purchase history with website behavior to identify which customers are likely to stop buying from us. It produces a daily report that helps the Customer Success team prioritize retention outreach.

---

## Why It Matters

> *Explain the business value. What decisions does this enable? What would happen if this project didn't exist?*

### Business Value Delivered

| Value | Description |
|-------|-------------|
| [Value 1] | [How this benefits the business] |
| [Value 2] | [How this benefits the business] |
| [Value 3] | [How this benefits the business] |

### Key Business Questions Answered

- [ ] [Question 1 this project answers?]
- [ ] [Question 2 this project answers?]
- [ ] [Question 3 this project answers?]

---

## Key Outputs

> *What does this project produce? Who uses it?*

| Output | Description | Consumers | Refresh Frequency |
|--------|-------------|-----------|-------------------|
| [Output 1 name] | [What it contains in plain language] | [Who uses it] | [Daily/Weekly/etc.] |
| [Output 2 name] | [What it contains in plain language] | [Who uses it] | [Daily/Weekly/etc.] |
| [Output 3 name] | [What it contains in plain language] | [Who uses it] | [Daily/Weekly/etc.] |

---

## Data Sources

> *Where does the data come from?*

| Source | What It Provides | Update Frequency | Data Owner |
|--------|------------------|------------------|------------|
| [Source 1] | [Plain language description] | [Frequency] | [Team/Role] |
| [Source 2] | [Plain language description] | [Frequency] | [Team/Role] |
| [Source 3] | [Plain language description] | [Frequency] | [Team/Role] |

---

## Quick Facts

| Property | Value |
|----------|-------|
| **Runs** | [Plain language schedule, e.g., "Every day at 6 AM"] |
| **Typical Runtime** | [e.g., "About 30 minutes"] |
| **Project Owner** | [Role/Team, not personal name] |
| **Technical Owner** | [Role/Team, not personal name] |
| **Status** | [Active / Maintenance / Under Development / Deprecated] |
| **Created** | [Date/Year] |
| **Last Major Update** | [Date and brief description] |

---

## Data Flow Overview

> *High-level visualization of how data moves through the project*

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     INPUTS      │     │   PROCESSING    │     │    OUTPUTS      │
│                 │     │                 │     │                 │
│ • [Source 1]    │────▶│ • [Process 1]   │────▶│ • [Output 1]    │
│ • [Source 2]    │     │ • [Process 2]   │     │ • [Output 2]    │
│ • [Source 3]    │     │ • [Process 3]   │     │ • [Output 3]    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**In plain language:**
1. Data arrives from [sources]
2. We [primary transformations in business terms]
3. Results are delivered to [consumers]

---

## Key Metrics to Watch

> *How do we know the project is working correctly?*

| Metric | Expected Range | Warning Sign |
|--------|----------------|--------------|
| [Output volume] | [Typical range] | [What indicates a problem] |
| [Refresh timing] | [Expected time] | [What indicates a problem] |
| [Quality indicator] | [Expected value] | [What indicates a problem] |

---

## If Something Goes Wrong

> *Quick escalation guidance*

### Signs Something May Be Wrong

- [ ] [Symptom 1 - e.g., "Dashboard showing stale data"]
- [ ] [Symptom 2 - e.g., "Reports not delivered by expected time"]
- [ ] [Symptom 3 - e.g., "Unusual values in output"]

### Who to Contact

| Issue Type | Contact | When |
|------------|---------|------|
| Data not refreshing | [Role/Team] | If data is more than [X hours] late |
| Incorrect values | [Role/Team] | If output values look wrong |
| Access issues | [Role/Team] | If you can't access outputs |
| Business rule questions | [Role/Team] | If you need clarification on logic |

### Escalation Path

```
1. First Contact: [Primary Role]
   ↓ (if unresolved after [timeframe])
2. Escalate to: [Secondary Role]
   ↓ (if critical business impact)
3. Emergency: [Emergency Contact/Process]
```

---

## Related Projects

> *Other projects that interact with this one*

| Project | Relationship |
|---------|--------------|
| [Project A] | [Provides input data / Consumes our output / etc.] |
| [Project B] | [Relationship description] |

---

## Change History

| Date | Change | Impact |
|------|--------|--------|
| [Date] | [Brief description] | [Business impact] |
| [Date] | [Brief description] | [Business impact] |

---

## Document Approval

| Role | Name | Date |
|------|------|------|
| Business Owner | [Role title] | [Date] |
| Technical Owner | [Role title] | [Date] |

---

> **Note**: This executive summary should be reviewed and updated quarterly, or whenever significant changes are made to the project.
