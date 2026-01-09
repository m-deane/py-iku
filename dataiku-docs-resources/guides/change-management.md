# Change Management Guide

> **How to use this guide**: Follow this process when requesting or making changes to the Dataiku project.

---

# [PROJECT_NAME] - Change Management Guide

**Last Updated**: [DATE]
**Change Coordinator**: [ROLE]

---

## Change Types

### Classification

| Type | Description | Approval Required | Lead Time |
|------|-------------|-------------------|-----------|
| **Emergency** | Critical fix for production issue | Post-hoc | Immediate |
| **Minor** | Small, low-risk changes | Technical Owner | 1 day |
| **Standard** | Normal changes following process | Technical + Business | 3-5 days |
| **Major** | Significant changes to logic/structure | Full approval chain | 1-2 weeks |

### Examples by Type

**Emergency:**
- Fix causing job failures
- Critical data quality issue
- Security vulnerability

**Minor:**
- Rename a column in output
- Adjust logging
- Update documentation

**Standard:**
- Add new output field
- Modify business rule threshold
- Add new data source field

**Major:**
- New data source integration
- Significant logic change
- Architecture modification

---

## Change Request Process

### Step 1: Document the Request

Complete this information:

```markdown
## Change Request

**Requested By**: [Your Role]
**Date**: [Date]
**Type**: [Emergency/Minor/Standard/Major]

### What Change Is Needed?
[Clear description of the desired change]

### Why Is This Change Needed?
[Business justification]

### What Is The Impact?
- Affected outputs: [list]
- Affected consumers: [list]
- Expected benefit: [description]

### Proposed Timeline
- Requested completion: [date]
- Business reason for timeline: [explanation]
```

### Step 2: Impact Assessment

Before approving, assess:

```markdown
## Impact Assessment

### Technical Impact
- [ ] Recipes affected: [list]
- [ ] Datasets affected: [list]
- [ ] Downstream impacts: [list]

### Data Impact
- [ ] Output format changes: [Yes/No]
- [ ] Historical data affected: [Yes/No]
- [ ] Data volume change: [expected change]

### Consumer Impact
- [ ] Consumers notified: [list]
- [ ] Documentation updates needed: [list]
- [ ] Training required: [Yes/No]

### Risk Assessment
- [ ] Risk level: [Low/Medium/High]
- [ ] Rollback possible: [Yes/No]
- [ ] Testing plan: [description]
```

### Step 3: Approval

| Change Type | Approvers Required |
|-------------|-------------------|
| Emergency | Technical Owner (post-hoc documentation) |
| Minor | Technical Owner |
| Standard | Technical Owner + Business Owner |
| Major | Technical Owner + Business Owner + [Additional] |

### Step 4: Implementation

1. Make changes in **Development** environment
2. Test thoroughly
3. Document changes made
4. Deploy to **Production**
5. Verify in production
6. Update documentation

### Step 5: Communication

Notify stakeholders:
- [ ] Change completed notification
- [ ] Documentation updated
- [ ] Training provided (if needed)

---

## Making Changes: Technical Guide

### Change Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHANGE IMPLEMENTATION FLOW                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Request] → [Impact Assessment] → [Approval]                   │
│                                        │                        │
│                                        ▼                        │
│                              ┌──────────────────┐               │
│                              │    DEVELOPMENT   │               │
│                              │  Make changes    │               │
│                              │  Test thoroughly │               │
│                              └────────┬─────────┘               │
│                                       │                         │
│                                       ▼                         │
│                              ┌──────────────────┐               │
│                              │    REVIEW        │               │
│                              │  Code review     │               │
│                              │  Validate output │               │
│                              └────────┬─────────┘               │
│                                       │                         │
│                                       ▼                         │
│                              ┌──────────────────┐               │
│                              │   PRODUCTION     │               │
│                              │  Deploy changes  │               │
│                              │  Monitor         │               │
│                              └────────┬─────────┘               │
│                                       │                         │
│                                       ▼                         │
│                              ┌──────────────────┐               │
│                              │   DOCUMENT       │               │
│                              │  Update docs     │               │
│                              │  Notify users    │               │
│                              └──────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Common Change Scenarios

#### Adding a New Output Field

1. **Identify source**
   - Where does the new field come from?
   - Is it in an existing dataset or new?

2. **Modify flow**
   - Add field to relevant recipes
   - Propagate through pipeline

3. **Update output**
   - Add to final output dataset
   - Update schema documentation

4. **Test**
   - Verify field populated correctly
   - Check impact on downstream

5. **Document**
   - Update Data Dictionary
   - Update consumer documentation

#### Modifying a Business Rule

1. **Locate the rule**
   - Find in Business Rules Catalog
   - Identify implementation location

2. **Get approval**
   - Confirm change with Business Owner
   - Document approved logic

3. **Modify recipe**
   - Update formula/logic
   - Add comments explaining change

4. **Test**
   - Verify rule applies correctly
   - Check edge cases

5. **Document**
   - Update Business Rules Catalog
   - Add to change history

#### Adding a New Data Source

1. **Set up connection**
   - Configure data source in Dataiku
   - Verify connectivity

2. **Create input dataset**
   - Define schema
   - Configure refresh

3. **Integrate into flow**
   - Add to relevant recipes
   - Build data lineage

4. **Update documentation**
   - Add to Data Dictionary
   - Update Flow Documentation

---

## Testing Requirements

### Test Checklist

Before deploying any change:

```markdown
## Test Checklist

### Data Validation
- [ ] Output row counts within expected range
- [ ] Key fields populated correctly
- [ ] No unexpected nulls introduced
- [ ] Data types correct

### Logic Validation
- [ ] Business rules applying correctly
- [ ] Edge cases handled
- [ ] No regression in existing logic

### Integration Validation
- [ ] Upstream data flowing correctly
- [ ] Downstream processes not broken
- [ ] No performance degradation

### Consumer Validation
- [ ] Output format unchanged (or communicated)
- [ ] Consumers can access data
- [ ] No breaking changes
```

---

## Rollback Procedures

### When to Rollback

- Change causing failures in production
- Data quality significantly degraded
- Consumers unable to use output

### How to Rollback

#### For Recipe Changes:

1. Open recipe in Dataiku
2. Access version history (if available)
3. Revert to previous version
4. Rebuild affected datasets

#### For Schema Changes:

1. Revert recipe changes
2. Clear affected datasets
3. Rebuild from clean state

#### For Major Changes:

1. Contact [Technical Owner]
2. Coordinate rollback plan
3. Execute rollback
4. Verify recovery
5. Notify stakeholders

---

## Communication Templates

### Change Notification (Pre-Change)

```
Subject: [PROJECT_NAME] - Upcoming Change Notification

Hi team,

A change to [PROJECT_NAME] is scheduled:

**What**: [Brief description of change]
**When**: [Date and time]
**Impact**: [What consumers will notice]
**Action Required**: [Any actions needed from recipients]

Please contact [name/role] with questions.
```

### Change Completion Notification

```
Subject: [PROJECT_NAME] - Change Completed

Hi team,

The following change has been deployed:

**What Changed**: [Description]
**Effective**: [Date/time]
**What's Different**: [Observable changes]
**Documentation**: [Link to updated docs]

Contact [name/role] if you notice any issues.
```

### Issue Notification

```
Subject: [PROJECT_NAME] - Issue Notification

Hi team,

An issue has been identified:

**Problem**: [Brief description]
**Impact**: [What's affected]
**Status**: [Investigating/Fixing/Resolved]
**ETA**: [Expected resolution time]

We will provide updates as available.
```

---

## Change History Log

### Template

| Date | Change ID | Description | Type | Approved By | Implemented By |
|------|-----------|-------------|------|-------------|----------------|
| [Date] | CHG-001 | [Description] | [Type] | [Role] | [Role] |

### Recent Changes

*[Maintain list of recent changes here]*

---

## Contact Directory

| Role | Responsibility | Contact For |
|------|----------------|-------------|
| Technical Owner | Approves technical changes | Implementation questions |
| Business Owner | Approves business logic | Rule changes, new requirements |
| Data Steward | Approves data changes | Schema, quality changes |
| Platform Admin | Infrastructure changes | Performance, access issues |
