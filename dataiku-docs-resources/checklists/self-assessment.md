# Self-Assessment Checklist

> **How to use this checklist**: After reviewing project documentation and training, use this to verify your understanding. You should be able to answer all questions before accepting ownership.

---

# [PROJECT_NAME] - Self-Assessment Checklist

**Assessor**: [YOUR NAME/ROLE]
**Date**: [DATE]

---

## Instructions

For each question:
- ✅ **Yes** = I can confidently answer/do this
- ⚠️ **Partial** = I need more clarity
- ❌ **No** = I need training/review on this

Review any ⚠️ or ❌ items with the current owner before handover completion.

---

## Level 1: Basic Understanding

*Can you explain the project to a non-technical stakeholder?*

### Business Context

| Question | Status | Notes |
|----------|--------|-------|
| What business problem does this project solve? | ☐ | |
| Who are the primary consumers of the outputs? | ☐ | |
| What decisions or actions do the outputs enable? | ☐ | |
| What would happen if this project stopped working? | ☐ | |
| How does this project fit into the larger data ecosystem? | ☐ | |

**Self-Check**: Explain the project's purpose in one sentence:
> _______________________________________________________________

### Data Overview

| Question | Status | Notes |
|----------|--------|-------|
| What are the main data sources? | ☐ | |
| What are the main outputs? | ☐ | |
| When does the data refresh? | ☐ | |
| Who owns the source data? | ☐ | |
| Who consumes the output data? | ☐ | |

### Schedule & SLAs

| Question | Status | Notes |
|----------|--------|-------|
| When does the project run? | ☐ | |
| When must outputs be available? | ☐ | |
| What is the expected run duration? | ☐ | |
| What happens if data is late? | ☐ | |

---

## Level 2: Operational Competence

*Can you operate the project day-to-day?*

### Daily Operations

| Question | Status | Notes |
|----------|--------|-------|
| How do I check if today's run succeeded? | ☐ | |
| Where do I find job logs? | ☐ | |
| How do I verify output data is fresh? | ☐ | |
| How do I run a scenario manually? | ☐ | |
| How do I rebuild a single dataset? | ☐ | |

**Self-Check**: Describe your morning check routine:
> _______________________________________________________________

### Monitoring & Alerts

| Question | Status | Notes |
|----------|--------|-------|
| What alerts are configured? | ☐ | |
| How will I be notified of failures? | ☐ | |
| What metrics should I watch? | ☐ | |
| What indicates a problem? | ☐ | |

### Basic Troubleshooting

| Question | Status | Notes |
|----------|--------|-------|
| What's the first thing to check when a job fails? | ☐ | |
| How do I find error messages? | ☐ | |
| What are the three most common issues? | ☐ | |
| When should I escalate vs. fix myself? | ☐ | |

**Self-Check**: A job failed. What are your first three steps?
> 1. _____________________________________________________________
> 2. _____________________________________________________________
> 3. _____________________________________________________________

### Contacts & Escalation

| Question | Status | Notes |
|----------|--------|-------|
| Who do I contact for data source issues? | ☐ | |
| Who do I contact for business logic questions? | ☐ | |
| Who do I contact for infrastructure issues? | ☐ | |
| What's the escalation path for critical issues? | ☐ | |

---

## Level 3: Technical Understanding

*Can you navigate and understand the project structure?*

### Flow Navigation

| Question | Status | Notes |
|----------|--------|-------|
| Can I find any recipe within 30 seconds? | ☐ | |
| Can I identify all the zones in the project? | ☐ | |
| Can I explain what each zone does? | ☐ | |
| Can I trace data from source to output? | ☐ | |

**Self-Check**: Name the main zones and their purposes:
> 1. _____________________________________________________________
> 2. _____________________________________________________________
> 3. _____________________________________________________________

### Recipe Understanding

| Question | Status | Notes |
|----------|--------|-------|
| Can I explain what each recipe type does? | ☐ | |
| Can I identify the critical path recipes? | ☐ | |
| Can I find where specific transformations occur? | ☐ | |
| Can I read and understand recipe configurations? | ☐ | |

### Data Lineage

| Question | Status | Notes |
|----------|--------|-------|
| Can I trace a specific output field to its source? | ☐ | |
| Can I identify what transformations affect a field? | ☐ | |
| Can I determine impact of changing a source field? | ☐ | |

**Self-Check**: Trace [key_output_field] back to its source:
> Output: _____________ ← Recipe: _____________ ← Source: _____________

### Business Rules

| Question | Status | Notes |
|----------|--------|-------|
| Can I locate the Business Rules Catalog? | ☐ | |
| Can I find where a specific rule is implemented? | ☐ | |
| Can I explain the major decision points? | ☐ | |
| Do I understand why each rule exists? | ☐ | |

**Self-Check**: Explain BR-001 (or main business rule) in plain language:
> _______________________________________________________________

---

## Level 4: Maintenance Capability

*Can you make changes and maintain the project?*

### Making Changes

| Question | Status | Notes |
|----------|--------|-------|
| Do I know the change request process? | ☐ | |
| Can I assess impact before making changes? | ☐ | |
| Do I know what changes require approval? | ☐ | |
| Can I make changes in development first? | ☐ | |
| Can I test changes before production? | ☐ | |

### Common Modifications

| Question | Status | Notes |
|----------|--------|-------|
| Could I add a new field to the output? | ☐ | |
| Could I modify a business rule threshold? | ☐ | |
| Could I add a new filter condition? | ☐ | |
| Could I update documentation after a change? | ☐ | |

### Documentation

| Question | Status | Notes |
|----------|--------|-------|
| Do I know where all documentation is stored? | ☐ | |
| Can I update documentation when changes are made? | ☐ | |
| Do I understand the documentation structure? | ☐ | |

---

## Level 5: Edge Cases & Exceptions

*Do you understand the unusual situations?*

### Known Issues

| Question | Status | Notes |
|----------|--------|-------|
| What are the known quirks of this project? | ☐ | |
| Are there any workarounds in use? | ☐ | |
| What historical issues should I know about? | ☐ | |

### Edge Cases

| Question | Status | Notes |
|----------|--------|-------|
| What happens when source data is missing? | ☐ | |
| What happens with unexpected data values? | ☐ | |
| How are exceptions handled? | ☐ | |
| Where do exception records go? | ☐ | |

### Seasonal/Cyclical Considerations

| Question | Status | Notes |
|----------|--------|-------|
| Are there monthly patterns to watch for? | ☐ | |
| Are there year-end considerations? | ☐ | |
| Are there holiday impacts? | ☐ | |
| Are there business cycle impacts? | ☐ | |

---

## Assessment Summary

### Score Summary

| Level | Questions | ✅ Yes | ⚠️ Partial | ❌ No |
|-------|-----------|--------|------------|-------|
| Level 1: Basic Understanding | | | | |
| Level 2: Operational Competence | | | | |
| Level 3: Technical Understanding | | | | |
| Level 4: Maintenance Capability | | | | |
| Level 5: Edge Cases | | | | |
| **TOTAL** | | | | |

### Readiness Assessment

**Minimum for Ownership**:
- Level 1: All ✅
- Level 2: All ✅
- Level 3: Mostly ✅ (some ⚠️ acceptable)
- Level 4: Mostly ✅ (some ⚠️ acceptable with support plan)
- Level 5: Awareness (⚠️ acceptable)

### Areas Needing Review

| Item | Current Status | Action Needed |
|------|----------------|---------------|
| | | |
| | | |
| | | |

### Sign-Off

```
I have completed this self-assessment honestly and identified areas
where I need additional support or training.

Assessor: _________________ Date: _______

Reviewed by: _________________ Date: _______
```

---

## Next Steps

For any ⚠️ or ❌ items:

1. [ ] Schedule review session with current owner
2. [ ] Review relevant documentation
3. [ ] Practice hands-on in development environment
4. [ ] Re-assess after additional training
