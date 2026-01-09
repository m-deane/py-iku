# Dataiku Project Documentation Resources

A comprehensive toolkit for documenting Dataiku DSS projects in a way that enables non-technical analysts to understand, own, and maintain data pipelines.

## Purpose

This resource collection helps you create documentation that answers the question:

> "If I inherit this project tomorrow with no prior context, what do I need to confidently operate and modify it?"

## Who This Is For

| Audience | What They Need | Start Here |
|----------|----------------|------------|
| **New Analyst** | Understanding the project from scratch | [Onboarding Guide](guides/onboarding-guide.md) |
| **Project Owner** | Day-to-day operations and maintenance | [Operations Guide](guides/operations-guide.md) |
| **Business Stakeholder** | Understanding outputs and value | [Executive Summary Template](templates/executive-summary.md) |
| **Technical Handover** | Complete technical transfer | [Handover Checklist](checklists/handover-checklist.md) |

## Resource Map

```
dataiku-docs-resources/
│
├── prompts/                     # AI assistant prompts
│   ├── cursor-rules.md          # Complete Cursor/AI rules file
│   ├── documentation-prompts.md # Specific documentation generation prompts
│   └── security-guidelines.md   # IP/data protection requirements
│
├── templates/                   # Fill-in-the-blank templates
│   ├── executive-summary.md     # Business-focused project overview
│   ├── flow-documentation.md    # Pipeline flow documentation
│   ├── recipe-documentation.md  # Individual recipe documentation
│   ├── dataset-documentation.md # Dataset inventory template
│   ├── business-rules-catalog.md # Business logic registry
│   ├── data-dictionary.md       # Field-level documentation
│   └── glossary.md              # Terms and definitions
│
├── guides/                      # How-to guides
│   ├── onboarding-guide.md      # New analyst orientation
│   ├── operations-guide.md      # Day-to-day maintenance
│   ├── visual-vocabulary.md     # Dataiku icons and symbols explained
│   ├── troubleshooting-playbook.md # Problem diagnosis guide
│   └── change-management.md     # How to request and make changes
│
├── checklists/                  # Verification checklists
│   ├── handover-checklist.md    # Complete ownership transfer
│   ├── self-assessment.md       # "Do I understand this project?"
│   ├── documentation-review.md  # Quality check for documentation
│   └── go-live-checklist.md     # Pre-production verification
│
└── examples/                    # Filled-out examples
    ├── sample-executive-summary.md
    ├── sample-flow-documentation.md
    └── sample-business-rules.md
```

## Quick Start

### For AI-Assisted Documentation

1. Copy `prompts/cursor-rules.md` into your project's `.cursorrules` file
2. Use the documentation commands (e.g., `/doc-handover-complete`)
3. AI will generate documentation following security and clarity guidelines

### For Manual Documentation

1. Start with `templates/executive-summary.md` for business context
2. Use `templates/flow-documentation.md` for each pipeline section
3. Complete `templates/business-rules-catalog.md` for all decision logic
4. Verify with `checklists/documentation-review.md`

## Documentation Principles

### 1. Layer Information (Pyramid Structure)

```
            ┌─────────────┐
            │  EXECUTIVE  │  ← 1 page: What & Why
            │   SUMMARY   │
            ├─────────────┤
            │    FLOW     │  ← 2-5 pages: How it works
            │  OVERVIEW   │
            ├─────────────┤
            │   RECIPE    │  ← Detailed: Each component
            │   DETAILS   │
            ├─────────────┤
            │  REFERENCE  │  ← Appendix: Glossary, dictionary
            │  MATERIALS  │
            └─────────────┘
```

### 2. Answer the Five Questions

Every piece of documentation should help answer:

| Question | Documentation Section |
|----------|----------------------|
| **WHAT** does this do? | Executive Summary, Flow Overview |
| **WHY** does it exist? | Business Purpose, Value Statement |
| **HOW** does it work? | Flow Documentation, Recipe Details |
| **WHO** is responsible? | Stakeholder Map, Contact Directory |
| **WHEN** does it run? | Scenarios, Schedules, SLAs |

### 3. Protect Sensitive Information

Never document:
- Actual data values or samples
- Credentials, API keys, connection strings
- Proprietary algorithm parameters
- Customer/client identifiable information
- Exact business thresholds (use "[CONFIGURED_VALUE]")

See `prompts/security-guidelines.md` for complete requirements.

### 4. Enable Self-Service

Good documentation lets analysts:
- Find any component in under 30 seconds
- Trace any output back to its source
- Diagnose common issues without escalation
- Make routine changes confidently

## Documentation Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION WORKFLOW                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. DISCOVER                 2. DOCUMENT                          │
│  ┌─────────────────┐        ┌─────────────────┐                  │
│  │ Explore project │───────▶│ Fill templates  │                  │
│  │ Interview owners│        │ Generate diagrams│                  │
│  │ Trace data flows│        │ Catalog rules   │                  │
│  └─────────────────┘        └────────┬────────┘                  │
│                                      │                            │
│  4. MAINTAIN                 3. VALIDATE                          │
│  ┌─────────────────┐        ┌────────▼────────┐                  │
│  │ Update on change│◀───────│ Review checklist│                  │
│  │ Version control │        │ Analyst walkthru│                  │
│  │ Periodic review │        │ Security audit  │                  │
│  └─────────────────┘        └─────────────────┘                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Success Metrics

Your documentation is effective when:

- [ ] A new analyst can explain the project's purpose after 15 minutes of reading
- [ ] An analyst can locate any recipe or dataset within 30 seconds
- [ ] Common issues can be resolved using documentation alone
- [ ] Business stakeholders can understand what outputs mean
- [ ] Changes can be made without tribal knowledge
- [ ] No sensitive information is exposed

## Contributing

When adding new templates or guides:

1. Follow the existing naming conventions
2. Include a "How to Use This Template" section
3. Provide at least one filled-out example
4. Update this README's resource map
5. Test with a non-technical reviewer

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | [DATE] | Initial release with core templates and guides |
