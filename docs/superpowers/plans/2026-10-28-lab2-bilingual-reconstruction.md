# Lab 2 Bilingual Experiment and Defense Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compare Claude Haiku 4.5 and Llama 3.3 70B for Lab 2, then deliver assignment-complete Russian and English reports and matching defense guides.

**Architecture:** Reuse the repository's profile-aware API configuration from `labs.common`, update the Lab 2 runner to follow the assignment's Model A/Model B roles, and build both reports from one verified run folder. Claude Haiku 4.5 is Model A; Llama 3.3 70B is Model B. Export each language's Markdown to HTML and DOCX with the existing shared document exporter; keep the original runs untouched.

**Tech Stack:** Python 3, OpenAI-compatible SDK, `python-dotenv`, `requests`, `python-docx`, Markdown-it, `unittest`, `uv`.

**Spec:** `docs/superpowers/specs/2026-10-28-lab2-report-reconstruction-design.md`

## Global Constraints

- Model A is `anthropic/claude-haiku-4.5`; Model B is `meta-llama/llama-3.3-70b-instruct`.
- Do not use Nemotron or write credentials into logs, reports, or results.
- Read the active `LAB_API_PROFILE` through the shared profile-aware configuration; preserve separate profile keys and endpoints.
- Write this run to a new folder under `results/`; do not overwrite old runs.
- The reviewer is one-way: Model B evaluates Model A's final answer in a fresh request.
- Use temperature `0.3`, maximum output `4096` tokens, and the configured profile timeout for a reproducible comparison.
- The report must distinguish measured evidence, model review, and draft personal judgments.
- Russian and English outputs must have the same data and all 14 assignment sections.
- Run only bounded API attempts; retain all response statuses and disclose failed or truncated outputs.

## Review Focus

- Wrong or unavailable model IDs: test exact model validation before any completion request.
- Profile/key mismatch: test Cloud.ru and course profile mapping with mocked environments and assert secrets are not part of serialized output.
- Truncated/empty responses: test status accounting and bounded retry behavior.
- Reviewer JSON/code-fence/parse failure: test preservation of the raw reviewer response and explicit parse-failure status.
- Context-dependent edge prompt: test that the prior essay is included in audience-rewrite input.
- Word-limit failure: test the 180–220 count on fixture outputs and surface misses in both languages.

---

## File Structure

- Modify `lab2/common.py` to obtain the selected profile, endpoint, models, timeouts, and client from the shared API-profile layer while retaining Lab 2 request/result helpers; remove the unnecessary pandas dependency by writing CSV through the standard library.
- Modify `lab2/runner.py` to validate selected models, run the required paired versions and edge cases, make a single independent reviewer request, and save a fresh manifest.
- Create `lab2/test_runner.py` for deterministic mocked tests of configuration, call roles, status handling, and saved artifacts.
- Modify `lab2/report.py` to generate the complete Russian report from a run folder, including all required prompts, outputs, analysis, scores, and limitations without truncation.
- Create `lab2/report_en.py` for an English report using the same validated data and section map.
- Create `lab2/export_reports.py` to export both report languages through the shared document helper.
- Use `lab1/documents.py` as the shared Markdown-to-HTML/DOCX exporter; do not use the existing `lab2/md_to_docx_en.py` auto-translation path.
- Modify `DEFENSE_GUIDE_LAB2_RU.md` and `DEFENSE_GUIDE_LAB2_EN.md` to match the verified run and implementation.
- Generate `LAB2_REPORT.md`, `LAB2_REPORT.html`, `LAB2_REPORT.docx`, and matching `_EN` files from the new run.

## Task 1: Profile-Aware Lab 2 Configuration

**Files:**
- Modify: `lab2/common.py`
- Test: `lab2/test_runner.py`

**Interfaces:**
- `Lab2Config.from_env(profile: str | None = None) -> Lab2Config` maps `labs.common.load_config(profile)` into the Lab 2 configuration and preserves Lab 2 model overrides.
- `Lab2Client.list_models() -> list[str]` returns models from the selected endpoint.
- `save_results_csv(results: list[CompletionResult], filepath: str) -> None` writes the existing result fields with Python's `csv` module.

- [x] **Step 1: Write failing profile and CSV tests** for Cloud.ru and course profiles; assert the selected key is used internally, endpoint/profile/model IDs map correctly, serialized manifests never include a credential, and CSV headers/rows round-trip correctly.
- [x] **Step 2: Run the profile tests** with `uv run --with pandas --with-requirements requirements.txt python -m unittest lab2.test_runner -v`; the temporary `pandas` extra permits the current implementation to import so the profile tests fail at their intended assertions.
- [x] **Step 3: Implement shared-profile mapping** in `Lab2Config.from_env()`, validate positive token/time limits without printing key values, and replace pandas CSV output with `csv.DictWriter`.
- [x] **Step 4: Run the profile tests** and confirm both profile cases pass.

## Task 2: Assignment-Accurate, Testable Runner

**Files:**
- Modify: `lab2/runner.py`, `lab2/common.py`
- Test: `lab2/test_runner.py`

**Interfaces:**
- `Lab2Runner.run_all() -> list[CompletionResult]` runs Model A's baseline; paired V1/V2/V3 prompts on A and B; at least three fully-contextualized edge checks; and one Model B review of Model A's final answer.
- Persist raw outputs, exact prompts, per-attempt status, model ID, latency, tokens, finish reason, selected profile, and source/runner hashes in the unique run directory.

- [x] **Step 1: Add failing mocked-client tests** asserting baseline uses Model A only, V1/V2/V3 prompt strings are identical across both models, the reviewer direction is B → A only, and reviewer input contains the task, criteria, final prompt, and final answer.
- [x] **Step 2: Add failing failure-path tests** asserting empty/truncated responses are not counted as success, final-answer retries are bounded to two attempts, any existing output folder is rejected, and audience-rewrite edge input includes the preceding essay.
- [x] **Step 3: Run the focused tests** and confirm the current runner's reciprocal review and incomplete context trigger failures.
- [x] **Step 4: Implement the minimal runner changes**; run with Model A `anthropic/claude-haiku-4.5`, Model B `meta-llama/llama-3.3-70b-instruct`, temperature `0.3`, max output `4096`, and a unique output directory. Validate model availability before any completion request.
- [x] **Step 5: Run all Lab 2 tests** and inspect the temporary manifest/CSV for model IDs, status totals, and absence of credentials.

## Task 3: Execute and Validate the New Model Comparison

**Files:**
- Create: a new run folder such as `results/lab2_claude_haiku_llama_20261028/`
- Test: no live API test; use the mocked runner suite from Task 2 before execution.

- [x] **Step 1: Check the active profile and exact model availability**; do not print API keys.
- [x] **Step 2: Run the experiment once** with `anthropic/claude-haiku-4.5` as Model A and `meta-llama/llama-3.3-70b-instruct` as Model B, temperature `0.3`, max output `4096`, and a new output folder.
- [x] **Step 3: Inspect the manifest and raw CSV/JSON**; reconcile all request counts, finish reasons, errors, word counts, and reviewer parse status. Do not hide or overwrite failed attempts.
- [x] **Step 4: If the API run is incomplete**, make only bounded retries for missing/failed cells and preserve the original attempt evidence; stop if the endpoint, quota, or model access prevents completion.

## Task 4: Complete Russian and English Reports

**Files:**
- Modify: `lab2/report.py`
- Create: `lab2/report_en.py`
- Create: `lab2/export_reports.py`
- Test: `lab2/test_runner.py`

**Interfaces:**
- `lab2.report.build(run_dir, language, student, group) -> str` builds either language from the same run folder. `lab2.report_en` is a thin English CLI wrapper.
- Both builders read the same manifest and raw outputs and emit complete, untruncated required content.

- [x] **Step 1: Add a temporary-run fixture** with two models, V1/V2/V3 rows, edge results, one successful reviewer, one failed response, and a manifest.
- [x] **Step 2: Add failing tests** that require all 14 task headings, actual model IDs, complete prompts/answers, rubric/self-review sections, Prompt Card, final essay/edit disclosure, no template expressions, and explicit failure handling in both languages.
- [x] **Step 3: Run the tests** and confirm the present Russian generator fails on placeholders, truncation, and missing sections.
- [x] **Step 4: Implement the Russian and English builders** using explicit bilingual labels and verified run data. Do not infer a missing reviewer score or claim a personal opinion as confirmed.
- [x] **Step 5: Build both reports from the new run** and validate their section coverage, key metrics, word counts, model names, and cross-language consistency.

## Task 5: Export and Visually Verify Documents

**Files:**
- Create: `lab2/export_reports.py`
- Use: `lab1/documents.py`
- Generate: `LAB2_REPORT.html`, `LAB2_REPORT.docx`, `LAB2_REPORT_EN.html`, `LAB2_REPORT_EN.docx`

- [x] **Step 1: Add `lab2.export_reports.main()`** to call `lab1.documents.export_document(path, language=...)` for both Markdown reports; avoid `lab2/md_to_docx_en.py` because it translates text during export rather than building a separately reviewed English report.
- [x] **Step 2: Run the exporter** with `uv run --with-requirements requirements-report.txt python -m lab2.export_reports` and confirm both HTML and DOCX outputs exist and are non-empty.
- [x] **Step 3: Render both DOCX files to page images** using the documents skill renderer.
- [x] **Step 4: Inspect every page** for clipping, broken tables, missing glyphs, page number errors, and unreadable prompt/answer blocks.
- [x] **Step 5: Fix any defects and rerender** until both documents pass visual review.

## Task 6: Update Both Defense Guides

**Files:**
- Modify: `DEFENSE_GUIDE_LAB2_RU.md`, `DEFENSE_GUIDE_LAB2_EN.md`

- [x] **Step 1: Replace stale model claims and fabricated/stale figures** with exact findings from the new manifest and raw outputs.
- [x] **Step 2: Align the walkthrough with the completed 14-task assignment**, actual runner responsibilities, report files, and disclosed limitations.
- [x] **Step 3: Add concise likely instructor questions** on prompt evolution, few-shot effects, word limits, failed edge cases, one-way reviewer design, and the two selected models.
- [x] **Step 4: Cross-check each stated number and code-path explanation** against the final reports and source files.

## Task 7: Final Verification

**Files:** all changed files above.

- [x] Run `uv run --with-requirements requirements.txt python -m unittest lab1.test_runner labs.test_common lab2.test_runner -v`.
- [x] Run `git diff --check` on all changed files.
- [x] Search all final reports/guides for Nemotron, test names, unresolved placeholders, unsupported model claims, and leaked credentials.
- [x] Compare both reports against all 14 assignment requirements and compare each reported statistic with the new run artifacts.
- [x] Confirm the previous `results/lab2` and `results/lab2_new` folders were not modified.
- [x] Confirm both DOCX render directories contain every expected page and record that every page was visually inspected.

## Plan Self-Review

- **Spec coverage:** API profile handling and the new run are Tasks 1–3; all 14 report sections are Task 4; bilingual exports and visual QA are Task 5; defense preparation is Task 6; acceptance checks are Task 7.
- **Review focus:** Every listed failure mode has an owning test in Tasks 1, 2, or 4.
- **Type consistency:** The shared builder accepts a run directory, language, and optional student/group values and returns Markdown text; the existing `Lab2Runner` and `CompletionResult` types remain the runner contract.
- **Execution approach:** Native, in this session. Model calls are authorized by the user; this plan should still be reviewed against the selected model pair and output scope before implementation.
