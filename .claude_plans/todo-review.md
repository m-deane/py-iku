# TODO Review: Success Criteria & Use Case Alignment

**Date:** 2026-02-23
**Library Version:** 0.3.0
**Test Suite:** 1693 tests (all passing)

---

## Overview

This document reviews TODO items 2-6 (item 1 is done) against the original use case: *converting Python data processing code (pandas, numpy, scikit-learn) into Dataiku DSS visual recipes, flows, and configurations, eliminating the manual effort of rebuilding Python pipelines in Dataiku's visual recipe UI.*

---

## TODO Item 2: Test Example Notebooks

### a) Current State Assessment

**What exists:**
- 5 Jupyter notebooks in `notebooks/examples/`:
  - `01_beginner.ipynb` -- 32 code cells, 59 total cells
  - `02_intermediate.ipynb` -- 55 code cells, 89 total cells
  - `03_advanced.ipynb` -- 40 code cells, 51 total cells
  - `04_expert.ipynb` -- 54 code cells, 69 total cells
  - `05_master.ipynb` -- 44 code cells, 63 total cells
- **Total: 225 code cells across 5 notebooks**
- No test file for notebooks exists (grep for "notebook" or "ipynb" in `tests/` returned zero results)
- No CI configuration for notebook execution
- Notebooks use `sys.path.insert(0, "../..")` for imports (notebooks 02-05)
- Notebook 01 does not use sys.path (relies on installed package)
- All notebooks import from `py2dataiku` -- they depend on the library being either installed or on the path

**What's working:**
- Notebooks cover the full feature surface: basic conversion, all recipe types, visualizations, processors, DAG analysis, optimization, LLM analysis, DSS export, configuration, plugins, scenarios, metrics, MLOps, exceptions
- Each notebook has clear markdown documentation between code cells
- Progressive difficulty (beginner through master) is well-structured

**What's missing:**
- No automated testing of any kind -- notebooks have never been validated by a test runner
- No `conftest.py` or test harness for notebook execution
- No record of which cells pass/fail

### b) Success Criteria

| Criterion | Metric | Verification Method |
|-----------|--------|---------------------|
| All code cells execute without exception | 225/225 code cells produce no ImportError, AttributeError, NameError, TypeError, or other unhandled exception | Run each notebook via `nbclient` or pytest-notebook and capture cell-level pass/fail |
| Test file exists and runs in CI | `tests/test_py2dataiku/test_notebooks.py` exists with passing tests | `python -m pytest tests/test_py2dataiku/test_notebooks.py -v` passes |
| Failures are documented or fixed | Any cells that legitimately require external resources (API keys, file I/O) are either mocked or marked as expected-skip | Review test output for skip annotations |
| Notebook tests are part of the main test suite | Test count increases by the number of notebook test cases | `python -m pytest tests/ --co -q` shows notebook tests |

### c) Link to Use Case

- **How it serves the mission:** Notebooks are the primary learning tool for users adopting py-iku. If notebooks contain broken code, users will lose confidence in the library and abandon adoption. Data scientists who prototype in Python (the target users) are heavy notebook users.
- **Pain point addressed:** Users trying the library for the first time encounter errors in example code, wasting time debugging the library instead of converting their pipelines.
- **Impact if NOT completed:** Untested notebooks may silently break with future library changes, creating a poor first impression. The 5 notebooks collectively demonstrate every major feature -- broken examples mean broken documentation.

### d) Scope & Deliverables

**Files to create:**
- `tests/test_py2dataiku/test_notebooks.py` -- pytest-based notebook cell execution tests

**Files to modify:**
- Any notebook cells that fail during testing (fix the code)
- `pyproject.toml` -- add `nbclient` or `nbformat` to dev dependencies if not present

**Approach:**
1. Use `nbformat` + `nbclient` to execute each notebook programmatically
2. Each notebook becomes one test function (or one test class with parametrized cells)
3. Cells requiring external resources (LLM API keys) should be handled via MockProvider or skipped
4. IPython display calls (`display(SVG(...))`) need IPython to be available or should be guarded

**In scope:** Automated execution of all 225 code cells, fixing any failures, adding to test suite
**Out of scope:** Testing notebook rendering in Jupyter UI, testing that visualizations look correct visually

### e) Dependencies & Risks

- **Dependencies:** None (item 1 is done, notebooks exist)
- **Risks:**
  - Cells using `IPython.display` will fail outside Jupyter -- need `try/except` guards or mock
  - Notebook 01 assumes package is installed; others use `sys.path` hack -- testing approach must handle both
  - Some cells in 04_expert create MockProvider with specific response JSON -- these should work but need validation
- **Open questions:** Should notebook tests be slow-tests (separate marker) or part of the default test run?

### f) Priority & Effort Estimate

- **Priority:** 1 (highest) -- untested examples are a liability
- **Effort:** M (medium) -- writing the test harness is straightforward; fixing broken cells may take time depending on how many fail

---

## TODO Item 3: Add More Visualizations and Flow Diagrams to Notebooks

### a) Current State Assessment

**Visualization format coverage per notebook:**

| Notebook | SVG | ASCII | HTML | Mermaid | PlantUML | Interactive | `_repr_svg_()` | Theme comparison |
|----------|-----|-------|------|---------|----------|-------------|----------------|------------------|
| 01_beginner | No | Yes | No | Yes | No | No | No | No |
| 02_intermediate | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes (light/dark/custom) |
| 03_advanced | No | No | No | No | No | No | No | No |
| 04_expert | No | Yes | No | No | No | No | No | No |
| 05_master | Yes (inline) | Yes | No | No | No | No | No | No |

**Assessment:**
- Notebook 02 has excellent visualization coverage (all 6 formats + themes + `_repr_svg_()`)
- Notebook 03 (Advanced) has **zero** visualizations despite covering processors, DAG analysis, and flow optimization -- these are ideal candidates for visual output
- Notebooks 04 and 05 are light on visualizations despite covering complex flows (DSS export, production pipelines)
- No notebook shows visual before/after optimization comparison
- No notebook shows DAG graph visualization (FlowGraph is discussed in 03 but never visualized)
- No notebook demonstrates `flow.to_png()` or `flow.to_pdf()` (require cairosvg)

**What's working:**
- The visualization infrastructure is comprehensive (6 formats + themes + Jupyter integration)
- Notebook 02 serves as a strong template for visualization coverage

**What's missing:**
- Visual output in notebooks 03, 04, 05
- Before/after optimization diagrams
- DAG layout visualizations
- Theme comparison in advanced notebooks

### b) Success Criteria

| Criterion | Metric | Verification Method |
|-----------|--------|---------------------|
| Every notebook has at least 3 visualization formats | Each of 01-05 uses 3+ of: SVG, ASCII, HTML, Mermaid, PlantUML, Interactive | Manual audit of notebook cells |
| Advanced+ notebooks (03-05) show visual before/after optimization | At least 2 optimization visual comparisons across notebooks | Cell content review |
| DAG analysis includes visual output | FlowGraph topological order and structure are visualized, not just printed | Cell content review |
| Visualization cells produce output | All viz cells execute without error (covered by TODO item 2) | Notebook test suite |

**Specific targets per notebook:**

| Notebook | Current viz formats | Target viz formats |
|----------|--------------------|--------------------|
| 01_beginner | ASCII, Mermaid (2) | ASCII, Mermaid, SVG (3+) |
| 02_intermediate | All 6 + themes | No changes needed |
| 03_advanced | 0 | ASCII, SVG, Mermaid (3+) + before/after optimization diagrams |
| 04_expert | ASCII only (1) | ASCII, SVG, Mermaid (3+) + rule-based vs LLM flow comparison |
| 05_master | ASCII, SVG (2) | ASCII, SVG, Mermaid (3+) + production flow with zones |

### c) Link to Use Case

- **How it serves the mission:** py-iku's primary output is visual -- flow diagrams are how users verify that the conversion is correct. If notebooks don't show visual output, users cannot learn how to verify their conversions.
- **Pain point addressed:** Users converting their Python pipelines need to visually inspect the generated Dataiku flow to confirm correctness before importing into DSS. Visualization examples teach them how to do this.
- **Impact if NOT completed:** Users won't discover the full visualization capabilities, may not realize they can generate SVG/HTML/Mermaid output for documentation, and miss the visual validation step that's critical for production use.

### d) Scope & Deliverables

**Files to modify:**
- `notebooks/examples/01_beginner.ipynb` -- add 1-2 SVG visualization cells
- `notebooks/examples/03_advanced.ipynb` -- add 4-6 visualization cells (processor results, optimization before/after, DAG graph)
- `notebooks/examples/04_expert.ipynb` -- add 3-4 visualization cells (LLM flow diagrams, DSS export flow, rule vs LLM comparison)
- `notebooks/examples/05_master.ipynb` -- add 3-4 visualization cells (production flow in multiple formats, zone-colored diagrams)

**Specific visualizations to add:**

1. **03_advanced:**
   - ASCII visualization of the Prepare recipe pipeline from Section 3
   - SVG visualization of the FlowGraph from Section 4
   - Mermaid diagram of the before-optimization flow
   - SVG diagram of the after-optimization flow (side-by-side comparison)
   - ASCII of the validated flow from Section 6

2. **04_expert:**
   - SVG of the rule-based flow (Section 6)
   - SVG of the LLM-based flow (Section 6) for visual comparison
   - Mermaid of the end-to-end workflow (Section 13)

3. **05_master:**
   - Mermaid diagram of the production fraud detection flow
   - SVG with zones highlighted
   - ASCII of ETL pipeline from Section 7.1

**In scope:** Adding visualization cells to existing notebooks
**Out of scope:** Creating new notebooks, changing narrative structure, adding PNG/PDF export (requires cairosvg)

### e) Dependencies & Risks

- **Dependencies:** Should be done after TODO item 2 (test notebooks) so we can verify the new cells work
- **Risks:**
  - SVG inline display requires IPython -- cells need `from IPython.display import SVG, display` guards
  - Large flows may produce large SVG output that clutters the notebook -- may need to truncate or use ASCII for very large flows
- **Open questions:** None

### f) Priority & Effort Estimate

- **Priority:** 3 -- important for user experience but not blocking
- **Effort:** S (small) -- adding cells to existing notebooks with known API calls

---

## TODO Item 4: Update Docs

### a) Current State Assessment

**MkDocs site structure (`docs/`):**
- `index.md` -- Landing page
- `getting-started/installation.md` -- Installation guide
- `getting-started/quickstart.md` -- Quick start guide
- `api/` -- 15 API reference pages (core-functions, py2dataiku-class, models, enums, llm-providers, visualizers, exporters, plugins, configuration, exceptions, graph, recipe-settings, scenarios-metrics, mlops)
- `reference/index.md` -- Auto-generated API reference (mkdocstrings)
- `mkdocs.yml` -- Site configuration with Material theme

**What's working:**
- Site structure is comprehensive with 15 API reference pages
- Auto-generated API reference via mkdocstrings
- Material theme with light/dark mode toggle
- Code copy buttons, tabs, search
- Installation and quick start are accurate for v0.3.0
- Mermaid diagram rendering support is configured

**What's missing or outdated:**

| Issue | Location | Status |
|-------|----------|--------|
| No link to example notebooks | `docs/index.md`, `docs/getting-started/quickstart.md` | Missing |
| No notebooks section in nav | `mkdocs.yml` | Missing |
| `docs/index.md` claims "5 visualization formats" | Line 49 | Should say 6 (SVG, HTML, ASCII, Mermaid, PlantUML, Interactive) |
| Quick start references `convert_file_with_llm` | `quickstart.md` line 115 | Feature exists; correct |
| Column lineage quick start section shows basic usage | `quickstart.md` line 142 | `get_column_lineage` now requires `dataset` parameter -- may be outdated |
| API reference for configuration shows TOML format | `quickstart.md` line 166 | Format shown may not match actual config parser |
| No Changelog or Release Notes page | `docs/` | Missing |
| `Py2Dataiku` class documentation doesn't mention `convert_file`/`convert_file_with_llm` | `api/py2dataiku-class.md` | Incomplete |
| No "Examples" or "Tutorials" section in docs | `mkdocs.yml` nav | Missing -- notebooks would fill this gap |
| Auto-generated API reference depth | `reference/index.md` | Need to verify all public symbols are documented |

**Cross-reference with `__init__.py` public API (82 exports):**
The API reference pages should cover all 82 exports. Key areas to verify:
- Recipe Settings (12 subclasses) -- has its own page
- Scenarios & Metrics -- has its own page
- MLOps -- has its own page
- All enums (25+) -- has its own page

### b) Success Criteria

| Criterion | Metric | Verification Method |
|-----------|--------|---------------------|
| Notebooks linked from docs | At least one nav entry pointing to notebooks | Check `mkdocs.yml` nav |
| Visualization format count is correct | Docs say "6 visualization formats" | Grep docs for format claims |
| All 82 public API exports are documented | Each symbol in `__all__` appears in at least one docs page | Cross-reference script |
| Column lineage docs match implementation | Quick start example for `get_column_lineage()` works with current API | Run the example |
| No broken internal links | `mkdocs build --strict` passes | Build command |
| Version references are v0.3.0 | No references to v0.1.0 or v0.2.0 | Grep docs for version strings |

### c) Link to Use Case

- **How it serves the mission:** Documentation is how users discover and learn py-iku. Inaccurate docs waste user time. Missing notebook links means users may never find the examples.
- **Pain point addressed:** Users who find discrepancies between docs and actual behavior lose trust. Users who cannot find examples spend more time figuring out the API.
- **Impact if NOT completed:** Documentation drift will accelerate as the library evolves. New features (scenarios, metrics, MLOps, config system, column lineage) added in v0.3.0 may not be discoverable.

### d) Scope & Deliverables

**Files to modify:**

1. `mkdocs.yml`:
   - Add "Examples" or "Notebooks" nav section linking to notebooks
   - Consider adding notebooks as downloadable assets or linking to GitHub

2. `docs/index.md`:
   - Fix visualization format count (5 -> 6, include Interactive)
   - Add link to notebooks section

3. `docs/getting-started/quickstart.md`:
   - Verify `get_column_lineage()` example matches current API signature
   - Add link to notebooks for extended examples
   - Verify config file TOML format matches implementation

4. API reference pages (audit each):
   - `api/core-functions.md` -- verify `convert_file`, `convert_file_with_llm` documented
   - `api/models.md` -- verify `ColumnLineage` documented
   - `api/enums.md` -- verify all 25+ enum types listed
   - `api/configuration.md` -- verify TOML/YAML/RC format examples
   - `api/scenarios-metrics.md` -- verify all factory methods documented
   - `api/mlops.md` -- verify all model classes documented

5. **New file (optional):**
   - `docs/examples/index.md` -- index page for notebooks with descriptions

**In scope:** Fixing inaccuracies, adding notebook links, verifying API completeness
**Out of scope:** Rewriting docs from scratch, adding tutorials beyond what notebooks provide, hosting notebooks as rendered HTML in docs

### e) Dependencies & Risks

- **Dependencies:** Best done after TODO items 2 and 3 (test and enhance notebooks) so the docs link to validated notebooks
- **Risks:**
  - mkdocstrings auto-generation may not pick up all symbols if docstrings are missing
  - `mkdocs build --strict` may reveal broken cross-references requiring fixes
- **Open questions:**
  - Should notebooks be rendered as HTML pages in the docs site (requires nbconvert plugin)?
  - Or just linked to the GitHub repository?

### f) Priority & Effort Estimate

- **Priority:** 2 -- docs are the second most important user-facing artifact after the code itself
- **Effort:** M (medium) -- auditing 15+ docs pages, fixing inaccuracies, adding nav entries

---

## TODO Item 5: Integrate with dataiku-mcp Factory

### a) Current State Assessment

**What exists:**
- No references to "dataiku-mcp" or "MCP" anywhere in the py-iku codebase or planning documents (`grep` of `.claude_plans/` returned zero results)
- There is a `.claude/skills/mcp-builder/` directory in the project, which is a Claude Code skill for building MCP servers -- this is tooling infrastructure, not library code
- No Dataiku-specific MCP server package was found in the codebase
- The term "dataiku-mcp factory" is not defined in any existing document

**Research on "dataiku-mcp factory":**
- This likely refers to building an MCP (Model Context Protocol) server that wraps py-iku as a tool, enabling AI assistants (like Claude) to convert Python code to Dataiku flows interactively
- Alternatively, it could mean integrating py-iku with a hypothetical Dataiku platform MCP server for direct DSS instance interaction
- The `.claude/skills/mcp-builder/` tooling suggests the project environment has MCP server creation capabilities

**What's working:** N/A -- nothing has been started
**What's missing:** Clarity on what "dataiku-mcp factory" means and what the integration scope is

### b) Success Criteria

**Cannot be fully defined until scope is clarified.** Preliminary criteria based on most likely interpretation:

| Criterion | Metric | Verification Method |
|-----------|--------|---------------------|
| Scope document exists | A clear spec defining what "dataiku-mcp factory" means for py-iku | Document in `.claude_plans/` |
| MCP server can call `convert()` | An MCP tool definition wraps `convert()` and returns flow JSON | MCP tool test |
| MCP server can call `convert_with_llm()` | An MCP tool wraps `convert_with_llm()` with provider configuration | MCP tool test |
| MCP server can call `visualize()` | An MCP tool returns ASCII/Mermaid visualization of a flow | MCP tool test |
| MCP server is documented | README or docs page explains how to run the MCP server | Documentation exists |

**Questions that MUST be answered before proceeding:**

1. What is the "dataiku-mcp factory"? Is this:
   a. An MCP server that exposes py-iku tools to AI assistants?
   b. An integration with an existing Dataiku MCP server?
   c. A factory pattern for creating MCP connections to Dataiku DSS instances?
   d. Something else entirely?

2. Who is the consumer of this MCP integration?
   a. Claude Code / AI assistants
   b. Other MCP clients
   c. Dataiku DSS itself

3. What is the deployment model?
   a. Standalone MCP server (stdio or HTTP)
   b. Plugin for an existing MCP server
   c. Library integration only

### c) Link to Use Case

- **How it serves the mission:** An MCP server would allow AI assistants to invoke py-iku as a tool, enabling conversational Python-to-Dataiku conversion. This is a natural evolution: instead of calling `convert()` in a script, users would say "convert this code to Dataiku" in a chat interface.
- **Pain point addressed:** Users currently must write Python code to use py-iku. An MCP integration would let them use natural language.
- **Impact if NOT completed:** py-iku remains a developer-only tool. The MCP ecosystem is growing rapidly and early integration could be a significant competitive advantage.

### d) Scope & Deliverables

**Pending user clarification.** Likely deliverables if this is an MCP server wrapping py-iku:

**Files to create:**
- `mcp_server/` -- MCP server directory
  - `server.py` -- Main server with tool definitions
  - `tools.py` -- Tool implementations wrapping py-iku API
  - `requirements.txt` -- MCP server dependencies
  - `README.md` -- Setup and usage instructions

**Tools to expose (likely):**
1. `convert_code` -- Takes Python code, returns Dataiku flow JSON
2. `convert_code_with_llm` -- Takes Python code + provider config, returns flow JSON
3. `visualize_flow` -- Takes flow JSON + format, returns visualization string
4. `export_to_dss` -- Takes flow JSON + project config, returns DSS bundle
5. `analyze_code` -- Takes Python code, returns analysis result (LLM mode)

**In scope (tentative):** MCP server wrapping core py-iku functionality
**Out of scope (tentative):** Direct Dataiku DSS instance API integration, real-time flow monitoring

### e) Dependencies & Risks

- **Dependencies:**
  - Requires clear scope definition from user (BLOCKER)
  - May depend on `mcp` Python package
  - If integrating with an existing Dataiku MCP server, requires access to that server's API/protocol
- **Risks:**
  - Scope creep if "factory" implies a generic framework for creating MCP integrations
  - MCP protocol may evolve, requiring maintenance
  - Testing MCP servers requires MCP client tooling
- **Open questions:** See Section b) -- three critical questions need user input

### f) Priority & Effort Estimate

- **Priority:** 4 (lowest of actionable items) -- blocked on scope clarification
- **Effort:** M-L (medium to large, depending on scope) -- building an MCP server is straightforward but testing and documentation add work

---

## TODO Item 6: Review Library Against Use Case

### a) Current State Assessment

**Original design spec** (`.claude_plans/py2dataiku_library_prompt.md`) defined 8 success criteria:

1. Accurately parse 90%+ of common pandas operations
2. Generate valid Dataiku recipe configurations (JSON schema compliant)
3. Produce clear, readable flow diagrams in multiple formats
4. Provide actionable optimization recommendations
5. Support both Python scripts and Jupyter notebooks
6. Handle edge cases gracefully with clear fallback to Python recipes
7. Comprehensive test coverage (>80%)
8. Well-documented API with examples

**Five independent reviews** have already been conducted:
- Architecture review
- Code quality review
- Test coverage analysis (71% at time of review, now 1693 tests)
- Feature gap analysis
- API/UX review

**Enhancement roadmap** compiled 4 tiers of improvements across these reviews.

### b) Success Criteria

| Criterion | Metric | Verification Method |
|-----------|--------|---------------------|
| Gap matrix produced | Table mapping every original spec item to current status with evidence | Document review |
| Enhancement roadmap items assessed | Every Tier 1 and Tier 2 item from `enhancement-roadmap.md` classified as Done/Partial/Not Started | Cross-reference with codebase |
| Feature coverage numbers updated | Current recipe, processor, and pandas coverage percentages calculated | Enum counts, mapping audits |
| End-to-end usability confirmed | A test user can go from "I have a pandas script" to "I have a Dataiku DSS project zip" in under 5 minutes | Manual walkthrough |
| Priority recommendations produced | Top 5 remaining gaps ranked by user impact | Analysis document |
| Clear assessment of library readiness | Binary answer: "Is the library usable end-to-end for its stated purpose today?" with evidence | Integrated assessment |

### c) Link to Use Case

- **How it serves the mission:** This is the meta-review -- it answers "have we built what we set out to build?" If the answer is no, it identifies what remains.
- **Pain point addressed:** Without this review, development may focus on nice-to-have features while critical gaps remain. This review ensures alignment with the original vision.
- **Impact if NOT completed:** The project risks feature creep (building things nobody asked for) while leaving gaps in the core conversion workflow.

### d) Scope & Deliverables

**File to create:**
- `.claude_plans/use-case-review.md` -- comprehensive gap analysis document

**Document structure:**

1. **Original Spec vs Current Implementation Matrix**

| Spec Item | Status | Evidence | Remaining Gap |
|-----------|--------|----------|---------------|
| Parse 90%+ pandas ops | Partial (~50% per gap analysis) | `PandasMapper` covers ~25 methods, 50+ common | Map 25+ more methods |
| Valid recipe configs | Mostly done | 34/37 recipe types, settings composition | 3 missing types, some settings incomplete |
| Flow diagrams in multiple formats | Done | 6 formats: SVG, HTML, ASCII, Mermaid, PlantUML, Interactive | None |
| Optimization recommendations | Partial | `FlowOptimizer` merges Prepare recipes, removes orphans | Filter pushdown, parallel branch detection not done |
| Python scripts and notebooks | Scripts done, notebooks not supported as input | `convert_file()` for .py files | No `NotebookAnalyzer` for .ipynb input |
| Edge case fallback to Python | Done | AST analyzer creates Python recipes for unrecognized patterns | Working |
| Test coverage >80% | Approaching (1693 tests, estimate ~75-80%) | Need fresh coverage run | May need targeted additions |
| Well-documented API | Done | 15 API docs pages, 5 example notebooks, docstrings on all public symbols | Docs accuracy needs verification |

2. **Enhancement Roadmap Progress**

Check each Tier 1 and Tier 2 item:

| Item | Description | Status (estimated) |
|------|-------------|-------------------|
| T1.1 | Fix DSSExporter recipe payload bugs | Likely done (part of comprehensive enhancement) |
| T1.2 | Fix silent error swallowing in LLM analyzer | Likely done (exception hierarchy exists) |
| T1.3 | Fix version inconsistency | Done (`importlib.metadata` in `__init__.py`) |
| T1.5 | Fix type annotations | Need to verify |
| T1.8 | Mark `get_column_lineage()` as NotImplementedError | Done (now implemented) |
| T1.11 | Export commonly needed types from `__init__.py` | Done (82 exports) |
| T1.12 | Add IF_THEN_ELSE and SWITCH_CASE processors | Done (in `PrepareStep` factory methods) |
| T1.13 | Add TRANSLATE_VALUES processor | Done (in `PrepareStep.translate_values()`) |
| T2.1 | Custom exception hierarchy | Done (7 exception types) |
| T2.2 | Extract shared base generator class | Done (`BaseFlowGenerator` ABC) |
| T2.3 | DAG data structure | Done (`FlowGraph` class) |
| T2.5 | Strengthen optimizer | Done (merges Prepare recipes, removes orphans) |
| T2.6 | Round-trip serialization | Done (`from_dict()`, `from_json()`, `from_yaml()`) |
| T2.7 | New test files for zero-coverage modules | Done (27 test files now exist) |
| T2.8 | Populate ProcessorCatalog | Partially done (122 entries claimed) |
| T2.10 | Add DatasetConnectionType enum | Done (13 types) |
| T4.1 | Refactor DataikuRecipe using composition | Done (`RecipeSettings` ABC with 12 subclasses) |
| T4.2 | Column lineage tracking | Done (`get_column_lineage()` with `ColumnLineage` dataclass) |
| T4.3 | Instance-based PluginRegistry | Done |
| T4.4 | DataikuScenario model | Done |
| T4.5 | Metrics and Checks models | Done |
| T4.7 | Flow Zones support | Done |

3. **Feature Coverage Numbers (Current)**

| Category | Spec/Roadmap Target | Current | Status |
|----------|-------------------|---------|--------|
| Recipe types | 37 | 37 (in `RecipeType` enum) | Complete |
| Processor types (enum) | 110+ | 122 (in `ProcessorType` enum) | Complete |
| Processor catalog entries | 122 | 122 (claimed in CLAUDE.md) | Need verification |
| pandas method mappings | 50+ common | ~25 direct + LLM fallback | Partial |
| sklearn mappings | 30+ common | ~12 classes | Partial |
| NumPy mappings | 25+ functions | ~15 functions | Partial |
| Dataset connection types | 15+ | 13 | Good |
| Automation (scenarios) | Full | Full model | Complete |
| Metrics/Checks | Full | Full model | Complete |
| MLOps | Partial | API endpoints, model versions, drift | Complete for scope |
| Visualization formats | 5 (per spec) | 6 | Exceeds spec |
| Test count | >80% coverage | 1693 tests | Need coverage % |
| Config system | Not in spec | Full (TOML/YAML/RC/env) | Exceeds spec |
| Plugin system | Not in spec | Full (instance-based registry) | Exceeds spec |

4. **Critical gaps remaining:**
   - Notebook input support (`NotebookAnalyzer`) -- promised in spec, not built
   - pandas method mapping coverage (~50%) -- still the primary gap
   - sklearn ML model training mapping (RandomForest, etc. -> ML recipes)
   - Interactive mode (`InteractiveConverter`) -- promised in spec, not built

5. **Top 5 priority recommendations**

**Actions to take:**
1. Read and audit ALL source files referenced in the enhancement roadmap to determine actual Done/Not Done status
2. Run `python -m pytest tests/ --cov=py2dataiku --cov-report=html` for current coverage numbers
3. Count actual `ProcessorCatalog` entries vs claimed 122
4. Verify pandas mapping coverage by counting methods in `PandasMapper`
5. Test end-to-end: write a realistic pandas script, convert it, export to DSS, verify output

**In scope:** Comprehensive gap analysis with evidence-based assessment
**Out of scope:** Implementing fixes (that's separate work)

### e) Dependencies & Risks

- **Dependencies:** None -- this is a review/analysis task
- **Risks:**
  - The enhancement roadmap was written when the library was at an earlier state; many items may already be done
  - Coverage numbers from the test-coverage-analysis.md (71%, 1000 tests) are outdated -- library now has 1693 tests
  - Some gap analysis claims may not reflect current state (e.g., ProcessorCatalog entries)
- **Open questions:** None

### f) Priority & Effort Estimate

- **Priority:** 2 (tied with docs update) -- this review determines what's left to do
- **Effort:** M (medium) -- primarily reading and auditing code, running coverage tools, producing a gap matrix

---

## Summary: Priority Order & Dependencies

```
Priority 1: TODO #2 (Test example notebooks)          [M effort, no blockers]
         |
         v
Priority 2: TODO #6 (Review library against use case) [M effort, no blockers]
         |  TODO #4 (Update docs)                      [M effort, benefits from #2, #3, #6]
         |
         v
Priority 3: TODO #3 (Add visualizations to notebooks) [S effort, depends on #2]
         |
         v
Priority 4: TODO #5 (Integrate with dataiku-mcp)      [M-L effort, BLOCKED on scope clarification]
```

### Dependency Graph

```
#2 Test notebooks ──> #3 Add visualizations ──> #4 Update docs
                                                      ^
#6 Review vs use case ────────────────────────────────┘

#5 MCP integration (independent, blocked on scope)
```

### Effort Summary

| TODO | Description | Priority | Effort | Blocked? |
|------|-------------|----------|--------|----------|
| #2 | Test example notebooks | 1 | M | No |
| #6 | Review library against use case | 2 | M | No |
| #4 | Update docs | 2 | M | No (but benefits from others) |
| #3 | Add visualizations to notebooks | 3 | S | On #2 |
| #5 | Integrate with dataiku-mcp factory | 4 | M-L | Yes (needs scope clarification) |

### Total Estimated Effort

- Items 2, 3, 4, 6: approximately 3-5 days of focused work
- Item 5: approximately 2-5 additional days depending on scope

---

*This review was compiled by analyzing the actual codebase, reading all 5 notebooks (331 total cells, 225 code cells), auditing the docs directory (18 files), cross-referencing the original design spec, enhancement roadmap, feature gap analysis, API/UX review, and test coverage analysis.*
