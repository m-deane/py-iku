# Security & Confidentiality Guidelines for Dataiku Documentation

This document defines what must NEVER be included in project documentation to protect business IP, proprietary data, and confidential information.

## Classification Framework

### PROHIBITED - Never Document

| Category | What It Includes | Risk If Exposed |
|----------|------------------|-----------------|
| **Credentials** | Passwords, API keys, tokens, certificates, SSH keys | Unauthorized system access |
| **Connection Strings** | Database URLs, server addresses, ports, hostnames | Infrastructure targeting |
| **Data Values** | Actual records, sample data, data previews | Privacy breach, competitive intel |
| **Exact Counts** | Row counts, user counts, transaction volumes | Business intelligence exposure |
| **Algorithm Details** | Model weights, coefficients, exact formulas | Intellectual property theft |
| **Business Thresholds** | Exact cutoff values, scoring boundaries | Competitive advantage loss |
| **PII** | Names, emails, phone numbers, addresses, IDs | Privacy regulation violation |
| **Internal Infrastructure** | Server names, IP addresses, internal URLs | Security vulnerability |

### RESTRICTED - Document with Redaction

| Category | How to Document | Example |
|----------|-----------------|---------|
| **Threshold Concepts** | Describe purpose, not value | "Filters high-value customers" not "revenue > $50k" |
| **Data Scale** | Use ranges or qualitative terms | "Substantial volume" not "2.3M records" |
| **Business Logic** | Describe intent, not implementation | "Applies risk criteria" not "score < 0.15" |
| **System Names** | Use functional descriptions | "[CRM_SYSTEM]" not "salesforce-prod-1" |

### PERMITTED - Safe to Document

| Category | Examples |
|----------|----------|
| **Flow Structure** | Recipe types, dependencies, execution order |
| **Field Purposes** | What a column represents (not actual values) |
| **Business Context** | Why the project exists, who uses outputs |
| **Process Descriptions** | What transformations occur (not how exactly) |
| **Operational Procedures** | How to run, monitor, troubleshoot |
| **Contact Roles** | Job titles, not personal names |

---

## Redaction Standards

### Standard Placeholders

```markdown
# Credentials & Access
[CREDENTIALS]
[SERVICE_ACCOUNT]
[API_KEY]
[AUTH_TOKEN]

# Infrastructure
[SERVER_NAME]
[DATABASE_HOST]
[INTERNAL_URL]
[PRODUCTION_CLUSTER]

# Connections
[CONNECTION_NAME]
[SALESFORCE_PROD]
[DATA_WAREHOUSE]

# Values
[THRESHOLD_VALUE]
[CONFIGURED_VALUE]
[BUSINESS_RULE_PARAMETER]

# Scale
[SUBSTANTIAL_VOLUME]
[SIGNIFICANT_COUNT]
[APPROXIMATE_RANGE]

# Timing
[BUSINESS_HOURS]
[SLA_WINDOW]
```

### Redaction Examples

#### Database Connections

**PROHIBITED:**
```
postgresql://admin:p@ssw0rd123@prod-analytics.company.internal:5432/customers
```

**CORRECT:**
```
Connects to [PRODUCTION_DATABASE] using [SERVICE_ACCOUNT] credentials
```

#### Business Rules

**PROHIBITED:**
```sql
WHERE customer_ltv > 50000
  AND churn_score < 0.15
  AND segment IN ('ENTERPRISE', 'STRATEGIC')
```

**CORRECT:**
```markdown
Filters to high-value customers (LTV above threshold) with elevated churn
risk (score above threshold) in priority segments (Enterprise, Strategic)
```

#### Data Statistics

**PROHIBITED:**
```
Processes 2,347,891 customer records daily
Filters remove approximately 12.3% of records
Output contains 156 columns
```

**CORRECT:**
```
Processes customer records daily from [CRM_SOURCE]
Filters remove records not meeting quality criteria
Output contains customer attributes needed for analysis
```

#### Algorithm Parameters

**PROHIBITED:**
```python
weights = {'recency': 0.35, 'frequency': 0.25, 'monetary': 0.40}
decay_rate = 0.95
score_cap = 1000
```

**CORRECT:**
```markdown
Customer value is calculated using a weighted combination of:
- Recency of engagement
- Frequency of interaction
- Monetary contribution

Weights and parameters are configured by the Analytics team and
reviewed quarterly.
```

---

## Data Handling Rules

### Sample Data

**Never include actual data in documentation:**

**PROHIBITED:**
```
| customer_id | name | revenue |
|-------------|------|---------|
| C-10042 | Acme Corp | $125,000 |
| C-10043 | Beta Inc | $89,500 |
```

**CORRECT:**
```
| Field | Type | Description |
|-------|------|-------------|
| customer_id | String | Unique customer identifier |
| name | String | Customer account name |
| revenue | Decimal | Total revenue in reporting period |
```

### Screenshots

If screenshots are necessary:
1. Blur or redact any visible data values
2. Remove or obscure credentials/URLs in browser bars
3. Replace actual names with "[SAMPLE]" or similar
4. Crop to show only relevant UI elements

### Logs & Error Messages

**PROHIBITED:**
```
Error connecting to prod-db-master.company.internal:5432
User john.smith@company.com authentication failed
Processing customer record ID: 1000234567
```

**CORRECT:**
```
Error connecting to [DATABASE_SERVER]
User [SERVICE_ACCOUNT] authentication failed
Processing customer record
```

---

## Verification Checklist

Before finalizing any documentation, verify:

### Credential Check
- [ ] No passwords visible
- [ ] No API keys or tokens
- [ ] No connection strings with credentials
- [ ] No certificate contents

### Infrastructure Check
- [ ] No internal server names
- [ ] No IP addresses
- [ ] No internal URLs
- [ ] No port numbers (unless generic like 443)

### Data Check
- [ ] No actual data values
- [ ] No sample records
- [ ] No exact row counts
- [ ] No customer/user identifiable information

### Business Logic Check
- [ ] No exact threshold values
- [ ] No proprietary formula details
- [ ] No model parameters
- [ ] No competitive intelligence

### Personnel Check
- [ ] No personal names (use roles)
- [ ] No personal email addresses
- [ ] No personal phone numbers
- [ ] No employee IDs

---

## Compliance Considerations

### GDPR/Privacy Regulations
- Never document data that could identify individuals
- Describe data categories, not specific data
- Reference data retention policies without specifics

### SOX/Financial Controls
- Document process existence, not specific values
- Reference controls without exposing thresholds
- Describe audit trails conceptually

### Industry-Specific (HIPAA, PCI, etc.)
- Follow industry-specific documentation guidelines
- When in doubt, redact
- Consult compliance team for sensitive projects

---

## Exception Process

If documentation absolutely requires sensitive information:

1. **Justify**: Document why the information is essential
2. **Minimize**: Include only what's absolutely necessary
3. **Protect**: Use appropriate access controls
4. **Mark**: Clearly label as "CONFIDENTIAL - RESTRICTED ACCESS"
5. **Review**: Get approval from Security/Compliance team
6. **Audit**: Track who accesses the documentation

---

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════╗
║              DOCUMENTATION SECURITY QUICK CHECK               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  STOP! Before saving, check for:                              ║
║                                                               ║
║  □ Passwords/credentials    → Replace with [CREDENTIALS]      ║
║  □ Server names/IPs         → Replace with [SERVER_NAME]      ║
║  □ Actual data values       → Remove or describe generally    ║
║  □ Exact counts             → Use "substantial" or ranges     ║
║  □ Exact thresholds         → Use [THRESHOLD_VALUE]           ║
║  □ Personal names           → Use job titles/roles            ║
║  □ Algorithm specifics      → Describe purpose, not method    ║
║                                                               ║
║  When in doubt, redact it.                                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```
