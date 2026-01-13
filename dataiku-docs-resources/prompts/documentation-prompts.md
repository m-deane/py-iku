# Documentation Generation Prompts

Specific prompts for generating different types of Dataiku project documentation.

---

## Executive Summary Generation

### Prompt: `/doc-executive-summary`

```
Analyze this Dataiku project and generate a one-page Executive Summary for non-technical stakeholders.

Include:
1. **What This Project Does** - 2-3 sentences in plain business language
2. **Why It Matters** - Business value and decisions it enables
3. **Key Outputs** - Table of outputs with description, consumer, frequency
4. **Data Sources** - Table of inputs with business description
5. **Quick Facts** - Schedule, owner (role), status
6. **If Something Goes Wrong** - Simple escalation guidance

Requirements:
- Use plain language a business executive would understand
- Focus on business outcomes, not technical implementation
- Never include actual data values, credentials, or thresholds
- Use role titles, not personal names
- Keep to one page maximum
```

---

## Flow Documentation Generation

### Prompt: `/doc-flow-overview`

```
Analyze this Dataiku project and generate comprehensive flow documentation.

Generate THREE levels of visualization:

1. **Bird's Eye View** (ASCII)
   - Show: Inputs → Processing → Outputs
   - One box per major zone
   - 30-second comprehension target

2. **Zone-Based Flow** (Mermaid)
   - Group recipes/datasets by logical zone
   - Show data movement between zones
   - 2-minute comprehension target

3. **Flow Narrative**
   For each zone, document:
   - What This Section Does (plain language)
   - Why This Section Exists (business purpose)
   - How Data Flows Through (step table)
   - What Could Go Wrong (failure modes)
   - Who to Contact (roles)

Requirements:
- Non-technical language throughout
- Focus on business transformation, not technical operations
- Include record flow indicators (filter, join, aggregate)
- Never include actual data values or credentials
```

### Prompt: `/doc-lineage [field_name]`

```
Trace the lineage of field "[field_name]" from final output back to original sources.

Document:
1. **Trace Path** - Visual upstream trace with arrows
2. **Transformations** - Each modification in plain language
3. **Business Rules Applied** - Any BR-XXX rules affecting this field
4. **Source Dependencies** - Original fields that feed into this
5. **Impact of Changes** - What would break if source fields changed

Format as:
```
[final_output].[field_name]
  ↑ transformation: [description]
    ↑ source: [intermediate_dataset].[field]
      ↑ transformation: [description]
        ↑ source: [original_source].[field]
```

Requirements:
- Plain language descriptions
- Link to business rules where applicable
- Identify all upstream dependencies
```

---

## Recipe Documentation Generation

### Prompt: `/doc-recipe [recipe_name]`

```
Generate comprehensive documentation for recipe "[recipe_name]".

Include:
1. **Quick Facts Table** - Type, inputs, outputs, schedule
2. **What This Recipe Does** - 2-3 sentences, plain language
3. **Why This Recipe Exists** - Business justification
4. **Step-by-Step Explanation** - Table with Step, What Happens, Why
5. **Business Rules Applied** - List with BR-XXX references
6. **Data Flow Diagram** - ASCII showing inputs → recipe → outputs
7. **What Could Fail** - Table of symptoms, causes, resolutions
8. **Modification Guidance** - Prerequisites for making changes

Requirements:
- Every step explained in plain language
- Focus on WHAT and WHY, not HOW (no code)
- Link all business logic to cataloged rules
- Include troubleshooting for common failures
```

### Prompt: `/doc-all-recipes`

```
Generate documentation for ALL recipes in this project.

For each recipe, create a "Recipe Card" with:
- Quick facts (type, I/O, schedule)
- One-paragraph purpose description
- Key transformations list
- Business rules applied
- Failure modes

Then create:
- **Recipe Index** - Sortable table of all recipes
- **Recipe Dependency Map** - Which recipes depend on which
- **Recipe-to-Business-Rule Matrix** - Cross-reference

Format for easy searching and cross-referencing.
```

---

## Dataset Documentation Generation

### Prompt: `/doc-dataset [dataset_name]`

```
Generate comprehensive documentation for dataset "[dataset_name]".

Include:
1. **Quick Facts** - Type (I/O/intermediate), volume range, frequency, retention
2. **What This Dataset Contains** - Plain language description
3. **Why This Dataset Exists** - Business purpose
4. **Key Fields** - Table with field name, meaning, example use
5. **Data Quality Expectations** - What should be true about this data
6. **Upstream Dependencies** - What creates this dataset
7. **Downstream Usage** - What consumes this dataset
8. **Common Questions** - FAQ about this dataset

Requirements:
- Field descriptions in business terms
- Never include actual data values
- Include data quality indicators
- Link to producing/consuming recipes
```

### Prompt: `/doc-data-dictionary`

```
Generate a complete Data Dictionary for this project.

Include:
1. **Dataset Inventory** - All datasets with type and purpose
2. **Field Catalog** - All fields across all datasets with:
   - Field name
   - Dataset
   - Data type
   - Business meaning
   - Source (derived/direct)
   - Used by (downstream)

3. **Cross-Reference Tables**:
   - Field → Recipes that use it
   - Field → Business rules that apply
   - Field → Output reports containing it

Format for searchability - analysts should find any field in seconds.
```

---

## Business Rules Documentation

### Prompt: `/doc-rules-catalog`

```
Generate a complete Business Rules Catalog for this project.

For EVERY business decision/rule in the project, create an entry:

**BR-XXX: [Rule Name]**
- What This Rule Does (plain language)
- Why This Rule Exists (business justification)
- How It Works (simplified, no exact values)
- Example Scenario (illustrative case)
- Where Implemented (recipe, step)
- Who Owns (definition, implementation, approval)
- Related Rules (dependencies)

Create indexes:
1. **By Category** - Segmentation, filtering, calculation, etc.
2. **By Location** - Which rules in which recipes
3. **By Owner** - Which rules owned by which team

Include:
- Decision trees for complex branching rules
- Rule interaction diagrams where rules depend on each other
```

### Prompt: `/doc-decision-tree [process_name]`

```
Generate a decision tree diagram for "[process_name]".

Include:
1. **Visual Tree** (ASCII) - All decision points and outcomes
2. **Decision Points Table** - Question, field checked, possible paths
3. **Outcome Definitions** - What each endpoint means
4. **Implementation Locations** - Recipe/step for each decision
5. **Edge Cases** - What happens with unexpected inputs

Format the tree for easy following - a non-technical analyst should be
able to trace any record's path through the logic.
```

---

## Operations Documentation

### Prompt: `/doc-operations`

```
Generate complete operations documentation for this project.

Include:
1. **Scenario Documentation** - For each scenario:
   - What it does
   - When it runs (schedule/trigger)
   - What runs (ordered list)
   - How to know it worked
   - If it fails

2. **SLA & Expectations**:
   - Data freshness expectations
   - Acceptable delay thresholds
   - Maintenance windows
   - Calendar considerations

3. **Monitoring Guide**:
   - What to check daily
   - Warning signs to watch for
   - Health indicators

4. **Manual Operations**:
   - How to run manually
   - How to re-run failed jobs
   - How to run partial refreshes

Requirements:
- Step-by-step instructions
- Assume reader has basic Dataiku familiarity
- Include screenshots guidance (not actual screenshots)
```

---

## Troubleshooting Documentation

### Prompt: `/doc-troubleshoot`

```
Generate comprehensive troubleshooting documentation.

Create diagnostic decision trees for:
1. **Job Failures** - Error types and resolutions
2. **Data Quality Issues** - Wrong values, missing data, unexpected counts
3. **Performance Issues** - Slow runs, resource problems
4. **Access Issues** - Permission problems

For each issue type:
- Symptom identification
- Diagnostic steps
- Common causes with resolutions
- Escalation criteria

Include:
- "First 5 minutes" quick check guide
- Error message decoder (common errors → plain language)
- Contact matrix (issue type → who to contact)

Format as flowcharts where possible for easy navigation.
```

---

## Handover Documentation

### Prompt: `/doc-handover`

```
Generate a complete handover package for transferring ownership of this project.

Include:
1. **Executive Summary** - Business context and value
2. **Flow Overview** - How data moves through
3. **Operations Guide** - Day-to-day running
4. **Troubleshooting Guide** - Common issues
5. **Business Rules Reference** - All decision logic
6. **FAQ** - Questions new owners typically ask
7. **Handover Checklist** - Before/during/after transfer tasks
8. **30-Day Support Plan** - Structured support period

Also generate:
- Quick Reference Card (one-page cheat sheet)
- Contact Directory (roles and responsibilities)
- Known Issues & Quirks (tribal knowledge capture)
- Change History (what's changed recently)

Requirements:
- Assume recipient has no prior context
- Enable self-service for common operations
- Identify all sources of tribal knowledge
- Include "what I wish I knew" insights
```

---

## Self-Assessment Generation

### Prompt: `/doc-self-assessment`

```
Generate a self-assessment questionnaire for this project.

Create questions an analyst should be able to answer after reviewing documentation:

**Level 1: Basic Understanding**
- What does this project do?
- Who uses the outputs?
- When does it run?

**Level 2: Operational Competence**
- How do you check if today's run succeeded?
- What's the first thing to check if a job fails?
- Who do you contact for [issue type]?

**Level 3: Maintenance Capability**
- Where is business rule BR-XXX implemented?
- What would be affected if you changed [component]?
- How would you add a new field to the output?

Include answer key (or documentation references for answers).
```

---

## Full Documentation Generation

### Prompt: `/doc-all`

```
Generate complete documentation for this Dataiku project.

Create ALL of the following in a structured document:

1. Executive Summary (1 page)
2. Flow Overview with diagrams (2-5 pages)
3. Dataset Inventory with data dictionary
4. Recipe Documentation for all recipes
5. Business Rules Catalog
6. Operations Guide
7. Troubleshooting Playbook
8. Handover Package
9. FAQ
10. Glossary

Format with:
- Table of contents with links
- Consistent heading structure
- Cross-references between sections
- Search-friendly formatting

Security Requirements:
- No actual data values
- No credentials or connection details
- No proprietary algorithm specifics
- All thresholds use placeholders

Quality Requirements:
- Non-technical language for business sections
- Self-service enabled for common operations
- 30-second findability for any component
```
