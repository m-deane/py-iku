# Data Dictionary Template

> **How to use this template**: Document all datasets and their fields. This is the authoritative reference for what data exists and what it means.

---

# [PROJECT_NAME] - Data Dictionary

**Last Updated**: [DATE]
**Document Owner**: [ROLE]

---

## Quick Navigation

- [Dataset Inventory](#dataset-inventory)
- [Input Datasets](#input-datasets)
- [Intermediate Datasets](#intermediate-datasets)
- [Output Datasets](#output-datasets)
- [Field Cross-Reference](#field-cross-reference)

---

## Dataset Inventory

### Summary View

| Dataset Name | Type | Purpose | Records | Refresh |
|--------------|------|---------|---------|---------|
| [dataset_1] | Input | [brief purpose] | [volume range] | [frequency] |
| [dataset_2] | Intermediate | [brief purpose] | [volume range] | [frequency] |
| [dataset_3] | Output | [brief purpose] | [volume range] | [frequency] |

### Dataset Relationship Map

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA FLOW OVERVIEW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUTS              INTERMEDIATE              OUTPUTS          │
│  ──────              ────────────              ───────          │
│                                                                 │
│  [input_1] ─────┐                                               │
│                 ├───► [staging] ───► [enriched] ───► [output_1] │
│  [input_2] ─────┘                         │                     │
│                                           └────────► [output_2] │
│  [input_3] ─────────────────────────────────────────► [output_3]│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Input Datasets

### [Input Dataset 1 Name]

#### Overview

| Property | Value |
|----------|-------|
| **Full Name** | [project_key].[dataset_name] |
| **Type** | Input |
| **Source System** | [Where this data comes from] |
| **Update Frequency** | [How often source data arrives] |
| **Typical Volume** | [Row count range] |
| **Retention** | [How long data is kept] |
| **Owner** | [Team/Role responsible for source data] |

#### Business Description

[2-3 sentences describing what this data represents in business terms]

#### Field Definitions

| # | Field Name | Data Type | Business Description | Example Values | Required | Notes |
|---|------------|-----------|---------------------|----------------|----------|-------|
| 1 | [field_name] | [String/Integer/Date/etc.] | [What this field represents] | [Example, not real data] | Yes/No | [Any important notes] |
| 2 | [field_name] | [type] | [description] | [example] | Yes/No | [notes] |
| 3 | [field_name] | [type] | [description] | [example] | Yes/No | [notes] |

#### Data Quality Expectations

| Rule | Field(s) | Expected Condition |
|------|----------|-------------------|
| Completeness | [field] | Should never be null |
| Uniqueness | [field] | Should be unique per record |
| Range | [field] | Should be between [min] and [max] |
| Format | [field] | Should match pattern [pattern description] |

#### Known Issues / Quirks

- [Issue 1]: [Description and workaround]
- [Issue 2]: [Description and workaround]

---

### [Input Dataset 2 Name]

*[Repeat the above structure for each input dataset]*

---

## Intermediate Datasets

### [Intermediate Dataset 1 Name]

#### Overview

| Property | Value |
|----------|-------|
| **Full Name** | [project_key].[dataset_name] |
| **Type** | Intermediate |
| **Created By** | [Recipe name that creates this] |
| **Used By** | [Recipes/outputs that consume this] |
| **Purpose** | [Why this intermediate step exists] |

#### Business Description

[Describe what transformation has occurred and why this dataset exists]

#### Key Fields Added/Modified

| Field Name | Source | Transformation | Business Purpose |
|------------|--------|----------------|------------------|
| [new_field] | Calculated | [How it's derived] | [Why it's needed] |
| [modified_field] | [source_field] | [What changed] | [Why] |

#### Full Field Definitions

| # | Field Name | Data Type | Description | Source |
|---|------------|-----------|-------------|--------|
| 1 | [field] | [type] | [description] | [original source or "Derived"] |

---

## Output Datasets

### [Output Dataset 1 Name]

#### Overview

| Property | Value |
|----------|-------|
| **Full Name** | [project_key].[dataset_name] |
| **Type** | Output |
| **Consumers** | [Who/what uses this output] |
| **Refresh Schedule** | [When this is updated] |
| **Delivery Method** | [How consumers access this] |
| **SLA** | [When data must be available] |

#### Business Description

[Describe what this output provides and how it's used]

#### Consumer Guide

**Who Uses This Data:**
- [Consumer 1]: [How they use it]
- [Consumer 2]: [How they use it]

**How to Access:**
[Instructions for how consumers get this data]

**When Data is Available:**
[Timing expectations]

#### Field Definitions

| # | Field Name | Data Type | Business Description | Possible Values | How to Interpret |
|---|------------|-----------|---------------------|-----------------|------------------|
| 1 | [field] | [type] | [what it means] | [values/range] | [interpretation guide] |
| 2 | [field] | [type] | [what it means] | [values/range] | [interpretation guide] |

#### Field Lineage

| Output Field | Source Dataset | Source Field | Transformations Applied |
|--------------|----------------|--------------|------------------------|
| [output_field_1] | [source_dataset] | [source_field] | [list of transformations] |
| [output_field_2] | [source_dataset] | [source_field] | [list of transformations] |
| [output_field_3] | Calculated | N/A | [how it's derived] |

#### Common Questions About This Output

**Q: Why might [field] be empty/null?**
A: [Explanation]

**Q: What does it mean when [field] has value [X]?**
A: [Explanation]

**Q: Why don't I see record [type] in this output?**
A: [Explanation of filters applied]

---

## Field Cross-Reference

### Field → Dataset Map

> *Find which datasets contain a specific field*

| Field Name | Found In Datasets | Notes |
|------------|-------------------|-------|
| customer_id | [input_1], [staging], [output_1], [output_2] | Primary key |
| [field_name] | [dataset_list] | [notes] |
| [field_name] | [dataset_list] | [notes] |

### Field → Business Rule Map

> *Which fields are affected by business rules*

| Field Name | Business Rules Applied | Impact |
|------------|----------------------|--------|
| [field] | BR-001, BR-003 | [Brief description] |
| [field] | BR-002 | [Brief description] |

### Field Transformation Tracker

> *Track how fields change as they flow through the pipeline*

| Original Field | In Dataset | Becomes | In Dataset | Transformation |
|----------------|------------|---------|------------|----------------|
| [source_field] | [input] | [derived_field] | [intermediate] | [what happened] |
| [source_field] | [input] | [output_field] | [output] | [what happened] |

---

## Data Type Reference

### Standard Data Types Used

| Type | Description | Example |
|------|-------------|---------|
| String | Text values | "ABC123" |
| Integer | Whole numbers | 42 |
| Double | Decimal numbers | 3.14159 |
| Boolean | True/False | TRUE |
| Date | Calendar date | 2024-01-15 |
| Datetime | Date and time | 2024-01-15 10:30:00 |
| Array | List of values | ["A", "B", "C"] |

### Date/Time Formats

| Format | Example | Used In |
|--------|---------|---------|
| YYYY-MM-DD | 2024-01-15 | [datasets] |
| YYYY-MM-DD HH:MM:SS | 2024-01-15 10:30:00 | [datasets] |
| [custom format] | [example] | [datasets] |

---

## Appendix: Dataset Change History

### Recent Changes

| Date | Dataset | Change | Impact |
|------|---------|--------|--------|
| [date] | [dataset] | [field added/removed/modified] | [downstream effects] |

### Planned Changes

| Target Date | Dataset | Planned Change | Stakeholders Notified |
|-------------|---------|----------------|----------------------|
| [date] | [dataset] | [description] | [Yes/No] |
