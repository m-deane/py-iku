# Dataset Documentation Template

> **How to use this template**: Create one document per dataset, or compile multiple datasets into a single document with one section per dataset.

---

## Dataset: [DATASET_NAME]

### Quick Facts

| Property | Value |
|----------|-------|
| **Dataset Name** | [dataset_name] |
| **Full Path** | [project_key].[dataset_name] |
| **Type** | [Input / Intermediate / Output] |
| **Storage** | [Files / SQL / Managed / etc.] |
| **Update Frequency** | [How often data changes] |
| **Typical Volume** | [Row count range] |
| **Retention** | [How long data is kept] |

---

### What This Dataset Contains

> *Describe in plain language what data this dataset holds. A non-technical person should understand.*

[2-3 sentences describing what this data represents]

**Example:**
> This dataset contains one record per active customer, with their profile information, contact details, and summary metrics about their engagement with our products. It is updated daily with the latest customer information.

---

### Why This Dataset Exists

> *Business purpose and usage*

**Used For:**
- [Primary use case]
- [Secondary use case]

**Consumed By:**
- [Consumer 1]: [How they use it]
- [Consumer 2]: [How they use it]

---

### Data Lineage

```
UPSTREAM                    THIS DATASET                DOWNSTREAM
─────────                   ────────────                ──────────

[source_dataset_1] ─┐
                    ├──► [DATASET_NAME] ──┬──► [downstream_1]
[source_dataset_2] ─┘                     │
                                          └──► [downstream_2]
```

**Created By:** [recipe_name] ([recipe_type])

**Used By:**
- [recipe_name_1] - for [purpose]
- [recipe_name_2] - for [purpose]

---

### Field Definitions

#### Core Fields

| # | Field Name | Type | Description | Example | Required | Source |
|---|------------|------|-------------|---------|----------|--------|
| 1 | [field_name] | [String/Integer/Date/etc.] | [What this field represents] | [Example value] | Yes/No | [Origin] |
| 2 | [field_name] | [type] | [description] | [example] | Yes/No | [source] |
| 3 | [field_name] | [type] | [description] | [example] | Yes/No | [source] |

#### Derived/Calculated Fields

| # | Field Name | Type | Description | Calculation | Business Rule |
|---|------------|------|-------------|-------------|---------------|
| 1 | [field_name] | [type] | [what it represents] | [how calculated] | [BR-XXX] |
| 2 | [field_name] | [type] | [what it represents] | [how calculated] | [BR-XXX] |

#### Category/Code Fields

| Field Name | Possible Values | Value Descriptions |
|------------|-----------------|-------------------|
| [category_field] | Value A | [What Value A means] |
| | Value B | [What Value B means] |
| | Value C | [What Value C means] |

---

### Data Quality

#### Expected Quality Rules

| Rule | Field(s) | Condition | Severity |
|------|----------|-----------|----------|
| Completeness | [field] | Should not be null | High |
| Uniqueness | [field] | Should be unique | High |
| Range | [field] | Should be between [min] and [max] | Medium |
| Format | [field] | Should match [pattern] | Low |

#### Quality Metrics

| Metric | Expected | Alert Threshold |
|--------|----------|-----------------|
| Row count | [typical range] | < [min] or > [max] |
| Null rate for [key_field] | < [%] | > [threshold]% |
| Duplicate rate | 0 | > 0 |

---

### Access & Security

| Property | Value |
|----------|-------|
| **Classification** | [Public / Internal / Confidential / Restricted] |
| **Contains PII** | [Yes/No - if yes, which fields] |
| **Access Required** | [Role/permission needed] |
| **Restricted Fields** | [Fields with limited access] |

---

### Refresh & Timing

| Property | Value |
|----------|-------|
| **Update Trigger** | [Schedule / Upstream completion / Manual] |
| **Update Frequency** | [Daily / Hourly / Real-time / etc.] |
| **Typical Update Time** | [When update usually completes] |
| **Data As Of** | [How current is the data] |

**Timeline:**
```
[Source System] ────► [This Dataset] ────► [Consumers]
    Updates at           Updated at          Available at
    [time]               [time]              [time]
```

---

### Common Questions

**Q: Why might this dataset be empty?**
A: [Explanation - e.g., "Source data hasn't arrived yet", "Filter conditions removed all records"]

**Q: Why might records be missing?**
A: [Explanation of what filters or conditions might exclude records]

**Q: Why might a field be null?**
A: [Explanation by field - when nulls are expected vs. problematic]

**Q: How current is this data?**
A: [Explanation of data latency]

**Q: Can I add new fields to this dataset?**
A: [Process for requesting changes]

---

### Known Issues & Quirks

| Issue | Description | Workaround |
|-------|-------------|------------|
| [issue_1] | [what the issue is] | [how to handle it] |
| [issue_2] | [what the issue is] | [how to handle it] |

---

### Related Datasets

| Dataset | Relationship | Common Key |
|---------|--------------|------------|
| [related_dataset_1] | [Parent / Child / Sibling] | [join_field] |
| [related_dataset_2] | [relationship] | [join_field] |

---

### Sample Schema (Structure Only)

```
[DATASET_NAME]
├── [field_1]: [type] (PK) - [brief description]
├── [field_2]: [type] - [brief description]
├── [field_3]: [type] - [brief description]
├── [field_4]: [type] - [brief description]
└── [field_5]: [type] - [brief description]
```

---

### For Input Datasets Only

#### Source System

| Property | Value |
|----------|-------|
| **Source System** | [System name] |
| **Source Owner** | [Team/Role] |
| **Extraction Method** | [API / File transfer / DB query / etc.] |
| **Source Contact** | [Who to contact for source issues] |

#### Source to Dataset Mapping

| Source Field | Dataset Field | Transformation |
|--------------|---------------|----------------|
| [source_field] | [dataset_field] | [None / Renamed / Parsed / etc.] |

---

### For Output Datasets Only

#### Consumer Information

| Consumer | Contact | How They Use It | SLA |
|----------|---------|-----------------|-----|
| [consumer_1] | [contact] | [usage] | [requirement] |
| [consumer_2] | [contact] | [usage] | [requirement] |

#### Delivery Information

| Property | Value |
|----------|-------|
| **Delivery Method** | [Export / API / Direct access / etc.] |
| **Delivery Location** | [Where output goes] |
| **Format** | [CSV / Parquet / Database table / etc.] |
| **Notification** | [Who is notified when ready] |

---

### Change History

| Date | Change | Impact | Made By |
|------|--------|--------|---------|
| [date] | [what changed] | [downstream impact] | [role] |
