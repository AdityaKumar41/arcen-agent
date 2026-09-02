---
name: simplify-code
description: "Parallel 4-agent cleanup of recent code changes."
version: 1.1.0
author: Arcen Agent (inspired by Hermes Agent / Claude Code /simplify)
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [code-review, cleanup, refactor, delegation, subagent, parallel, simplify]
    related_skills: [requesting-code-review, test-driven-development, plan]
---

# Simplify Code — Parallel Review & Cleanup

Review your recent code changes with four focused reviewers running in
parallel, aggregate their findings, and apply the fixes worth applying.

**This is a cleanup pass, not a bug hunt.** You are improving the quality of
code that already works — removing duplication, flattening needless
complexity, cutting waste, and deepening band-aid fixes. Do not go hunting
for correctness bugs here; that's what `requesting-code-review` is for.

**Core principle:** Four narrow reviewers beat one broad reviewer. Each one
deeply searches the codebase for a single class of problem — reuse, quality,
efficiency, altitude — without diluting its attention across all four. They
run concurrently, so you pay the latency of one review, not four.

## When to Use

Trigger this skill when the user says any of:

- "simplify" / "simplify my changes" / "simplify these changes"
- "review my code" / "review my recent changes" / "clean up my changes"
- "/simplify" (if they're carrying the Claude Code habit over)

Optional modifiers the user may add — honor them:

- **Focus:** "simplify focus on efficiency" → run only the efficiency reviewer
  (or weight the aggregation toward it). Recognized focuses: `reuse`,
  `quality` (also accepts `simplification`), `efficiency`, `altitude`.
- **Dry run:** "simplify but don't change anything" / "just report" → run the
  four reviewers, present findings, apply NOTHING. Ask before applying.
- **Scope:** "simplify the last commit" / "simplify staged" / "simplify
  src/foo.py" → narrow the diff source accordingly (see Phase 1).

Do NOT auto-run this after every edit or tack it onto the end of unrelated
tasks. It costs four subagents' worth of tokens — invoke it only when the
user explicitly asks.

## The Process

### Phase 1 — Identify the changes

Capture the diff to review. Pick the source by what the user asked for, in
this default order:

```bash
# 1. Default: uncommitted working-tree changes (tracked files)
git diff

# 2. If that's empty, include staged changes
git diff HEAD

# 3. Scoped variants the user may request:
git diff --staged                 # "staged changes"
git diff HEAD~1                   # "the last commit"
git diff main...HEAD              # "this branch" / "my PR"
git diff -- src/foo.py            # specific file(s)
```

If `git diff` and `git diff HEAD` are both empty and there's no git repo or no
changes, fall back to the files the user explicitly named or that were
recently created/edited in this session. If you genuinely can't find any
changed code, say so and stop — there's nothing to simplify.

Capture the full diff text. Note its size: if it's very large (say >2000
changed lines), warn the user that four subagents each carrying the full diff
will be token-heavy, and offer to scope it down (per-directory, per-commit)
before proceeding.

### Phase 2 — Launch four reviewers in parallel

Use `delegate_task` **batch mode** — pass all four tasks in one `tasks`
array so they run concurrently. Four is the right fan-out for this pattern;
it's within the `delegation.max_concurrent_children` budget on any default
install.

**No delegation available?** If you can't call `delegate_task` in this
context (you're a leaf subagent, delegation is disabled, or the budget is
exhausted), do NOT skip the review or drop angles. Work through all four
reviewer angles yourself, sequentially, in this context — same search
standards, same finding format. Then say clearly in your final summary that
this was a single-pass inline review, not the parallel fan-out, so the user
knows what actually ran.

Give **every** reviewer the **complete diff** (not fragments — cross-file
issues hide in the gaps) plus the absolute repo path so they can search the
wider codebase. Each reviewer gets `terminal`, `file`, and `search`
toolsets (so they can `git`, `read_file`, and `search_files`/grep).

Tell each reviewer to:
- Search the existing codebase for evidence (don't reason from the diff alone).
- **Apply Chesterton's Fence:** before flagging anything for removal, run
  `git blame` on the line to understand why it exists. If you can't determine
  the original purpose, mark it `confidence: low` — don't guess.
- Report findings as structured output with the concrete cost, confidence,
  and risk:
  ```
  file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
  ```
  The **cost** field forces each finding to justify itself — a finding that
  can't articulate what the problem actually costs is probably a nit.
  - **SAFE** = proven not to affect behavior (unused imports, commented-out
    code, pass-through wrappers). Auto-apply these.
  - **CAREFUL** = improves without changing semantics (rename local variable,
    flatten nested ternary, extract helper). Apply with test verification.
  - **RISKY** = may change behavior or breaks public contracts (N+1
    restructuring, public API rename, memory lifecycle change). Flag for
    human review — do NOT auto-apply.
- Skip nits and style-only churn. Only flag things that materially improve
  the code.

Pass these four goals (drop any the user's focus excludes):

**Reviewer 1 — Code Reuse**
> Review this diff for code that duplicates functionality already in the
> codebase. Search utility modules, shared helpers, and adjacent files
> (use search_files / grep) for existing functions, constants, or patterns
> the new code could call instead of reimplementing. Flag: new functions
> that duplicate existing ones; hand-rolled logic that an existing utility
> already does (manual string/path manipulation, custom env checks, ad-hoc
> type guards, re-implemented parsing). For each, name the existing thing to
> use and where it lives.

**Reviewer 2 — Code Quality**
> Review this diff for quality problems. Look for: redundant state (values
> that duplicate or could be derived from existing state; caches that don't
> need to exist); parameter sprawl (new params bolted on where the function
> should have been restructured); copy-paste-with-variation (near-duplicate
> blocks that should share an abstraction); dead code; and magic numbers /
> inline strings that should be named constants. For each finding, explain
> the concrete maintenance cost.

**Reviewer 3 — Efficiency**
> Review this diff for performance and resource issues. Look for: O(N²) or
> worse loops where a dict/set lookup or sort would flatten the curve; N+1
> query patterns; redundant passes over data; unnecessarily large allocations;
> missing short-circuit returns; re-computation inside loops of things that
> don't change. Only flag things with a realistic performance impact for the
> expected data scale — don't micro-optimize sub-microsecond paths.

**Reviewer 4 — Altitude / Abstraction**
> Review this diff from 10,000 feet. Look for: abstractions set at the wrong
> level (too low: the caller has to know too much; too high: the function does
> too little); responsibilities leaking across layers; cases where the new
> code is a band-aid on a design issue that should be fixed at source.
> Distinguish "this is a band-aid and here's why" from "this is intentional
> pragmatism." Flag only issues where the altitude mismatch will create
> recurring friction or bugs, not just style preferences.

### Phase 3 — Aggregate and apply

When all reviewers report back:

1. **De-duplicate** findings across reviewers (the same line may appear in
   multiple reports; collapse it into one finding).
2. **Rank** by `risk` then `confidence`: SAFE/high first, RISKY/low last.
3. **Present a summary** to the user:
   - Group by risk tier.
   - For SAFE findings, state you're applying them now.
   - For CAREFUL findings, list them and ask the user to confirm before
     applying (or apply and run tests if you have a test suite available).
   - For RISKY findings, present them and explicitly do NOT apply without
     explicit instruction.
4. **Apply** the approved set:
   - Make the edits.
   - If a test suite exists, run it. If tests break, revert the offending
     change(s) and note what broke.
   - Report what was changed, what was skipped, and what needs human action.

## Output Format

After applying, give the user a concise table:

```
| File | Change | Risk | Reviewer |
|------|--------|------|---------|
| src/foo.py:42 | Replaced inline parse with existing `parse_env()` | SAFE | Reuse |
| src/bar.py:88 | Removed redundant cache dict | SAFE | Quality |
| src/baz.py:12 | Flatten O(N²) loop → dict lookup | CAREFUL | Efficiency |
| src/core.py:5 | Band-aid on wrong layer — logged for human review | RISKY | Altitude |
```

Then: test results (if run), and any RISKY items left for the user to decide.
