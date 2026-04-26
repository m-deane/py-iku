# py-iku Textbook — Style Contract

This file is the binding style contract for Phase 2 writer agents. Every chapter under `docs/textbook/` must conform to it. When in doubt, prefer the rule here over personal taste.

## 1. Voice

- Active, declarative, technical. Write as if explaining to a peer engineer.
- No marketing register. The reader has already decided to use the library; do not sell it.
- No first-person plural ("we"), no second-person hedging ("you might want to consider"), no breathless verbs ("delve into", "leverage", "unlock").
- No emojis anywhere — headings, prose, code comments, or diagrams.
- Prefer short sentences. Break compound claims into separate sentences when each could be cited independently.

## 2. Section template

Every chapter (1–12) opens and closes with the same two sections:

- The first H2 is `## What you'll learn` — 2–3 sentences naming the concrete capabilities the reader gains.
- The final H2 is `## What's next` — exactly one sentence pointing to the next chapter.
- Between them, use H2/H3 freely, but every chapter must include `## Further reading` as the second-to-last section (see rule 7).

Appendices use `## Scope` instead of `## What you'll learn` and omit `## What's next`.

## 3. Code-block conventions

- Every code block must be runnable as written. No `...`, no `# (omitted)`, no pseudocode.
- Import from the public API: `from py2dataiku import convert, DataikuFlow, ...`. Reach for `CodeAnalyzer` / `FlowGenerator` / `LLMFlowGenerator` only in chapters that explicitly cover internals (Ch 3, Ch 7, Ch 12).
- Prefer `convert(source)` as the entry point unless the chapter's subject demands otherwise.
- Pin column names and dataset names to the running example schema (see `_running_example.md`). Do not invent new column names mid-chapter.
- Show the input pandas snippet, then the resulting flow shape, then any assertion the reader can run themselves.
- Keep blocks under ~30 lines. Split longer flows into two blocks with a one-line bridge between them.

## 4. Citation style

When making a factual claim about DSS, the DSS API, or measured library behavior, cite inline.

- DSS API behavior or canonical names: link to the relevant file or class in `dataiku-api-client-python`. Form: `(see [dataiku-api-client-python source](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py))`.
- DSS user-facing concepts (recipes, flows, partitions): link to `doc.dataiku.com`. Form: `(see [Dataiku docs: Visual recipes](https://doc.dataiku.com/dss/latest/preparation/index.html))`.
- Internal evidence from the ultrareview or controlled experiments: cite the *measurement*, not the path to the internal doc. Example: write "3/3 identical runs at temperature=0 across the 18-recipe corpus" rather than linking `.claude_plans/llm-control-...md`.
- Never write "according to internal benchmarks" without saying which benchmark.

If a claim cannot be cited, soften it ("in current py-iku, the generator merges ...") or remove it.

## 5. Theory/howto ratio

Target ~30% theory, ~70% applied per chapter. "Theory" means data-engineering or DSS conceptual material that survives a future API revision. "Applied" means runnable code, expected output, or assertions against the produced flow.

The theory-heaviest chapter is Ch 8 (filters and predicates). The applied-heaviest chapters are Ch 2 (5-second tour), Ch 6 (recipe types tour), and Ch 11 (production usage).

## 6. Length per chapter

- Chapters 1–12: 1500–3500 words.
- Appendices A and B: 500–1200 words.
- Appendix C (cheatsheet): 500–800 words, mostly tabular.

Word count includes prose only — code blocks and tables do not count toward the limit but should not balloon a chapter past ~3500 words of prose.

## 7. Cross-reference rules

Every chapter ends with `## Further reading` immediately before `## What's next`. The list must contain at least:

- One link into `docs/api/` for the relevant API surface (e.g. `docs/api/recipes.md`).
- One link to a notebook under `notebooks/` that exercises the chapter's material.
- Optionally, one external reference already cited in the body.

Use absolute repo-rooted paths in markdown links: `[Recipes API reference](../api/recipes.md)` from a chapter file. Do not invent file names — confirm each link target exists before writing it.

## 8. Banned phrasings

These phrases are forbidden anywhere in the textbook. Treat any draft containing them as failing review.

- "robust", "powerful", "seamlessly", "effortlessly", "elegant", "intuitive"
- "we'll explore", "let's dive in", "in this chapter we", "join me as we"
- "best practice" without an immediately adjacent explanation of *why*
- "industry-standard" without a citation
- "Note that" / "It's important to note" / "Keep in mind that" — drop the preamble and state the fact
- "simply", "just", "easy" — almost always wrong about the reader's experience
- "cutting-edge", "state-of-the-art", "next-generation"
- emojis of any kind, in headings, prose, or code comments
- "magic" used as praise (e.g. "the magic happens in ...")

## 9. Banned content

- Do not summarize the README. The textbook explains *why* the library is shaped the way it is; the README explains *what* it does.
- Do not duplicate `docs/api/`. Link to it. If the API doc is wrong, file an issue rather than restate it differently here.
- Do not pretend features exist that do not. Cross-check every public symbol against `py2dataiku/__init__.py` before using it in an example.
- Do not use scikit-learn examples in chapters 1–11. Ch 12 is the only chapter that may discuss sklearn, and only as an extension/plugin case study.
- Do not introduce datasets or column names outside the running-example schema in `_running_example.md` unless the chapter is explicitly demonstrating a non-running-example pattern (Ch 6 recipe-type tour, Ch 9 advanced patterns). Even then, declare the new schema in a fenced block at the top of the section.
- Do not include speculative claims about DSS execution internals (e.g. "DSS uses a hash index for FilterOnValue"). The Ch 8 framing is "distinct processor types for distinct operator classes" — do not upgrade it to claims about indexing or query planning unless a primary source is cited.

## 10. Review checklist

Before submitting a chapter, verify:

- [ ] First H2 is `## What you'll learn`, last H2 is `## What's next`.
- [ ] `## Further reading` is present with at least one `docs/api/` link and one `notebooks/` link.
- [ ] Every code block is runnable and uses the public API.
- [ ] No banned phrasing (search for each term in section 8).
- [ ] Word count between 1500 and 3500 (or 500–1200 for appendices A/B, 500–800 for C).
- [ ] Theory/applied split is roughly 30/70.
- [ ] Every DSS factual claim has an inline citation.
- [ ] Column names and dataset names match `_running_example.md`.
