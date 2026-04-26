# py-iku Textbook — Chapter Outline

This file is the master outline. Phase 2 writer agents produce one markdown file per entry below, conforming to `STYLE.md`. The running-example contract lives in `_running_example.md`; chapters that use the running example must honor that schema and version progression.

The textbook is 12 chapters plus 3 appendices. The chapter dependency graph at the end of this file is authoritative for ordering and prerequisite assumptions.

---

## Chapter 1 — Why py-iku

**Filename**: `01-why-py-iku.md`

**What's covered**:
- The gap between an analyst's pandas script and a DSS visual flow that an enterprise can audit.
- Three concrete benefits of a flow over a script: lineage, reusability, and execution-engine portability.
- Where py-iku fits: source-to-flow, not flow-to-execution. The library produces DSS configuration; DSS executes it.
- A two-paragraph framing of the rule-based vs LLM-based modes and why both exist.

**What's NOT covered**:
- No code conversion examples — Ch 2 owns the first runnable example.
- No installation instructions — those live in the README.
- No DSS install or licensing — out of scope for the entire textbook.

**Assumed knowledge**: Working pandas; awareness that Dataiku DSS exists.

**Key code example(s)**: One small annotated diagram or pseudo-flow contrasting a 12-line pandas script with the equivalent DAG of recipes. No `convert()` calls in this chapter.

**Theory anchor**: A visual flow is not a transcription of a script; it is a different object with different properties (auditability, lineage, partial re-execution). Translation between the two is non-trivial and lossy in both directions.

**Citations needed**: At least one link to `doc.dataiku.com` describing the Flow as a first-class object. Optionally, one link to the DSS recipe overview page.

---

## Chapter 2 — The 5-Second Tour

**Filename**: `02-five-second-tour.md`

**What's covered**:
- The shortest possible end-to-end example: V1 of the running example (~5 lines of pandas) → `convert()` → inspect the resulting `DataikuFlow`.
- Reading the produced flow: how many recipes, what types, what dataset names.
- One round-trip: `flow.to_dict()` and `DataikuFlow.from_dict(...)` to demonstrate the model is data, not magic.
- A single visualization call (`flow.visualize(...)`) so the reader sees the DAG.

**What's NOT covered**:
- LLM mode (Ch 7).
- Anything beyond a single PREPARE recipe (Ch 3 onward).
- Customization or settings (Ch 5).

**Assumed knowledge**: Ch 1.

**Key code example(s)**:
- `running_example_v1.py` — the V1 pandas snippet from `_running_example.md`.
- One `convert()` call and one `flow.visualize()` call.

**Theory anchor**: The principle of a single deterministic pass: the rule-based path produces the same flow object every time for the same input, which is what makes it fit for CI.

**Citations needed**: One link to `py2dataiku/__init__.py` to anchor the public API surface (specifically `convert`).

---

## Chapter 3 — Anatomy of a Flow

**Filename**: `03-anatomy-of-a-flow.md`

**What's covered**:
- The four core model classes the reader will see repeatedly: `DataikuFlow`, `DataikuRecipe`, `DataikuDataset`, `PrepareStep`.
- The recipes-vs-processors distinction and why it matters operationally.
- The `FlowGraph` API: `flow.graph`, topological sort, cycle detection, subgraph discovery — what each is for.
- Round-trip serialization (`to_dict`/`from_dict`, `to_json`/`from_json`, `to_yaml`/`from_yaml`).

**What's NOT covered**:
- Specific recipe types beyond a brief enumeration (Ch 6).
- Specific processors beyond an enumeration (Ch 5).
- LLM internals (Ch 7).

**Assumed knowledge**: Ch 1, Ch 2.

**Key code example(s)**:
- Take the V1 flow from Ch 2, walk every attribute: `flow.recipes`, `flow.datasets`, `recipe.settings`, `recipe.steps`.
- Serialize and reload via JSON; assert structural equality.

**Theory anchor**: Recipes vs processors as the granularity of orchestration. A recipe is the unit DSS schedules and partitions; a processor is the unit it composes inside a single recipe's runtime. Choosing the right granularity is the central translation problem.

**Citations needed**: Link to `dataiku-api-client-python` for the recipe object model. Link to `doc.dataiku.com` Prepare recipe page for the processor concept.

---

## Chapter 4 — pandas-to-DSS Grammar

**Filename**: `04-pandas-to-dss-grammar.md`

**What's covered**:
- The translation problem stated cleanly: pandas is an imperative DSL over a single in-memory dataframe; DSS is a declarative DAG over named datasets.
- The decision rule the rule-based analyzer uses: structural ops (groupby, merge, concat, sort, top-n, window) become recipes; element-wise transforms (rename, fillna, type cast, round, abs, clip, simple filters) become processors.
- A reference table (~20 entries) of common pandas idioms and their py-iku targets, including the non-obvious cases listed in `CLAUDE.md`.
- One worked example showing the same pandas code producing different flow shapes depending on whether a step is structural or element-wise.

**What's NOT covered**:
- Per-recipe deep dives (Ch 5 for PREPARE, Ch 6 for the rest).
- Filter semantics (Ch 8).
- LLM analyzer behavior (Ch 7).

**Assumed knowledge**: Ch 1–3.

**Key code example(s)**:
- A pandas snippet using `df.merge`, `df.groupby`, `df.rename`, `df.fillna` — show the resulting recipe count and types.
- The reference table.

**Theory anchor**: Pandas as imperative DSL vs DSS as declarative DAG. The translation problem has no universally correct answer; the library chooses a convention (structural ops → recipes, element-wise → processors) and documents it.

**Citations needed**: Link to `mappings/pandas_mappings.py` (relative repo link) for the canonical mapping table source of truth.

---

## Chapter 5 — Prepare Recipes Deep Dive

**Filename**: `05-prepare-recipes-deep-dive.md`

**What's covered**:
- The structure of a PREPARE recipe: an ordered list of `PrepareStep` instances, each with a `ProcessorType` and a settings payload.
- Step ordering and why it matters: a `COLUMN_RENAMER` after a `FILL_EMPTY_WITH_VALUE` references different columns than before.
- Walkthrough of ~6 high-frequency processors: `COLUMN_RENAMER`, `FILL_EMPTY_WITH_VALUE`, `COLUMN_REMOVER`, `NUMERIC_TRANSFORM`, `STRING_TRANSFORMER`, `FILTER` (with forward-reference to Ch 8 for predicate detail).
- The `ProcessorCatalog` instance and how to discover the full 122-entry surface.
- Step merging: when py-iku's optimizer combines adjacent PREPARE recipes (with a forward-reference to Ch 10).

**What's NOT covered**:
- Filter predicate semantics (Ch 8).
- Recipes other than PREPARE (Ch 6).
- Optimizer internals beyond the merging mention (Ch 10).

**Assumed knowledge**: Ch 1–4.

**Key code example(s)**:
- The V1 running example, expanded to show 4–5 PrepareSteps in sequence.
- A `ProcessorCatalog().get_processor("COLUMN_RENAMER")` lookup.
- A two-block example showing why reordering two steps changes the output schema.

**Theory anchor**: Prepare-step composition and the order-of-operations rule. PREPARE is not a set of transforms; it is a sequence, and step N sees the schema produced by step N−1.

**Citations needed**: Link to `dataiku-api-client-python` for the PrepareStep class definition. Link to `doc.dataiku.com` for the prepare-recipe processor catalog page.

---

## Chapter 6 — Recipe Types Tour

**Filename**: `06-recipe-types-tour.md`

**What's covered**:
- A guided tour of the 8 most common non-PREPARE recipe types: `GROUPING`, `JOIN`, `SORT`, `TOP_N`, `WINDOW`, `SPLIT`, `STACK`, `DISTINCT`.
- For each: the pandas idiom that triggers it, the resulting `RecipeSettings` subclass, and a 5–10-line worked example.
- Forward-reference to running-example versions: V2 introduces JOIN, V3 introduces WINDOW, V4 introduces SORT, V5 introduces SPLIT.
- A short closer enumerating the remaining 29 recipe types by name with one-line summaries (no code).

**What's NOT covered**:
- PREPARE (Ch 5 owned that).
- SQL/Python recipes — out of scope for the rule-based path discussion.
- Filter predicate detail (Ch 8).

**Assumed knowledge**: Ch 1–5.

**Key code example(s)**:
- One worked example per recipe type from the tour, using running-example tables (`customers`, `orders`, `products`) wherever possible.
- The V2 jump (V1 + JOIN) shown as a concrete `convert()` diff.

**Theory anchor**: Recipe types as algebraic primitives over datasets. Each recipe type has a fixed input/output arity (1→1, 2→1, 1→N) and a fixed semantic; the visual flow is a composition of these primitives.

**Citations needed**: Link to `dataiku-api-client-python` `recipe.py` for the recipe-creator class hierarchy. Link to `doc.dataiku.com` recipe overview page.

---

## Chapter 7 — The LLM Path

**Filename**: `07-the-llm-path.md`

**What's covered**:
- When to use the LLM analyzer: code with conditional logic, ambiguous intent, or non-standard idioms the rule-based path misclassifies.
- The provider abstraction: Anthropic and OpenAI behind a single `LLMCodeAnalyzer` interface.
- Determinism: temperature=0, system-prompt construction, and structured output. Cite the controlled-experiment result rather than internal docs.
- Cost shape: a paragraph on token cost per conversion at typical input sizes.
- Failure modes: what `LLMResponseParseError` means and how the library degrades.

**What's NOT covered**:
- Provider-specific tuning beyond the public knobs.
- Rule-based analyzer internals (Ch 3, Ch 4 already covered).
- Production deployment (Ch 11).

**Assumed knowledge**: Ch 1–4.

**Key code example(s)**:
- The same V2 running example run through `convert(..., llm="anthropic")` and through the rule-based path; show the flows are structurally identical.
- A code snippet that the rule-based path misclassifies and the LLM path gets right.

**Theory anchor**: LLM-as-translator. With temperature=0 and a fixed system prompt, structured-output conversion is deterministic over the prompt+input pair. This is what makes it usable in CI.

**Citations needed**: One Anthropic API doc link for the structured-output / temperature=0 contract. Cite the measured determinism result inline ("3/3 identical runs at temperature=0 across the 18-recipe corpus") without linking the internal plan file.

---

## Chapter 8 — Filters and Predicates

**Filename**: `08-filters-and-predicates.md`

**What's covered**:
- The framing: DSS provides distinct processor types for distinct operator classes (string equality, numeric comparison, range, regex, set membership). py-iku selects among them based on the predicate's operator and operand types.
- Walkthrough of the predicate detection logic: how `df[df["col"] == "x"]` becomes `FILTER_ON_VALUE` while `df[df["col"] > 100]` becomes `FILTER_ON_NUMERICAL_RANGE`.
- The `matchingMode` parameter of `FilterOnValue` and how py-iku populates it. Cite `dataiku-api-client-python`.
- Multi-clause predicates: how AND/OR combinations decompose into either a single multi-clause filter or a chain of simpler ones.
- The complementary-filter detection that powers SPLIT recipes (forward-reference to Ch 9).

**What's NOT covered**:
- DSS execution internals (no claims about hash indexes, B-trees, range scans, or query planning — those are outside the verified evidence).
- Custom user-defined predicates (Ch 12).

**Assumed knowledge**: Ch 1–5.

**Key code example(s)**:
- Four predicates showing four different processor selections: `==` string, `>` numeric, `.isin([...])`, `.str.contains(...)`.
- One multi-clause AND example and one OR example.

**Theory anchor**: Distinct processor types for distinct operator classes. DSS does not conflate string-match and numeric-comparison at the configuration layer; py-iku's job is to route each predicate to the correct processor type based on the AST.

**Citations needed**: Link to `dataiku-api-client-python` source for `FilterOnValue` and its `matchingMode` field. Link to `doc.dataiku.com` for the filter-processor catalog entries.

---

## Chapter 9 — Advanced Patterns

**Filename**: `09-advanced-patterns.md`

**What's covered**:
- Multi-output split: when one input dataset becomes two outputs via complementary filters; how py-iku detects the complementarity and emits a single SPLIT recipe instead of two FILTER recipes.
- GREL formula generation: when an element-wise pandas expression cannot be expressed by a stock processor and gets compiled to a `FORMULA` processor with GREL.
- Conditional logic in the source: how if/else branches become either disjoint flow paths or formula-driven processors.
- Pattern: collapsing a chain of `df.assign(...)` into a single PREPARE recipe with N steps.

**What's NOT covered**:
- DAG-level optimization (Ch 10).
- Custom processor handlers (Ch 12).

**Assumed knowledge**: Ch 1–8 (especially Ch 8 for predicate detection).

**Key code example(s)**:
- V5 of the running example, which adds a SPLIT — show the SPLIT detection trace.
- A GREL-formula example: `df["full_name"] = df["first"] + " " + df["last"]` → `FORMULA` step with the emitted GREL string.

**Theory anchor**: The library makes specific structural inferences from local syntactic patterns (complementary predicates, expression trees that lack a stock processor). Each inference is a small theorem with a specific antecedent; surfacing the antecedents is what makes the tool predictable.

**Citations needed**: Link to `doc.dataiku.com` for GREL syntax. Link to `mappings/pandas_mappings.py` for the FORMULA fallback.

---

## Chapter 10 — Optimization and the DAG

**Filename**: `10-optimization-and-dag.md`

**What's covered**:
- `BaseFlowGenerator._optimize_flow` and `_merge_prepare_recipes`: what they do and when they run.
- The DAG-aware merging rule: adjacent PREPARE recipes on a single edge merge; PREPARE recipes feeding a fan-out do not.
- Fan-out guards: why merging a PREPARE that feeds two downstream recipes would change semantics.
- Inspecting the post-optimization flow: counting recipes before and after, asserting the merge happened.
- Cost-of-optimization: the optimization pass is O(V+E) over the flow graph, runs once per `convert()` call.

**What's NOT covered**:
- Production deployment (Ch 11).
- LLM analyzer internals (Ch 7).

**Assumed knowledge**: Ch 3 (FlowGraph), Ch 5 (PREPARE structure).

**Key code example(s)**:
- A pandas script that produces three sequential PREPARE recipes pre-optimization and one post-optimization. Show the recipe count drop.
- A pandas script with a fan-out where the PREPARE *cannot* be merged. Show the recipe count is preserved.

**Theory anchor**: DAG-aware merging respects semantic equivalence. Two adjacent PREPARE recipes on a linear path are equivalent to one combined PREPARE; the same is not true across a fan-out, because downstream consumers may differ in what they need from the intermediate dataset.

**Citations needed**: Link to `BaseFlowGenerator` in the repo for the optimization implementation.

---

## Chapter 11 — Production Usage

**Filename**: `11-production-usage.md`

**What's covered**:
- Wiring `convert()` into CI: a GitHub Actions snippet that runs conversion on every PR and asserts the flow shape.
- `Py2DataikuConfig`: toml/yaml/rc files, environment variables, `.env.local`, and where each takes precedence.
- LLM cost monitoring: capturing token counts via the provider response and logging per-conversion cost.
- Failure handling: catching `ConversionError`, `LLMResponseParseError`, and `ValidationError` separately because they signal different fixes.
- Versioning and reproducibility: pinning `py-iku` version and the LLM model name in CI.

**What's NOT covered**:
- DSS deployment of the produced flow — out of scope; this textbook stops at the flow object.
- Plugin extension (Ch 12).

**Assumed knowledge**: Ch 1–7.

**Key code example(s)**:
- A `pytest` test that calls `convert()` and asserts `len(flow.recipes) == 3` and the recipe types in topological order.
- A minimal `Py2DataikuConfig` toml file plus a Python snippet that loads it.
- A GitHub Actions YAML snippet (in a code block, not a real file) running the test.

**Theory anchor**: The tooling is only useful in production if its output is asserted-against. CI integration relies on the determinism property established in Ch 2 (rule-based) and Ch 7 (LLM with temperature=0).

**Citations needed**: Link to `Py2DataikuConfig` source. Link to GitHub Actions docs for the `pytest` step convention.

---

## Chapter 12 — Extending py-iku

**Filename**: `12-extending-py-iku.md`

**What's covered**:
- `PluginRegistry` and the global convenience functions (`register_recipe_handler`, etc.). Class-based design with backward-compatible shorthand.
- Writing a custom recipe handler: the function signature, what it returns, where it plugs in.
- Writing a custom processor handler that emits a `FORMULA` step for a domain-specific function.
- The single sklearn case study allowed in the textbook: handling `sklearn.preprocessing.StandardScaler` by emitting either a PREPARE chain or a Python recipe, and the trade-offs.
- Discoverability: how to introspect the registered handlers at runtime.

**What's NOT covered**:
- Modifying core enums (`RecipeType`, `ProcessorType`) — that is a contributor concern, not an extension concern.

**Assumed knowledge**: Ch 1–10.

**Key code example(s)**:
- A 20-line custom processor handler registered via `register_recipe_handler(...)`.
- A short sklearn `StandardScaler` example that hits the custom handler.
- A `PluginRegistry()` introspection snippet listing registered handlers.

**Theory anchor**: Extension via plugin registry rather than core modification. The library's authoring surface is small (~5 public functions); the extension surface is where domain logic goes.

**Citations needed**: Link to `py2dataiku/plugins/` source. Link to scikit-learn docs for `StandardScaler` (one citation, used only in this chapter).

---

## Appendix A — Glossary

**Filename**: `appendix-a-glossary.md`

**Scope**: ~40–60 entries, alphabetical, one or two sentences each. Covers DSS terminology (recipe, flow, dataset, processor, partition, GREL), py-iku internals (FlowGraph, PrepareStep, RecipeSettings, ProcessorCatalog, PluginRegistry), and library-specific exceptions. Each entry pointing to a chapter where appropriate.

**Length**: 500–1200 words.

**Citations needed**: At least one link to `doc.dataiku.com` glossary if it exists; otherwise per-term links as appropriate.

---

## Appendix B — Troubleshooting

**Filename**: `appendix-b-troubleshooting.md`

**Scope**: ~10–15 symptom→diagnosis→fix entries. Examples: "convert() raises InvalidPythonCodeError"; "LLM path returns a flow with the wrong recipe type"; "round-trip JSON fails to reproduce the original flow"; "PREPARE recipes did not merge as expected"; "FilterOnValue.matchingMode is wrong".

**Length**: 500–1200 words.

**Citations needed**: Each entry pointing to the relevant chapter and source file.

---

## Appendix C — Cheatsheet

**Filename**: `appendix-c-cheatsheet.md`

**Scope**: Mostly tables. The pandas → recipe/processor mapping table from Ch 4 in expanded form, plus a one-page quick reference of `convert()` signatures, the `RecipeType` and top-level `ProcessorType` enums, and the most common `flow.*` accessors.

**Length**: 500–800 words. Tables do not count toward the limit, but the prose around them should not exceed 800 words.

**Citations needed**: One link to `mappings/pandas_mappings.py` and one to `models/dataiku_recipe.py`.

---

## Chapter dependency graph

The graph is authoritative. A chapter may assume material from any of its ancestors and must not assume material from its descendants.

- Ch 1 (Why)
  - Ch 2 (5-second tour)
    - Ch 3 (Anatomy)
      - Ch 4 (Grammar)
        - Ch 5 (PREPARE deep dive)
          - Ch 6 (Recipe types tour)
            - Ch 8 (Filters and predicates)
              - Ch 9 (Advanced patterns)
                - Ch 10 (Optimization and DAG)
                  - Ch 11 (Production usage)
                    - Ch 12 (Extending py-iku)
        - Ch 7 (LLM path) — depends on Ch 4, parallel to Ch 5–6
- Appendix A (Glossary) — depends on all chapters
- Appendix B (Troubleshooting) — depends on all chapters
- Appendix C (Cheatsheet) — depends on Ch 4, Ch 5, Ch 6

Notes:
- Ch 7 is intentionally placed off the main spine because the LLM path is an alternative to, not a successor of, the rule-based path. A reader who only cares about the rule-based path can skip Ch 7 and follow Ch 6 → Ch 8 directly.
- Ch 11 depends on Ch 7 because production deployment of the LLM path requires the determinism contract Ch 7 establishes.
- Ch 12 depends on Ch 10 because plugin handlers interact with the optimizer's merging rules.
