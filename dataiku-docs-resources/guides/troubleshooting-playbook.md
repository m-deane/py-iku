# Troubleshooting Playbook

> **How to use this guide**: When something goes wrong, use this guide to diagnose and resolve issues systematically.

---

# [PROJECT_NAME] - Troubleshooting Playbook

**Last Updated**: [DATE]

---

## First 5 Minutes: Quick Diagnosis

```
╔════════════════════════════════════════════════════════════════╗
║                   QUICK DIAGNOSIS CHECKLIST                    ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  □ What failed? (scenario / recipe / dataset)                  ║
║  □ When did it fail? (this run / started recently / ongoing)   ║
║  □ What's the error message? (copy exact text)                 ║
║  □ Did anything change? (data / code / infrastructure)         ║
║  □ Is this affecting users? (severity assessment)              ║
║                                                                ║
║  QUICK CHECKS:                                                 ║
║  □ Is source data present and fresh?                           ║
║  □ Are upstream recipes successful?                            ║
║  □ Is this the first failure or recurring?                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Issue Categories

Jump to the relevant section:

1. [Job/Scenario Failures](#job-failures)
2. [Data Quality Issues](#data-quality-issues)
3. [Missing Data](#missing-data)
4. [Performance Issues](#performance-issues)
5. [Access/Permission Issues](#access-issues)
6. [Output Problems](#output-problems)

---

## Job Failures

### Diagnostic Tree

```
Job Failed
    │
    └── Check error message in job log
            │
    ┌───────┴───────┬───────────────┬───────────────┐
    │               │               │               │
    ▼               ▼               ▼               ▼
Connection      Schema          Resource        Code/Logic
Errors          Errors          Errors          Errors
    │               │               │               │
    ▼               ▼               ▼               ▼
[Jump A]        [Jump B]        [Jump C]        [Jump D]
```

### A: Connection Errors

**Common Messages:**
- "Connection refused"
- "Connection timed out"
- "Host not found"
- "Authentication failed"

**Diagnosis Steps:**

1. **Check source system status**
   - Is the source system running?
   - Is there scheduled maintenance?
   - Contact: [Source System Team/Contact]

2. **Check network connectivity**
   - Can other jobs reach the same system?
   - Is there a firewall issue?
   - Contact: [Infrastructure Team]

3. **Check credentials**
   - Have credentials expired?
   - Were credentials rotated?
   - Contact: [Security/Admin Team]

**Resolution:**
| Cause | Fix | Who |
|-------|-----|-----|
| Source system down | Wait for recovery, rerun | Self |
| Network issue | Escalate to infrastructure | [Team] |
| Credential expired | Request new credentials | [Team] |

---

### B: Schema Errors

**Common Messages:**
- "Column not found"
- "Schema mismatch"
- "Type mismatch"
- "Unknown field"

**Diagnosis Steps:**

1. **Identify the changed field**
   - Which column is mentioned in error?
   - Compare current schema to expected

2. **Determine if source changed**
   - Check source system for schema changes
   - Check if field was renamed/removed/added

3. **Assess impact**
   - Which recipes are affected?
   - Which outputs are impacted?

**Resolution:**
| Cause | Fix | Who |
|-------|-----|-----|
| Source added column | Usually harmless, verify | Self |
| Source removed column | Update recipe to handle | [Developer] |
| Source renamed column | Update recipe references | [Developer] |
| Source changed type | Update type handling | [Developer] |

---

### C: Resource Errors

**Common Messages:**
- "Out of memory"
- "Disk space full"
- "Execution timed out"
- "Resource limit exceeded"

**Diagnosis Steps:**

1. **Check resource usage**
   - Review job resource consumption
   - Compare to normal runs

2. **Check data volumes**
   - Is input data larger than usual?
   - Is there a data explosion (unexpected growth)?

3. **Check concurrent jobs**
   - Are other jobs consuming resources?
   - Is this a peak time?

**Resolution:**
| Cause | Fix | Who |
|-------|-----|-----|
| Data volume spike | Investigate source, optimize | [Developer] |
| Concurrent job contention | Reschedule or queue | Self |
| Need more resources | Request capacity increase | [Admin] |
| Inefficient code | Optimize recipe | [Developer] |

---

### D: Code/Logic Errors

**Common Messages:**
- "Division by zero"
- "Null pointer"
- "Invalid operation"
- "Formula error"

**Diagnosis Steps:**

1. **Locate the error**
   - Which recipe/step failed?
   - What was the input data?

2. **Check for edge cases**
   - Did unusual data trigger the error?
   - Is there a null/empty value causing issues?

3. **Review recent changes**
   - Was the recipe modified recently?
   - Did business rules change?

**Resolution:**
| Cause | Fix | Who |
|-------|-----|-----|
| Unexpected null values | Add null handling | [Developer] |
| Edge case in data | Add validation | [Developer] |
| Logic error | Debug and fix | [Developer] |
| Business rule conflict | Clarify with business | [Business Owner] |

---

## Data Quality Issues

### Diagnostic Tree

```
Data Looks Wrong
    │
    └── What's wrong?
            │
    ┌───────┴───────┬───────────────┬───────────────┐
    │               │               │               │
    ▼               ▼               ▼               ▼
Wrong           Duplicates      Unexpected      Wrong
Values                          Values          Format
    │               │               │               │
    ▼               ▼               ▼               ▼
[Jump E]        [Jump F]        [Jump G]        [Jump H]
```

### E: Wrong Values

**Symptoms:**
- Totals don't match expected
- Percentages seem off
- Values outside normal range

**Diagnosis Steps:**

1. **Verify source data**
   - Are source values correct?
   - Compare source to intermediate datasets

2. **Trace the transformation**
   - Where does the value change?
   - Which recipe introduced the issue?

3. **Check business rules**
   - Was a rule recently changed?
   - Is the rule being applied correctly?

**Investigation Path:**
```
Output Value: [X]
    ↑
Check recipe [name] - Is transformation correct?
    ↑
Check intermediate [dataset] - Is input value correct?
    ↑
Check source [dataset] - Is source value correct?
```

---

### F: Duplicate Records

**Symptoms:**
- Row counts higher than expected
- Same records appearing multiple times
- Aggregations are inflated

**Diagnosis Steps:**

1. **Identify duplication point**
   - Are duplicates in source?
   - Did a join create duplicates?

2. **Check join conditions**
   - Is the join key unique?
   - Are there many-to-many joins?

3. **Verify deduplication logic**
   - Is distinct/dedup step present?
   - Is it in the right place?

**Common Causes:**
| Cause | Location | Fix |
|-------|----------|-----|
| Source has duplicates | Input | Add dedup step early |
| Join key not unique | Join recipe | Review join conditions |
| Missing dedup step | Flow | Add distinct recipe |
| Reprocessed data | Source | Coordinate with source |

---

### G: Unexpected Values

**Symptoms:**
- New categories appearing
- Values outside expected range
- Unexpected nulls

**Diagnosis Steps:**

1. **Identify when it started**
   - Which run introduced new values?
   - What changed?

2. **Check source changes**
   - Did source system add new codes?
   - Did business rules change?

3. **Verify validation rules**
   - Are validations in place?
   - Are they filtering correctly?

---

### H: Wrong Format

**Symptoms:**
- Dates in wrong format
- Numbers appearing as text
- Encoding issues

**Diagnosis Steps:**

1. **Check source format**
   - Did source format change?
   - Is import reading correctly?

2. **Verify transformations**
   - Is type conversion applied?
   - Is date parsing configured correctly?

**Resolution:**
| Cause | Fix | Who |
|-------|-----|-----|
| Source format changed | Update import settings | [Developer] |
| Missing type conversion | Add conversion step | [Developer] |
| Encoding mismatch | Configure encoding | [Developer] |

---

## Missing Data

### Diagnostic Tree

```
Data is Missing
    │
    └── What's missing?
            │
    ┌───────┴───────┬───────────────┬───────────────┐
    │               │               │               │
    ▼               ▼               ▼               ▼
Entire          Specific        Recent          Specific
Dataset         Records         Data            Fields
Empty           Missing         Missing         Null
    │               │               │               │
    ▼               ▼               ▼               ▼
[Jump I]        [Jump J]        [Jump K]        [Jump L]
```

### I: Empty Dataset

**Diagnosis Steps:**

1. **Check if build ran**
   - Is the dataset built?
   - Did the job complete?

2. **Check upstream data**
   - Are input datasets populated?
   - Did upstream jobs succeed?

3. **Check filters**
   - Is a filter removing all records?
   - Are filter conditions too restrictive?

---

### J: Specific Records Missing

**Diagnosis Steps:**

1. **Are records in source?**
   - Verify records exist in source data
   - Check source data extraction timing

2. **Are records filtered out?**
   - Review filter conditions
   - Check business rule exclusions

3. **Did records fail validation?**
   - Check exception/error handling
   - Review data quality rules

**Investigation Query:**
> "For a specific record, trace through each step and identify where it disappears"

---

### K: Recent Data Missing

**Diagnosis Steps:**

1. **Check data freshness**
   - When was source data last updated?
   - Is there a delay in source?

2. **Check extraction timing**
   - Does extraction run after source updates?
   - Is there a timing gap?

3. **Verify date filters**
   - Are date filters configured correctly?
   - Is timezone causing issues?

---

### L: Specific Fields Null

**Diagnosis Steps:**

1. **Is field in source?**
   - Does source contain this field?
   - Is field populated in source?

2. **Is mapping correct?**
   - Is field being read correctly?
   - Is column mapping accurate?

3. **Is transformation clearing it?**
   - Does any step modify this field?
   - Is there conditional logic affecting it?

---

## Performance Issues

### Slow Job Execution

**Diagnosis Steps:**

1. **Compare to baseline**
   - How long does this normally take?
   - When did slowdown start?

2. **Identify bottleneck**
   - Which step is slowest?
   - What's consuming resources?

3. **Check data volume**
   - Has data size increased?
   - Is there data explosion?

**Common Causes:**
| Cause | Indicator | Fix |
|-------|-----------|-----|
| Data volume growth | Larger inputs | Optimize/partition |
| Join explosion | High memory use | Review join logic |
| Resource contention | Multiple slow jobs | Schedule differently |
| Infrastructure issue | All jobs slow | Escalate to admin |

---

## Access Issues

### Common Access Problems

| Error | Cause | Resolution |
|-------|-------|------------|
| "Permission denied" | Insufficient privileges | Request access from [admin] |
| "Dataset not visible" | Not granted access | Add to project/dataset permissions |
| "Cannot run scenario" | Missing execute permission | Request from project admin |
| "Cannot edit" | Read-only access | Request write access |

---

## Output Problems

### Consumer Reports Issue

**Symptom**: Consumer says data is wrong/missing

**Diagnosis Steps:**

1. **Verify output data**
   - Is output dataset correct in Dataiku?
   - Check directly in the project

2. **Check delivery**
   - Did export complete successfully?
   - Is file/table in expected location?

3. **Check consumer access**
   - Can consumer access the data?
   - Is there a caching issue?

---

## Escalation Guide

### When to Escalate

| Situation | Escalate To | Urgency |
|-----------|-------------|---------|
| Can't diagnose after 30 min | [Senior Analyst] | Normal |
| Infrastructure issue | [Platform Team] | Based on impact |
| Data breach concern | [Security Team] | Immediate |
| Business impact | [Business Owner] | Based on impact |

### How to Escalate

Include in escalation:
1. **Summary**: One sentence on what's wrong
2. **Impact**: Who/what is affected
3. **Timeline**: When it started, urgency
4. **Diagnosis**: What you've checked
5. **Ask**: What you need from them

---

## Error Message Decoder

| Error Contains | Usually Means | First Step |
|----------------|---------------|------------|
| "connection" | Network/DB connectivity | Check source system |
| "memory" | Resource exhaustion | Check data size |
| "permission" | Access rights | Verify credentials |
| "schema" | Data structure change | Compare schemas |
| "timeout" | Process too slow | Check performance |
| "null" | Missing data | Check data quality |
| "duplicate" | Unique constraint | Check for dupes |

---

## Post-Resolution Checklist

After fixing an issue:

- [ ] Verify fix resolved the issue
- [ ] Check downstream processes succeeded
- [ ] Notify affected stakeholders
- [ ] Document root cause and fix
- [ ] Consider preventive measures
- [ ] Update documentation if needed
