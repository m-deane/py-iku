# Operations Guide

> **How to use this guide**: Reference this for day-to-day operations, monitoring, and routine maintenance of your Dataiku project.

---

# [PROJECT_NAME] - Operations Guide

**Last Updated**: [DATE]
**On-Call Contact**: [ROLE]

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════════╗
║                    DAILY OPERATIONS QUICK REF                  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  MORNING CHECK (5 min):                                        ║
║  1. Jobs → Check overnight scenario status                     ║
║  2. Verify output data freshness                               ║
║  3. Review any alerts/notifications                            ║
║                                                                ║
║  IF SOMETHING LOOKS WRONG:                                     ║
║  1. Check job logs for error messages                          ║
║  2. Verify source data arrived                                 ║
║  3. See Troubleshooting section below                          ║
║                                                                ║
║  CONTACTS:                                                     ║
║  • Data issues: [Role]                                         ║
║  • Infrastructure: [Role]                                      ║
║  • Business questions: [Role]                                  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Schedule Overview

### Automated Runs

| Scenario | Schedule | What It Does | Expected Duration |
|----------|----------|--------------|-------------------|
| [scenario_1] | [schedule, e.g., "Daily 6:00 AM"] | [brief description] | [duration] |
| [scenario_2] | [schedule] | [brief description] | [duration] |
| [scenario_3] | [schedule] | [brief description] | [duration] |

### Data Source Timing

| Source | Data Available | Our Process Starts | Margin |
|--------|----------------|-------------------|--------|
| [source_1] | [time] | [time] | [buffer time] |
| [source_2] | [time] | [time] | [buffer time] |

### Output Delivery SLAs

| Output | Must Be Ready By | Typical Completion | Alert If Late By |
|--------|------------------|-------------------|------------------|
| [output_1] | [time] | [typical time] | [threshold] |
| [output_2] | [time] | [typical time] | [threshold] |

---

## Daily Operations

### Morning Health Check (5 minutes)

#### Step 1: Check Scenario Status

1. Navigate to: **Automation** → **Scenarios**
2. Verify overnight scenarios show ✅ green
3. Note any failures for investigation

**What to look for:**
| Status | Meaning | Action |
|--------|---------|--------|
| ✅ Green | Success | None needed |
| ❌ Red | Failed | Investigate immediately |
| 🟡 Yellow | Warning | Review logs |
| ⚪ Gray | Didn't run | Check trigger/schedule |

#### Step 2: Verify Data Freshness

1. Navigate to: **Flow**
2. Check key output datasets
3. Verify "Last built" timestamps are current

**Expected freshness:**
| Dataset | Should Be Updated | Check Location |
|---------|-------------------|----------------|
| [output_1] | By [time] | Flow → [dataset] |
| [output_2] | By [time] | Flow → [dataset] |

#### Step 3: Review Alerts

1. Check notification channels (email, Slack, etc.)
2. Review any overnight alerts
3. Acknowledge and address as needed

### Weekly Tasks

| Day | Task | How To |
|-----|------|--------|
| [Day] | [Task 1] | [Brief instructions] |
| [Day] | [Task 2] | [Brief instructions] |
| [Day] | Review job history for patterns | Jobs → filter last 7 days |

### Monthly Tasks

| Task | When | How To |
|------|------|--------|
| Review data quality trends | First week | [Instructions] |
| Clean up old job logs | Mid-month | [Instructions] |
| Verify documentation accuracy | End of month | [Instructions] |

---

## How to Run Jobs

### Run a Scenario Manually

**When to use**: When you need to run the full pipeline outside of scheduled times

1. Navigate to: **Automation** → **Scenarios**
2. Click on scenario name: `[scenario_name]`
3. Click **Run** button (top right)
4. Select: "Run now"
5. Monitor progress in **Jobs** tab

**Important**:
- Full run takes approximately [duration]
- Notify [stakeholders] if running outside normal schedule

### Run a Single Recipe

**When to use**: When you need to rebuild just one step

1. Navigate to: **Flow**
2. Click on the recipe you want to run
3. Click **Run** button
4. Choose:
   - "Build only this recipe" - Just this step
   - "Build required" - This step and anything upstream that's stale

### Run from a Specific Point

**When to use**: When earlier steps succeeded but later steps failed

1. Navigate to: **Flow**
2. Click on the dataset where you want to START rebuilding
3. Right-click → "Build flow outputs"
4. Select which downstream outputs to rebuild

---

## Monitoring

### Key Metrics to Watch

| Metric | Where to Find | Normal Range | Alert Threshold |
|--------|---------------|--------------|-----------------|
| Job duration | Jobs → [scenario] | [range] | > [threshold] |
| Output row count | [dataset] → Metrics | [range] | < [threshold] |
| Error rate | [dashboard/logs] | [expected] | > [threshold] |

### Setting Up Alerts

#### Scenario Failure Alerts

1. Go to: Scenario → Settings → Reporters
2. Add reporter for: "Scenario fails"
3. Configure notification: [email/Slack/etc.]

#### Data Quality Alerts

1. Go to: Dataset → Settings → Metrics
2. Configure: [specific checks]
3. Set thresholds and notifications

### Log Locations

| Log Type | Location | Retention |
|----------|----------|-----------|
| Job logs | Jobs → [job] → Logs | [period] |
| Scenario history | Automation → Scenarios → [name] → Runs | [period] |
| System logs | [Admin location] | [period] |

---

## Common Operations

### Rerunning After Failure

#### If a scenario failed:

1. **Diagnose**: Check job log for error message
2. **Fix**: Address the root cause (see Troubleshooting)
3. **Rerun**:
   - If fix was in data: Rerun full scenario
   - If fix was in recipe: Rebuild from that point

#### If data needs to be rebuilt from scratch:

1. Go to output dataset
2. Click **Clear** (removes existing data)
3. Rebuild using scenario or manual run

**⚠️ Warning**: Clearing data removes it until rebuild completes. Coordinate with consumers.

### Handling Late Source Data

**Scenario**: Source data arrives late

1. **Check**: Is source data now available?
2. **If yes**: Run scenario manually
3. **If no**: Contact source system owner ([contact])
4. **Notify**: Inform downstream consumers of delay

### Handling Schema Changes

**Scenario**: Source data structure changed

1. **Identify**: Which fields changed?
2. **Impact**: Which recipes are affected?
3. **Update**: Modify recipes to handle new schema
4. **Test**: Run in development first
5. **Deploy**: Apply changes to production

---

## Access Management

### Required Permissions

| Task | Required Role | How to Request |
|------|---------------|----------------|
| View jobs/data | [Role] | [Process] |
| Run scenarios | [Role] | [Process] |
| Modify recipes | [Role] | [Process] |
| Admin functions | [Role] | [Process] |

### Access Troubleshooting

| Error | Meaning | Resolution |
|-------|---------|------------|
| "Permission denied" | Insufficient role | Request access from [contact] |
| "Dataset not found" | Access not granted | Verify permissions in project settings |

---

## Maintenance Windows

### Scheduled Downtime

| System | Maintenance Window | Impact |
|--------|-------------------|--------|
| Dataiku Platform | [day/time] | All jobs paused |
| [Source System] | [day/time] | Source data delayed |
| [Database] | [day/time] | [specific impact] |

### During Maintenance

1. Jobs will be paused/delayed
2. Monitor for automatic recovery after maintenance
3. Manually trigger if needed post-maintenance

---

## Capacity Planning

### Current Resource Usage

| Resource | Current | Limit | Alert At |
|----------|---------|-------|----------|
| Storage | [usage] | [limit] | [threshold] |
| Compute | [usage] | [limit] | [threshold] |
| [other] | [usage] | [limit] | [threshold] |

### Growth Considerations

- Data volume grows approximately [rate]
- Review capacity [frequency]
- Contact [role] for capacity increases

---

## Backup and Recovery

### What Is Backed Up

| Component | Backup Frequency | Retention | Recovery Time |
|-----------|------------------|-----------|---------------|
| Project configuration | [frequency] | [period] | [time] |
| Dataset data | [frequency] | [period] | [time] |
| Job history | [frequency] | [period] | [time] |

### Recovery Procedures

#### To restore a previous version:

1. [Step 1]
2. [Step 2]
3. [Step 3]

#### To rebuild data from scratch:

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Escalation Matrix

| Issue Type | First Contact | Escalate After | Escalate To |
|------------|---------------|----------------|-------------|
| Job failures | Self-diagnose | 30 min | [Role] |
| Data quality | [Role] | 1 hour | [Role] |
| Infrastructure | [Role] | Immediate | [Role] |
| Business logic | [Role] | Next business day | [Role] |

### Emergency Contacts

| Situation | Contact | Method |
|-----------|---------|--------|
| Critical failure | [Role] | [phone/slack/etc.] |
| Security concern | [Role] | [method] |
| Data breach | [Role] | [method] |

---

## Documentation Quick Links

| Need Help With | See |
|----------------|-----|
| Understanding the flow | Flow Documentation |
| Data field meanings | Data Dictionary |
| Business rule details | Business Rules Catalog |
| Troubleshooting | Troubleshooting Playbook |
| New analyst orientation | Onboarding Guide |
