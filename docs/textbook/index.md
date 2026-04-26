# Foreword

This is the textbook for py-iku, a library that converts pandas data-processing code into Dataiku DSS visual flows. The README tells you what the library does and how to install it. This book explains why the library is shaped the way it is, what choices it makes when the translation from pandas to DSS is ambiguous, and how to work with — and against — those choices in production.

## Who this book is for

The intended reader is a data engineer or analytics engineer who is already fluent in pandas, has heard of Dataiku DSS, and has either never built a flow by hand or has built one and found the manual configuration tedious. Familiarity with notebooks and command-line Python is assumed. Familiarity with DSS administration is not assumed; the book stops at the boundary of the produced flow and does not cover deployment, scheduling, or DSS server configuration.

The book is also useful to a platform engineer who has been asked to translate an existing pandas codebase into DSS as part of a migration. The chapters on filters, optimization, and the LLM path are especially relevant to that audience because they describe the exact decisions the library makes when the input has many predicates, long PREPARE chains, or non-standard idioms.

The book is not aimed at a reader who wants to learn pandas, learn DSS from scratch, or evaluate whether to adopt either tool. The decision to adopt has been made; the question is how to bridge them well.

## How to read it

The chapters have a directed dependency graph. The strongly recommended path on a first read is straight through Chapters 1 to 6, then Chapter 8, then 9 through 12. Chapter 7, the LLM path, is deliberately off the main spine: it describes an alternative analyzer, not a successor to the rule-based path. A reader who only cares about deterministic, offline conversion can skip Chapter 7 on a first read and come back to it later when LLM-based conversion becomes interesting. Chapter 11, on production usage, does cite the determinism contract that Chapter 7 establishes for the LLM path, so a reader who skips Chapter 7 should treat Chapter 11's LLM-CI sections as informational rather than prescriptive.

Each chapter begins with a `## What you'll learn` section naming the concrete capabilities that chapter delivers and ends with a `## What's next` pointer to the following chapter. Between them, every chapter has a `## Further reading` section with at least one link into `docs/api/` and at least one link to an exercising notebook under `notebooks/`. The book does not duplicate the API reference — when the API reference is the right place for a detail, the chapter links to it instead of restating it.

## What this book covers

- Chapter 1, *Why py-iku*. The gap between a pandas script and a DSS flow, and the three properties (lineage, partial re-execution, engine portability) that make a flow worth producing.
- Chapter 2, *The 5-Second Tour*. The shortest end-to-end example: V1 of the running example, one `convert()` call, and inspection of the resulting `DataikuFlow`.
- Chapter 3, *Anatomy of a Flow*. The four core model classes (`DataikuFlow`, `DataikuRecipe`, `DataikuDataset`, `PrepareStep`), the `FlowGraph` API, and round-trip serialization.
- Chapter 4, *pandas to DSS Grammar*. The decision rule that the rule-based analyzer uses to route pandas idioms to either recipes or processors, with a reference table of common cases.
- Chapter 5, *PREPARE Recipes Deep Dive*. The structure of a PREPARE recipe, step ordering, the six high-frequency processors, and the `ProcessorCatalog`.
- Chapter 6, *Recipe Types Tour*. The eight most common non-PREPARE recipe types — `GROUPING`, `JOIN`, `SORT`, `TOP_N`, `WINDOW`, `SPLIT`, `STACK`, `DISTINCT` — with one worked example each.
- Chapter 7, *The LLM Path*. When the LLM analyzer is appropriate, the determinism contract that makes it usable in CI, and the failure modes.
- Chapter 8, *Filters and Predicates*. Why DSS uses distinct processor types for distinct operator classes and how py-iku selects among them based on the AST.
- Chapter 9, *Advanced Patterns*. Multi-output split detection, GREL-formula generation, and how conditional logic in the source code becomes structure in the flow.
- Chapter 10, *Optimization and the DAG*. The PREPARE-merge optimization pass, fan-out guards, and how to inspect the post-optimization flow.
- Chapter 11, *Production Usage*. Wiring `convert()` into CI, configuration precedence, LLM cost monitoring, and version pinning for reproducibility.
- Chapter 12, *Extending py-iku*. The `PluginRegistry`, the three registration entry points, and a worked sklearn case study.
- Appendix A, *Glossary*. Concise definitions of the DSS and py-iku terms used throughout the book.
- Appendix B, *Troubleshooting*. The ten most common errors, each with symptom, cause, and fix.
- Appendix C, *Cheatsheet*. A one-page reference suitable for printing.

## What it doesn't cover

The book does not cover DSS administration, Dataiku Cloud setup, or DSS server tuning. It does not cover ML model training internals; Chapter 12 mentions `sklearn.preprocessing.StandardScaler` only as the canonical example of code that the core library deliberately does not handle, to motivate the plugin extension surface. It does not cover deploying the produced flow to a running DSS instance; the boundary of the textbook is the `DataikuFlow` object. Once that object exists, the public DSS API client (`dataiku-api-client-python`) is the right tool to push it into a project, and the textbook treats that step as out of scope.

The book also avoids speculation about DSS execution internals. When a chapter discusses why DSS has separate `FILTER_ON_VALUE` and `FILTER_ON_NUMERIC_RANGE` processors, the framing is "distinct processor types for distinct operator classes" — the choice py-iku has to make at the configuration layer. The book does not claim, for instance, that one processor uses a hash index and the other does not, because that is a runtime detail that is not part of the configuration surface and is not part of what py-iku produces.

## Conventions

The voice contract is in `STYLE.md` alongside the chapters. It is binding on every chapter and appendix. The rules of interest to readers are: every code block is runnable as written and uses the public API; every code block in chapters 2 onward references the running example schema fixed in `_running_example.md`; every factual claim about DSS or measured library behavior is cited inline. All code blocks in the textbook are exercised by `tests/test_textbook_examples.py`, so a reader who finds a code block that does not run should file a bug — that is a regression, not a documentation drift issue.

Cross-references use repo-rooted relative paths. A chapter linking to the API reference writes `../api/recipes.md`, not a fully qualified URL, so the same link resolves whether the reader is on the published docs site or browsing the markdown locally. Glossary entries in Appendix A are anchored, so a chapter can link directly to a single term: `appendix-a-glossary.md#topological-order`.
