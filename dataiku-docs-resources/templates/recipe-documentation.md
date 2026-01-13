# Recipe Documentation Template

> **How to use this template**: Create one document per recipe, or compile multiple recipes into a single document with one section per recipe.

---

## Recipe: [RECIPE_NAME]

### Quick Facts

| Property | Value |
|----------|-------|
| **Recipe Name** | [recipe_name] |
| **Recipe Type** | [Prepare / Join / Stack / Group / Python / SQL / etc.] |
| **Location** | [Zone name in flow] |
| **Inputs** | [List of input datasets] |
| **Outputs** | [List of output datasets] |
| **Run Schedule** | [Part of which scenario, how often] |
| **Typical Duration** | [Expected run time] |

---

### What This Recipe Does

> *Describe in plain language what this recipe accomplishes. A non-technical person should understand after reading this.*

[2-3 sentences describing the business purpose and transformation]

**Example:**
> This recipe combines customer profile information with their recent purchase history to create a single view of each customer. It matches records using customer ID and adds calculated fields for total spending and purchase frequency.

---

### Why This Recipe Exists

> *Business justification for this transformation*

[Explain the business need this recipe addresses]

---

### Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ [input_1]       │────▶│                 │────▶│ [output]        │
│ [description]   │     │  [recipe_name]  │     │ [description]   │
└─────────────────┘     │                 │     └─────────────────┘
                        │                 │
┌─────────────────┐     │                 │
│ [input_2]       │────▶│                 │
│ [description]   │     └─────────────────┘
└─────────────────┘

Record Flow: [MANY] → [RESULT] because [reason]
Example: 1000 customers + 5000 orders → 1000 enriched customer records (1:N join aggregated)
```

---

### Step-by-Step Explanation

> *For Prepare recipes, document each step. For other recipe types, document the key logic.*

#### For Prepare Recipes:

| Step # | Step Name | What It Does | Why | Business Rule |
|--------|-----------|--------------|-----|---------------|
| 1 | [name] | [plain language description] | [business reason] | [BR-XXX or N/A] |
| 2 | [name] | [plain language description] | [business reason] | [BR-XXX or N/A] |
| 3 | [name] | [plain language description] | [business reason] | [BR-XXX or N/A] |
| ... | ... | ... | ... | ... |

#### For Join Recipes:

| Property | Value |
|----------|-------|
| **Join Type** | [Inner / Left / Right / Full / Cross] |
| **Left Dataset** | [dataset_name] |
| **Right Dataset** | [dataset_name] |
| **Join Keys** | Left.[field] = Right.[field] |
| **Result** | [What the joined result represents] |

**Join Explanation:**
[Explain in plain language what the join accomplishes and why this join type was chosen]

#### For Group/Aggregate Recipes:

| Property | Value |
|----------|-------|
| **Group By** | [Fields used for grouping] |
| **Aggregations** | [List of aggregations performed] |

| Output Field | Aggregation | Source Field | Purpose |
|--------------|-------------|--------------|---------|
| [field] | [SUM/AVG/COUNT/etc.] | [source] | [why needed] |

#### For Python/SQL Recipes:

**Purpose**: [What the code accomplishes]

**Logic Summary**:
1. [Step 1 in plain language]
2. [Step 2 in plain language]
3. [Step 3 in plain language]

**Key Operations**:
- [Operation 1]: [Description]
- [Operation 2]: [Description]

---

### Business Rules Applied

| Rule ID | Rule Name | How Applied |
|---------|-----------|-------------|
| [BR-XXX] | [name] | [How this rule is implemented in this recipe] |
| [BR-YYY] | [name] | [How this rule is implemented in this recipe] |

---

### Input Requirements

| Input Dataset | Required Fields | Why Needed |
|---------------|-----------------|------------|
| [input_1] | [field_list] | [What these fields are used for] |
| [input_2] | [field_list] | [What these fields are used for] |

---

### Output Produced

| Output Field | Type | Description | Source |
|--------------|------|-------------|--------|
| [field_1] | [type] | [what it represents] | [direct copy / derived / calculated] |
| [field_2] | [type] | [what it represents] | [source] |
| [field_3] | [type] | [what it represents] | [source] |

---

### Data Quality Checks

| Check | Condition | Action if Failed |
|-------|-----------|------------------|
| [check_1] | [what is validated] | [what happens] |
| [check_2] | [what is validated] | [what happens] |

---

### Edge Cases & Exception Handling

| Scenario | Handling |
|----------|----------|
| [Input field is null] | [What happens] |
| [No matching records in join] | [What happens] |
| [Unexpected value] | [What happens] |
| [Empty input dataset] | [What happens] |

---

### What Could Go Wrong

| Failure Mode | Symptoms | Likely Cause | Resolution |
|--------------|----------|--------------|------------|
| [failure_1] | [what you'd see] | [common cause] | [how to fix] |
| [failure_2] | [what you'd see] | [common cause] | [how to fix] |
| [failure_3] | [what you'd see] | [common cause] | [how to fix] |

---

### Dependencies

**Upstream (This recipe needs):**
- [upstream_dataset_1] must be built
- [upstream_dataset_2] must contain [required data]

**Downstream (Depends on this recipe):**
- [downstream_recipe_1] uses output for [purpose]
- [downstream_recipe_2] uses output for [purpose]

---

### Performance Notes

| Metric | Typical Value | Alert If |
|--------|---------------|----------|
| Run time | [typical duration] | > [threshold] |
| Output rows | [typical count] | < [threshold] or > [threshold] |
| Memory usage | [typical] | [threshold] |

---

### Modification Guide

**If you need to modify this recipe:**

1. **Before making changes:**
   - [ ] Review downstream dependencies
   - [ ] Get approval from [role] if changing business rules
   - [ ] Test in development first

2. **Common modifications:**
   - Adding a field: [where and how]
   - Changing a filter: [where and how]
   - Updating a calculation: [where and how]

3. **After making changes:**
   - [ ] Test output data quality
   - [ ] Verify downstream processes still work
   - [ ] Update this documentation

---

### Related Documentation

| Document | Relevance |
|----------|-----------|
| Flow Documentation | Overall pipeline context |
| Business Rules Catalog | Rule definitions |
| Data Dictionary | Field definitions |

---

### Change History

| Date | Change | Made By | Reason |
|------|--------|---------|--------|
| [date] | [what changed] | [role] | [why] |
