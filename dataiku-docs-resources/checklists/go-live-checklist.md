# Go-Live Checklist

> **How to use this checklist**: Complete all items before deploying a new Dataiku project or major changes to production.

---

# [PROJECT_NAME] - Go-Live Checklist

**Target Go-Live Date**: [DATE]
**Project Owner**: [ROLE]
**Go-Live Coordinator**: [ROLE]

---

## Pre-Go-Live: Planning (1-2 Weeks Before)

### Stakeholder Readiness

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| All stakeholders identified and notified | ☐ | | |
| Go-live date agreed with all parties | ☐ | | |
| Consumer training completed | ☐ | | |
| Support team briefed | ☐ | | |
| Communication plan prepared | ☐ | | |

### Documentation Readiness

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Executive Summary complete | ☐ | | |
| Flow Documentation complete | ☐ | | |
| Data Dictionary complete | ☐ | | |
| Business Rules Catalog complete | ☐ | | |
| Operations Guide complete | ☐ | | |
| Troubleshooting Guide complete | ☐ | | |
| Documentation review passed | ☐ | | |

### Technical Readiness

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Development testing complete | ☐ | | |
| Performance testing complete | ☐ | | |
| Data quality validation complete | ☐ | | |
| Integration testing with consumers complete | ☐ | | |
| Security review passed | ☐ | | |
| Code review completed | ☐ | | |

---

## Pre-Go-Live: Final Preparation (1 Week Before)

### Environment Setup

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Production environment configured | ☐ | | |
| Production connections established | ☐ | | |
| Production credentials set up | ☐ | | |
| Scenarios configured and scheduled | ☐ | | |
| Monitoring and alerts configured | ☐ | | |

### Access & Permissions

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Production access granted to operators | ☐ | | |
| Consumer access configured | ☐ | | |
| Service accounts created | ☐ | | |
| Permission testing completed | ☐ | | |

### Rollback Preparation

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Rollback plan documented | ☐ | | |
| Rollback tested (if applicable) | ☐ | | |
| Rollback decision criteria defined | ☐ | | |
| Previous state preserved (if replacing) | ☐ | | |

---

## Pre-Go-Live: Final Checks (1-2 Days Before)

### Data Validation

| Check | Status | Notes |
|-------|--------|-------|
| Source data connections verified | ☐ | |
| Test run completed successfully | ☐ | |
| Output data quality verified | ☐ | |
| Output format matches consumer expectations | ☐ | |
| Historical comparison (if applicable) | ☐ | |

### Operational Readiness

| Check | Status | Notes |
|-------|--------|-------|
| Schedule confirmed appropriate | ☐ | |
| SLA commitments documented | ☐ | |
| On-call support arranged | ☐ | |
| Escalation contacts confirmed | ☐ | |
| Notification channels tested | ☐ | |

### Final Sign-Off

| Approval | Name/Role | Date | Signature |
|----------|-----------|------|-----------|
| Technical Owner | | | |
| Business Owner | | | |
| Data Governance (if required) | | | |
| Security (if required) | | | |

---

## Go-Live Day

### Pre-Launch (Morning of Go-Live)

| Item | Time | Status | Owner | Notes |
|------|------|--------|-------|-------|
| Final environment check | | ☐ | | |
| Source data availability confirmed | | ☐ | | |
| Team members on standby | | ☐ | | |
| Communication channels active | | ☐ | | |
| Rollback resources ready | | ☐ | | |

### Launch Execution

| Item | Time | Status | Owner | Notes |
|------|------|--------|-------|-------|
| Scenario enabled/triggered | | ☐ | | |
| Job execution started | | ☐ | | |
| Job execution completed | | ☐ | | |
| Initial output validation | | ☐ | | |
| Consumer notification sent | | ☐ | | |

### Post-Launch Verification

| Check | Status | Notes |
|-------|--------|-------|
| All jobs completed successfully | ☐ | |
| Output row counts within expected range | ☐ | |
| Key fields populated correctly | ☐ | |
| Consumers can access output | ☐ | |
| No unexpected errors in logs | ☐ | |

---

## Post-Go-Live: Day 1

### Morning After Check

| Check | Status | Notes |
|-------|--------|-------|
| Scheduled run completed on time | ☐ | |
| Data quality acceptable | ☐ | |
| No consumer complaints | ☐ | |
| Monitoring/alerts working | ☐ | |

### Issue Log

| Issue # | Description | Severity | Status | Resolution |
|---------|-------------|----------|--------|------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Go/No-Go Decision

| Time | Decision | Made By |
|------|----------|---------|
| End of Day 1 | ☐ Continue / ☐ Monitor Closely / ☐ Rollback | |

---

## Post-Go-Live: Week 1

### Daily Checks

| Day | Run Status | Data Quality | Consumer Feedback | Issues |
|-----|------------|--------------|-------------------|--------|
| Day 2 | ☐ OK | ☐ OK | ☐ OK | |
| Day 3 | ☐ OK | ☐ OK | ☐ OK | |
| Day 4 | ☐ OK | ☐ OK | ☐ OK | |
| Day 5 | ☐ OK | ☐ OK | ☐ OK | |
| Day 6 | ☐ OK | ☐ OK | ☐ OK | |
| Day 7 | ☐ OK | ☐ OK | ☐ OK | |

### Week 1 Review

| Item | Status | Notes |
|------|--------|-------|
| All scheduled runs successful | ☐ | |
| Performance within expectations | ☐ | |
| No critical issues outstanding | ☐ | |
| Consumer satisfaction confirmed | ☐ | |
| Documentation updates completed | ☐ | |

---

## Post-Go-Live: Stabilization (Weeks 2-4)

### Week 2-4 Monitoring

| Week | Stability | Issues Resolved | Notes |
|------|-----------|-----------------|-------|
| Week 2 | ☐ Stable | | |
| Week 3 | ☐ Stable | | |
| Week 4 | ☐ Stable | | |

### Transition to BAU

| Item | Status | Date |
|------|--------|------|
| Hypercare period complete | ☐ | |
| Knowledge transfer to BAU team | ☐ | |
| Handover documentation complete | ☐ | |
| Project closed | ☐ | |

---

## Go-Live Communication Templates

### Go-Live Announcement

```
Subject: [PROJECT_NAME] - Go-Live Notification

Dear stakeholders,

[PROJECT_NAME] is now live in production.

What this means:
- [Output 1] is now available at [location]
- [Output 2] is now available at [location]
- Data will be refreshed [frequency]

What you need to do:
- [Action 1]
- [Action 2]

Support contacts:
- Technical issues: [contact]
- Business questions: [contact]

Thank you for your support during this launch.

Best regards,
[Project Team]
```

### Issue Notification

```
Subject: [PROJECT_NAME] - Issue Notification

We have identified an issue with [PROJECT_NAME]:

Issue: [Brief description]
Impact: [What's affected]
Status: [Investigating/Fixing/Resolved]
ETA: [Expected resolution]

We will provide updates as available.

Contact: [Support contact]
```

---

## Emergency Rollback Procedure

### Rollback Triggers

Initiate rollback if:
- [ ] Critical data quality issues affecting business decisions
- [ ] Complete job failures with no quick fix
- [ ] Security or compliance concerns
- [ ] Overwhelming consumer complaints

### Rollback Steps

1. [ ] Notify stakeholders of rollback decision
2. [ ] Disable production scenarios
3. [ ] [Specific rollback step 1]
4. [ ] [Specific rollback step 2]
5. [ ] Restore previous state (if applicable)
6. [ ] Verify rollback successful
7. [ ] Communicate rollback completion
8. [ ] Schedule post-mortem

### Post-Rollback

- [ ] Document root cause
- [ ] Plan remediation
- [ ] Schedule re-launch attempt
