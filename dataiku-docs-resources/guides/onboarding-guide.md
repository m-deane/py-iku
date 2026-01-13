# New Analyst Onboarding Guide

Welcome to your new Dataiku project! This guide will help you understand and take ownership of the project efficiently.

---

## Your First Hour

### Step 1: Understand the Business Context (15 minutes)

Before touching anything technical, answer these questions:

```
□ What business problem does this project solve?
□ Who are the consumers of the outputs?
□ What decisions does this data enable?
□ What would happen if this project stopped working?
```

**Find answers in**: Executive Summary document, or ask the current owner.

### Step 2: Get Oriented in Dataiku (15 minutes)

1. **Open the project** in Dataiku DSS
2. **View the Flow** - Click "Flow" in the left navigation
3. **Identify zones** - How is the project organized?
4. **Count components** - How many datasets? Recipes? Scenarios?

```
Quick inventory:
□ ____ Input datasets (data coming in)
□ ____ Output datasets (data going out)
□ ____ Intermediate datasets (data in process)
□ ____ Recipes (transformations)
□ ____ Scenarios (automated runs)
```

### Step 3: Trace a Complete Path (15 minutes)

Pick ONE output and trace it back to source:
1. Click on an output dataset
2. Look at "Lineage" or trace upstream
3. Follow the path back to the original input
4. Note each transformation along the way

```
Path traced:
[Output] ← [Recipe] ← [Dataset] ← [Recipe] ← ... ← [Input Source]
```

### Step 4: Check Current Status (15 minutes)

1. **Jobs**: Are recent jobs succeeding?
2. **Scenarios**: When did they last run?
3. **Data freshness**: When was data last updated?
4. **Alerts**: Any active issues?

---

## Your First Day

### Learn the Flow Structure

Use the Flow Overview documentation to understand:

```
□ How many distinct "zones" or sections exist?
□ What is the purpose of each zone?
□ Where does data enter the project?
□ Where does data exit the project?
□ What are the critical path recipes? (if one fails, everything fails)
```

### Understand Key Outputs

For EACH output dataset, document your understanding:

| Output | What It Contains | Who Uses It | When Refreshed |
|--------|------------------|-------------|----------------|
| | | | |
| | | | |
| | | | |

### Map Data Sources

For EACH input dataset:

| Source | What It Provides | Update Frequency | Owner |
|--------|------------------|------------------|-------|
| | | | |
| | | | |
| | | | |

### Review Scenarios

| Scenario | Purpose | Schedule | What It Runs |
|----------|---------|----------|--------------|
| | | | |
| | | | |

---

## Your First Week

### Day 2-3: Understand Business Rules

Review the Business Rules Catalog. For each rule:

```
□ Can I explain what this rule does in plain language?
□ Do I understand WHY this rule exists?
□ Can I find WHERE this rule is implemented?
□ Do I know WHO to ask if the rule needs to change?
```

### Day 3-4: Practice Operations

**With supervision**, practice these operations:

```
□ Check if the daily scenario ran successfully
□ View job logs for a completed job
□ Identify what failed in a failed job (use a past example)
□ Trigger a manual run of a scenario
□ Navigate to any recipe within 30 seconds
```

### Day 4-5: Understand Troubleshooting

Review the Troubleshooting Playbook. Ensure you can:

```
□ Diagnose the most common failure types
□ Know what to check first when something breaks
□ Understand the escalation path
□ Know when to fix yourself vs. when to ask for help
```

### End of Week: Self-Assessment

Complete the Self-Assessment Checklist. You should be able to:

```
□ Explain the project to a business stakeholder
□ Navigate to any component quickly
□ Check operational status
□ Diagnose simple failures
□ Know who to contact for different issue types
```

---

## Your First Month

### Week 2: Deepen Technical Understanding

```
□ Read through ALL recipe documentation
□ Understand each transformation in detail
□ Map field lineage for key output fields
□ Identify data quality rules and checks
```

### Week 3: Practice Changes (in Development)

With guidance, make practice changes:

```
□ Add a simple column rename
□ Modify a filter condition
□ Add a new output field
□ Update documentation for a change you made
```

### Week 4: Prepare for Independence

```
□ Shadow the current owner during incident response
□ Take primary responsibility for daily checks
□ Handle a simple change request end-to-end
□ Update documentation where gaps exist
```

---

## Essential Questions to Ask the Current Owner

### About the Business

1. "What business outcome depends on this project?"
2. "Who complains first when something breaks?"
3. "What's the most critical output and why?"
4. "Are there seasonal patterns I should know about?"
5. "What business changes might affect this project?"

### About the Technical Implementation

1. "What's the trickiest part of this project?"
2. "What breaks most often and why?"
3. "Are there any known issues or workarounds?"
4. "What would you do differently if rebuilding from scratch?"
5. "What did YOU wish you knew when you started?"

### About Operations

1. "What's your daily/weekly routine for this project?"
2. "How do you know everything is working?"
3. "What's the first thing you check when something fails?"
4. "Who do you call for different types of issues?"
5. "What's the worst thing that's happened and how was it fixed?"

### About Changes

1. "How often does this project change?"
2. "What kind of changes are requested most?"
3. "What's the process for making changes?"
4. "What changes are safe vs. risky?"
5. "Who needs to approve different types of changes?"

---

## Red Flags to Watch For

### During Onboarding

| Red Flag | What It Might Mean | Action |
|----------|-------------------|--------|
| No documentation exists | Knowledge only in people's heads | Document as you learn |
| "It's complicated" with no details | Possible technical debt | Request detailed walkthrough |
| Many manual steps required | Automation opportunity or risk | Document and evaluate |
| "Don't touch X" without reason | Unknown dependencies | Get details before proceeding |
| Frequent failures treated as normal | Quality issues | Escalate for improvement |

### Gaps to Note and Fill

```
□ Missing documentation for [_______________]
□ Undocumented business rule at [_______________]
□ No troubleshooting guide for [_______________]
□ Unclear ownership for [_______________]
□ No explanation for why [_______________]
```

---

## Building Your Reference Kit

Create your own quick reference with:

### Cheat Sheet (One Page)

```
PROJECT: [name]
PURPOSE: [one sentence]

KEY OUTPUTS:
- [output 1]: [what/who/when]
- [output 2]: [what/who/when]

DAILY CHECK:
1. [check 1]
2. [check 2]

IF SOMETHING BREAKS:
1. First check [___]
2. Then check [___]
3. Call [role] if [condition]

KEY CONTACTS:
- Data issues: [role]
- Business questions: [role]
- Infrastructure: [role]
```

### Personal Notes

Keep a learning log:
```
Date: _______
What I learned: ________________________________
Questions to follow up: ________________________
Documentation gap found: _______________________
```

---

## Checklist: Ready for Ownership

Before accepting full ownership, verify:

### Understanding
- [ ] Can explain project purpose to non-technical stakeholder
- [ ] Can describe data flow from source to output
- [ ] Know all business rules and where they're implemented
- [ ] Understand all scenarios and their purposes

### Operations
- [ ] Can perform daily health checks
- [ ] Can diagnose and resolve common failures
- [ ] Know escalation paths for different issues
- [ ] Can run manual jobs when needed

### Changes
- [ ] Have made at least one change successfully
- [ ] Understand impact analysis process
- [ ] Know approval requirements for changes
- [ ] Can update documentation

### Support
- [ ] Have all necessary access/permissions
- [ ] Have contact information for support resources
- [ ] Have agreed support period with previous owner
- [ ] Know where to find help documentation

---

## After Handover: First 90 Days

### Month 1: Stabilize
- Focus on understanding and operations
- Don't make changes unless necessary
- Document gaps you find

### Month 2: Improve
- Address documentation gaps
- Fix small issues
- Optimize monitoring

### Month 3: Own
- Make proactive improvements
- Share knowledge with team
- Become the expert others consult

---

## Resources Quick Links

| Need | Document |
|------|----------|
| Project overview | Executive Summary |
| How data flows | Flow Overview |
| What datasets contain | Data Dictionary |
| Business logic | Business Rules Catalog |
| Daily operations | Operations Guide |
| When things break | Troubleshooting Playbook |
| All terms defined | Glossary |
