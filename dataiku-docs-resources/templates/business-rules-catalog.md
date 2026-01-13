# Business Rules Catalog Template

> **How to use this template**: Document every business rule, decision point, and calculation in your project. This is the authoritative reference for "why does the data look like this?"

---

# [PROJECT_NAME] - Business Rules Catalog

**Last Updated**: [DATE]
**Document Owner**: [ROLE]
**Business Approver**: [ROLE]

---

## Quick Navigation

- [Rules Index](#rules-index)
- [Rules by Category](#rules-by-category)
- [Decision Trees](#decision-trees)
- [Calculation Definitions](#calculation-definitions)
- [Rule Change History](#rule-change-history)

---

## Rules Index

### Master Rule List

| Rule ID | Rule Name | Category | Location | Owner |
|---------|-----------|----------|----------|-------|
| BR-001 | [Rule Name] | [Category] | [recipe, step] | [Role] |
| BR-002 | [Rule Name] | [Category] | [recipe, step] | [Role] |
| BR-003 | [Rule Name] | [Category] | [recipe, step] | [Role] |
| BR-004 | [Rule Name] | [Category] | [recipe, step] | [Role] |

### Rules by Recipe

| Recipe | Rules Applied |
|--------|---------------|
| [recipe_1] | BR-001, BR-003 |
| [recipe_2] | BR-002 |
| [recipe_3] | BR-004, BR-005, BR-006 |

---

## Rules by Category

### Filtering Rules

*Rules that determine which records are included or excluded*

### Segmentation Rules

*Rules that categorize records into groups*

### Calculation Rules

*Rules that determine how values are computed*

### Validation Rules

*Rules that ensure data quality*

### Transformation Rules

*Rules that modify data values*

---

## Detailed Rule Definitions

---

### BR-001: [Rule Name]

#### Overview

| Property | Value |
|----------|-------|
| **Rule ID** | BR-001 |
| **Category** | [Filtering/Segmentation/Calculation/etc.] |
| **Status** | Active / Under Review / Deprecated |
| **Effective Date** | [Date this rule became active] |
| **Last Reviewed** | [Date] |

#### What This Rule Does

[Plain language explanation that a business user would understand. 2-3 sentences describing the purpose and effect of this rule.]

#### Why This Rule Exists

[Business justification. What business need does this rule address? What would happen without it?]

#### Rule Logic (Simplified)

```
IF [condition in plain language]
THEN [outcome in plain language]
ELSE [alternative outcome]
```

**Note**: Exact threshold values are configured by [role] and reviewed [frequency].

#### Example Scenarios

**Scenario 1**: [Describe a typical case]
> When a [record type] has [characteristic], the system will [action], resulting in [outcome].

**Scenario 2**: [Describe an edge case]
> When a [record type] has [unusual characteristic], the system will [action].

#### Input Requirements

| Field | Source | Required | Description |
|-------|--------|----------|-------------|
| [field_1] | [dataset.field] | Yes | [What this field provides] |
| [field_2] | [dataset.field] | No | [What this field provides] |

#### Output Produced

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| [output_field] | [type] | [possible values] | [What this field represents] |

#### Where Implemented

- **Recipe**: [recipe_name]
- **Step**: [step number or name]
- **Technical Implementation**: [Prepare processor / Python code / SQL / etc.]

#### Edge Cases & Exceptions

| Scenario | Handling |
|----------|----------|
| Missing [field] | [What happens] |
| Invalid [value type] | [What happens] |
| [Edge case] | [What happens] |

#### Ownership

| Role | Responsibility |
|------|----------------|
| Business Owner | [Role] - Defines the rule logic |
| Technical Owner | [Role] - Implements and maintains |
| Change Approval | [Role] - Approves modifications |

#### Related Rules

| Rule | Relationship |
|------|--------------|
| BR-XXX | [Depends on / Feeds into / Conflicts with] |
| BR-YYY | [Relationship description] |

#### Testing / Validation

To verify this rule is working correctly:

1. [Check 1: What to look for]
2. [Check 2: What to verify]
3. [Expected outcome]

---

### BR-002: [Rule Name]

*[Repeat the above structure for each business rule]*

---

## Decision Trees

### Decision Tree: [Process Name]

#### Purpose

[What decision is being made and why it matters]

#### Visual Representation

```
                         ┌──────────────────┐
                         │ Start: [Record]  │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │ Question 1:      │
                         │ [Condition?]     │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │ YES         │             │ NO
                    ▼             │             ▼
            ┌───────────┐        │      ┌───────────┐
            │ Question 2│        │      │ Question 3│
            │ [Cond?]   │        │      │ [Cond?]   │
            └─────┬─────┘        │      └─────┬─────┘
                  │              │            │
             ┌────┴────┐        │       ┌────┴────┐
             │YES  │NO │        │       │YES  │NO │
             ▼     ▼   │        │       ▼     ▼   │
          [Out A][Out B]│        │    [Out C][Out D]│
```

#### Decision Points Explained

| Step | Question | What We're Checking | Data Used |
|------|----------|---------------------|-----------|
| 1 | [Question in plain language] | [What the condition evaluates] | [field(s)] |
| 2 | [Question in plain language] | [What the condition evaluates] | [field(s)] |
| 3 | [Question in plain language] | [What the condition evaluates] | [field(s)] |

#### Possible Outcomes

| Outcome | Label | Description | Count/Proportion |
|---------|-------|-------------|------------------|
| A | [Label] | [What this outcome means] | [Typical %] |
| B | [Label] | [What this outcome means] | [Typical %] |
| C | [Label] | [What this outcome means] | [Typical %] |
| D | [Label] | [What this outcome means] | [Typical %] |

#### Implementation Location

| Decision Point | Recipe | Step |
|----------------|--------|------|
| Question 1 | [recipe] | [step] |
| Question 2 | [recipe] | [step] |
| Question 3 | [recipe] | [step] |

---

## Calculation Definitions

### Calculation: [Metric/Field Name]

#### What It Measures

[Plain language description of what this calculation represents]

#### Why It Matters

[Business importance of this metric]

#### Calculation Method (Conceptual)

```
[Result] = [Component A] [operation] [Component B] [operation] ...
```

**Note**: Actual formula uses parameters configured by [role].

#### Components

| Component | Source | Description |
|-----------|--------|-------------|
| [Component A] | [field or calculation] | [What it represents] |
| [Component B] | [field or calculation] | [What it represents] |

#### Interpretation Guide

| Value Range | Interpretation |
|-------------|----------------|
| [High range] | [What this indicates] |
| [Medium range] | [What this indicates] |
| [Low range] | [What this indicates] |
| Null/Missing | [What this means] |

#### Related Business Rules

- BR-XXX: [How this calculation is used]

---

## Exception Handling

### How Exceptions Are Managed

| Exception Type | Detection | Handling | Escalation |
|----------------|-----------|----------|------------|
| [Exception 1] | [How detected] | [What happens] | [Who's notified] |
| [Exception 2] | [How detected] | [What happens] | [Who's notified] |

### Exception Routing Rules

```
Record fails [validation]
    │
    ├── [Exception Type A]
    │   └── Route to: [destination/process]
    │
    ├── [Exception Type B]
    │   └── Route to: [destination/process]
    │
    └── [Unknown Exception]
        └── Route to: [manual review queue]
```

---

## Rule Change Process

### How to Request a Rule Change

1. **Identify the rule** using this catalog
2. **Document the requested change** and business justification
3. **Submit to**: [Role/Process]
4. **Required approvals**: [List of approvers]
5. **Lead time**: [Typical time required]

### Change Impact Assessment

Before changing a rule, assess:

- [ ] Which outputs are affected?
- [ ] Which downstream processes depend on this?
- [ ] Who needs to be notified?
- [ ] Is testing required?
- [ ] Documentation updates needed?

---

## Rule Change History

### Recent Changes

| Date | Rule ID | Change Description | Approved By | Effective Date |
|------|---------|-------------------|-------------|----------------|
| [Date] | BR-XXX | [What changed] | [Role] | [Date] |
| [Date] | BR-YYY | [What changed] | [Role] | [Date] |

### Upcoming Changes

| Target Date | Rule ID | Planned Change | Status |
|-------------|---------|----------------|--------|
| [Date] | BR-XXX | [Description] | [Pending/Approved] |

---

## Appendix: Rule Templates

### Template for New Rule Documentation

```markdown
### BR-XXX: [Rule Name]

#### Overview
| Property | Value |
|----------|-------|
| **Rule ID** | BR-XXX |
| **Category** | [Category] |
| **Status** | Draft |
| **Proposed Effective Date** | [Date] |

#### What This Rule Does
[Description]

#### Why This Rule Exists
[Business justification]

#### Rule Logic (Simplified)
[Logic description]

#### Implementation Plan
[Where and how it will be implemented]

#### Approval
- [ ] Business Owner: [Role]
- [ ] Technical Owner: [Role]
- [ ] Final Approval: [Role]
```

---

## Quick Reference: Finding Rules

**"Why was this record filtered out?"**
→ See Filtering Rules section

**"How was this category/segment assigned?"**
→ See Segmentation Rules section

**"How was this value calculated?"**
→ See Calculation Definitions section

**"What happens when data is invalid?"**
→ See Exception Handling section
