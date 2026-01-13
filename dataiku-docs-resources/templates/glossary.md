# Glossary Template

> **How to use this template**: Document all terms, acronyms, and concepts used in your project. This helps non-technical stakeholders understand documentation and outputs.

---

# [PROJECT_NAME] - Glossary of Terms

**Last Updated**: [DATE]

---

## Quick Navigation

- [Business Terms](#business-terms)
- [Technical Terms](#technical-terms)
- [Data Fields](#data-fields)
- [Status Codes & Categories](#status-codes--categories)
- [Acronyms](#acronyms)
- [Dataiku-Specific Terms](#dataiku-specific-terms)

---

## Business Terms

> *Terms specific to your business domain*

| Term | Definition | Context/Usage |
|------|------------|---------------|
| [Term 1] | [Plain language definition] | [Where/how this term is used] |
| [Term 2] | [Plain language definition] | [Where/how this term is used] |
| [Term 3] | [Plain language definition] | [Where/how this term is used] |

### Example Business Terms

| Term | Definition | Context/Usage |
|------|------------|---------------|
| Customer Lifetime Value (CLV) | Total predicted revenue from a customer over their entire relationship with us | Used in segmentation and prioritization |
| Churn | When a customer stops doing business with us | Churn prediction models, retention campaigns |
| Active Customer | A customer who has made a purchase within [timeframe] | Defines who is included in customer counts |
| Segment | A group of customers with similar characteristics | Marketing targeting, reporting breakdown |

---

## Technical Terms

> *Technical concepts explained in plain language*

| Term | Definition | Why It Matters |
|------|------------|----------------|
| [Term 1] | [Plain language definition] | [Business relevance] |
| [Term 2] | [Plain language definition] | [Business relevance] |

### Example Technical Terms

| Term | Definition | Why It Matters |
|------|------------|----------------|
| ETL | Extract, Transform, Load - the process of moving and preparing data | This is what our data pipeline does |
| Join | Combining two datasets by matching records on a common field | How we connect customer info to transaction info |
| Aggregation | Summarizing many records into fewer (e.g., summing daily sales into monthly) | How we create summary reports |
| Filter | Removing records that don't meet certain criteria | How we focus on relevant data only |
| Schema | The structure of a dataset - what columns exist and their types | When schema changes, our processes may need updates |

---

## Data Fields

> *Key fields in outputs and what they mean*

### Output: [Output Dataset 1 Name]

| Field Name | Business Meaning | Possible Values | Notes |
|------------|------------------|-----------------|-------|
| [field_1] | [What this represents] | [Value range/examples] | [Any important context] |
| [field_2] | [What this represents] | [Value range/examples] | [Any important context] |
| [field_3] | [What this represents] | [Value range/examples] | [Any important context] |

### Output: [Output Dataset 2 Name]

| Field Name | Business Meaning | Possible Values | Notes |
|------------|------------------|-----------------|-------|
| [field_1] | [What this represents] | [Value range/examples] | [Any important context] |
| [field_2] | [What this represents] | [Value range/examples] | [Any important context] |

---

## Status Codes & Categories

> *Codes and categories used in outputs and what they mean*

### [Category Type 1: e.g., Customer Segments]

| Code/Value | Meaning | Description |
|------------|---------|-------------|
| [Code A] | [Label] | [Detailed description of what this means] |
| [Code B] | [Label] | [Detailed description of what this means] |
| [Code C] | [Label] | [Detailed description of what this means] |

### [Category Type 2: e.g., Order Status]

| Code/Value | Meaning | Description |
|------------|---------|-------------|
| [Status 1] | [Label] | [What this status indicates] |
| [Status 2] | [Label] | [What this status indicates] |

### [Category Type 3: e.g., Risk Levels]

| Code/Value | Meaning | Action Required |
|------------|---------|-----------------|
| [Level 1] | [Label] | [What to do when you see this] |
| [Level 2] | [Label] | [What to do when you see this] |
| [Level 3] | [Label] | [What to do when you see this] |

---

## Acronyms

> *Abbreviations used in the project*

| Acronym | Full Form | Definition |
|---------|-----------|------------|
| [ABC] | [A Big Concept] | [What it means] |
| [XYZ] | [Xyz Your Z] | [What it means] |

### Common Acronyms You Might See

| Acronym | Full Form | Definition |
|---------|-----------|------------|
| API | Application Programming Interface | A way for systems to talk to each other |
| CSV | Comma-Separated Values | A simple file format for data (like Excel but simpler) |
| ETL | Extract, Transform, Load | The process of moving and preparing data |
| SQL | Structured Query Language | A language for working with databases |
| KPI | Key Performance Indicator | Important business metrics we track |
| SLA | Service Level Agreement | Promised delivery times or quality levels |
| UAT | User Acceptance Testing | Testing by business users before go-live |

---

## Dataiku-Specific Terms

> *Dataiku platform terminology*

| Term | Definition | In Plain Language |
|------|------------|-------------------|
| Dataset | A table of data within Dataiku | Like a spreadsheet or database table |
| Recipe | A set of instructions that transforms data | A step in our data pipeline |
| Flow | The visual representation of how data moves through recipes | The "map" of our data pipeline |
| Scenario | An automated sequence of tasks | A scheduled job that runs our pipeline |
| Zone | A logical grouping of datasets and recipes | A section of our pipeline with related steps |
| Job | A single execution of a recipe or scenario | One run of our process |
| Prepare Recipe | A visual recipe for data transformation | Cleaning and transforming data without code |
| Join Recipe | A recipe that combines datasets | Connecting different tables together |
| Build | Running a recipe to create/update its output | Refreshing the data |

---

## Calculation Definitions

> *How key metrics are calculated (without revealing exact formulas)*

### [Metric 1 Name]

**What it measures**: [Plain language description]

**Calculated from**: [Input fields/sources]

**Interpretation**:
- Higher values mean [interpretation]
- Lower values mean [interpretation]
- Typical range: [general range]

### [Metric 2 Name]

**What it measures**: [Plain language description]

**Calculated from**: [Input fields/sources]

**Interpretation**:
- [How to interpret this metric]

---

## Common Misunderstandings

> *Clarifications for frequently confused terms*

### "[Term A]" vs "[Term B]"

| | [Term A] | [Term B] |
|---|----------|----------|
| **Means** | [definition] | [definition] |
| **Used for** | [use case] | [use case] |
| **Example** | [example] | [example] |

### "[Term C]" is NOT the same as "[Term D]"

[Explanation of why these are different and when each applies]

---

## How to Add New Terms

When you encounter a term that should be in this glossary:

1. **Identify the term** that needs definition
2. **Determine the category** (Business, Technical, Data Field, etc.)
3. **Write a plain language definition** avoiding jargon
4. **Add context** about where/how the term is used
5. **Update this document** and note the date

---

## Version History

| Date | Changes | Author |
|------|---------|--------|
| [Date] | Initial creation | [Role] |
| [Date] | Added [terms] | [Role] |
