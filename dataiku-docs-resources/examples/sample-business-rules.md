# Sample Business Rules Documentation

> **Note**: This is an example of completed business rule documentation to demonstrate proper documentation style.

---

# Customer Churn Prediction - Business Rules Catalog (Sample)

**Last Updated**: 2024-01-15
**Business Approver**: VP Customer Success

---

## Rules Index

| Rule ID | Rule Name | Category | Location |
|---------|-----------|----------|----------|
| BR-001 | Customer Activity Classification | Engagement | calculate_engagement, Step 4 |
| BR-002 | Risk Score Calculation | Scoring | compute_risk_score, Step 2 |
| BR-003 | Risk Tier Assignment | Segmentation | assign_risk_tier, Step 3 |
| BR-004 | Action Priority Assignment | Prioritization | create_action_list, Step 1 |

---

## BR-001: Customer Activity Classification

### Overview

| Property | Value |
|----------|-------|
| **Rule ID** | BR-001 |
| **Category** | Engagement |
| **Status** | Active |
| **Effective Date** | 2023-10-01 |
| **Last Reviewed** | 2024-01-01 |

### What This Rule Does

Classifies each customer into an engagement level (High, Medium, Low, Inactive) based on their recent activity patterns. This classification helps identify customers who may be disengaging before they reach a critical stage.

### Why This Rule Exists

Early identification of declining engagement allows proactive intervention. Customers don't typically churn overnight - they show warning signs through reduced activity first. This rule captures those warning signs systematically.

### Rule Logic (Simplified)

```
IF customer has engaged multiple times recently THEN "High Engagement"
ELSE IF customer has engaged at least once recently THEN "Medium Engagement"
ELSE IF customer has any engagement in extended period THEN "Low Engagement"
ELSE "Inactive"
```

**Note**: Specific thresholds for "multiple times", "recently", and "extended period" are configured by the Analytics team and reviewed quarterly.

### Example Scenarios

**Scenario 1: Active Customer**
> Sarah logs into the platform several times per week, makes regular purchases, and occasionally contacts support for product questions. She is classified as "High Engagement."

**Scenario 2: Declining Customer**
> Tom used to be very active but hasn't logged in for several weeks. He still has an active subscription. He is classified as "Low Engagement" - a warning sign.

**Scenario 3: Edge Case**
> A customer's engagement data is incomplete (they just joined). With insufficient history, they are excluded from classification until sufficient data accumulates.

### Input Requirements

| Field | Source | Required | Description |
|-------|--------|----------|-------------|
| last_login_date | CRM | Yes | Most recent platform login |
| interaction_count | Derived | Yes | Count of recent interactions |
| days_since_activity | Derived | Yes | Days since any activity |

### Output Produced

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| engagement_level | String | High, Medium, Low, Inactive | Customer's engagement classification |

### Where Implemented

- **Recipe**: calculate_engagement
- **Step**: 4 (Formula processor)
- **Technical Implementation**: Cascading IF formula in Prepare recipe

### Edge Cases & Exceptions

| Scenario | Handling |
|----------|----------|
| New customer (<30 days) | Excluded from classification, marked "New Customer" |
| Missing activity data | Defaults to "Unknown" for manual review |
| Multiple account holder | Uses aggregate of all linked accounts |

### Ownership

| Role | Responsibility |
|------|----------------|
| Business Owner | VP Customer Success - Defines engagement criteria |
| Technical Owner | Analytics Team - Implements and maintains |
| Change Approval | Analytics Director - Approves threshold changes |

### Related Rules

| Rule | Relationship |
|------|--------------|
| BR-002 | Engagement level is an input to Risk Score Calculation |
| BR-003 | Engagement level influences tier assignment |

### Testing / Validation

To verify this rule is working correctly:

1. Check distribution of engagement levels matches business expectations (~20% High, ~40% Medium, ~30% Low, ~10% Inactive)
2. Verify no null engagement_level values in output
3. Spot-check sample customers across each level

---

## BR-002: Risk Score Calculation

### Overview

| Property | Value |
|----------|-------|
| **Rule ID** | BR-002 |
| **Category** | Scoring |
| **Status** | Active |
| **Effective Date** | 2023-10-01 |
| **Last Reviewed** | 2024-01-01 |

### What This Rule Does

Calculates a composite risk score for each customer by combining multiple risk indicators into a single score. Higher scores indicate higher churn risk.

### Why This Rule Exists

Multiple factors contribute to churn risk. A composite score allows us to rank customers by overall risk rather than looking at each factor individually, enabling efficient prioritization of retention efforts.

### Rule Logic (Simplified)

```
Risk Score = Weighted combination of:
  - Engagement decline signals
  - Support sentiment indicators
  - Transaction pattern changes
  - Contract timing factors
```

**Note**: Weights are determined through analysis and reviewed quarterly. The model is calibrated to historical churn outcomes.

### Example Scenarios

**Scenario 1: High Risk**
> A customer's engagement has dropped significantly, they recently filed a complaint, and their contract renewal is approaching. Multiple risk factors combine to produce a high score.

**Scenario 2: Low Risk**
> A customer has steady engagement, positive support interactions, and recently renewed their contract. Few risk factors apply, resulting in a low score.

### Input Requirements

| Field | Source | Description |
|-------|--------|-------------|
| engagement_level | BR-001 | From engagement classification |
| engagement_trend | Derived | Direction of engagement change |
| support_sentiment | Support System | Sentiment from recent tickets |
| transaction_trend | Derived | Purchase pattern changes |
| contract_days_remaining | CRM | Days until contract end |

### Output Produced

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| risk_score | Decimal | 0-100 | Composite risk score |
| primary_risk_factor | String | Various | Highest contributing factor |

### Ownership

| Role | Responsibility |
|------|----------------|
| Business Owner | VP Customer Success |
| Technical Owner | Analytics Team |
| Model Validation | Data Science Team - Validates calibration quarterly |

---

## BR-003: Risk Tier Assignment

### Overview

| Property | Value |
|----------|-------|
| **Rule ID** | BR-003 |
| **Category** | Segmentation |
| **Status** | Active |

### What This Rule Does

Converts the numeric risk score into actionable risk tiers (Critical, High, Medium, Low) that determine what type of response is appropriate.

### Why This Rule Exists

Customer Success teams work with categories, not numbers. Risk tiers translate scores into clear action triggers and enable different response playbooks for each tier.

### Rule Logic (Simplified)

```
IF risk_score is very high THEN "Critical" → Immediate executive attention
ELSE IF risk_score is high THEN "High" → Proactive outreach within 24 hours
ELSE IF risk_score is elevated THEN "Medium" → Standard monitoring
ELSE "Low" → No immediate action required
```

### Decision Tree

```
                    ┌───────────────────┐
                    │ Customer Risk     │
                    │ Score Received    │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Score > [CRIT]?   │
                    └─────────┬─────────┘
                              │
               ┌──────────────┼──────────────┐
               │YES                          │NO
               ▼                             ▼
       ┌───────────────┐           ┌─────────────────┐
       │   CRITICAL    │           │ Score > [HIGH]? │
       │ Immediate     │           └────────┬────────┘
       │ escalation    │                    │
       └───────────────┘         ┌──────────┼──────────┐
                                 │YES                  │NO
                                 ▼                     ▼
                         ┌───────────────┐   ┌─────────────────┐
                         │     HIGH      │   │ Score > [MED]?  │
                         │ 24hr outreach │   └────────┬────────┘
                         └───────────────┘            │
                                            ┌─────────┼─────────┐
                                            │YES                │NO
                                            ▼                   ▼
                                    ┌───────────────┐   ┌───────────────┐
                                    │    MEDIUM     │   │      LOW      │
                                    │ Monitor       │   │ No action     │
                                    └───────────────┘   └───────────────┘
```

### Output Produced

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| risk_tier | String | Critical, High, Medium, Low | Action category |
| recommended_action | String | Various | Suggested response |

---

## BR-004: Action Priority Assignment

### Overview

| Property | Value |
|----------|-------|
| **Rule ID** | BR-004 |
| **Category** | Prioritization |
| **Status** | Active |

### What This Rule Does

Within each risk tier, assigns a priority rank based on customer value and other business factors, ensuring the most important customers receive attention first.

### Why This Rule Exists

Not all customers in the same risk tier are equal. A high-risk enterprise customer needs attention before a high-risk small customer. This rule applies business prioritization within tiers.

### Rule Logic (Simplified)

```
Priority within tier based on:
  1. Customer lifetime value (higher = higher priority)
  2. Contract value (higher = higher priority)
  3. Strategic account flag (strategic = higher priority)
  4. Time sensitivity (closer to decision point = higher priority)
```

### Output Produced

| Field | Type | Description |
|-------|------|-------------|
| action_priority | Integer | 1-N ranking within tier |
| priority_reason | String | Why this priority was assigned |

---

## Rule Change History

| Date | Rule ID | Change | Approved By |
|------|---------|--------|-------------|
| 2024-01-15 | BR-002 | Added web engagement signals | Analytics Director |
| 2023-12-01 | BR-003 | Adjusted tier thresholds | VP Customer Success |
| 2023-10-01 | ALL | Initial implementation | Executive Sponsor |
