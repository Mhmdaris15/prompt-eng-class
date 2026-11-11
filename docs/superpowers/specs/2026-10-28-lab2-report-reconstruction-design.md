# Lab 2 Experiment, Report, and Defense Package

## Intent

Complete the ITMO Prompt Engineering Lab 2 assignment with a reproducible experiment, accurate reports in Russian and English, and updated defense guides in both languages. The user no longer trusts the Nemotron-generated work and has authorized new API calls.

## Current evidence

- The newest saved run records `moonshotai/Kimi-K2.6` and `Qwen/Qwen3-Coder-Next`; the older run records Kimi and Gemini. Neither contains Nemotron results.
- The current API profile resolves to the Cloud.ru-compatible endpoint. A read-only model listing confirms `anthropic/claude-haiku-4.5` and `meta-llama/llama-3.3-70b-instruct` are currently available. No credential values were printed.
- Existing `lab2/runner.py` implements only the first nine assignment tasks, and its reviewer flow makes a reciprocal evaluation that is not required. The report generator leaves template expressions, truncates prompts and answers, and omits required final deliverables.
- Existing defense guides contain unsupported or stale results and describe the runner as completing more tasks than it does.

## Goals

- Run a new, timestamped Lab 2 experiment using `anthropic/claude-haiku-4.5` as Model A and `meta-llama/llama-3.3-70b-instruct` as Model B, subject to an availability check immediately before execution.
- Use Model A for the baseline, prompt iterations, and final answer. Send identical V1, V2, and V3 versions to Model B for the assignment's cross-model comparisons. Use Model B as the single independent reviewer of Model A's final answer.
- Exercise at least three edge cases with prompts that include all needed context; record truncation or failed calls as failures rather than successes.
- Complete all 14 assignment sections in both the Russian and English reports, including the criteria/rubric, prompt-design tables, complete prompt versions, few-shot analysis, edge-case analysis, reviewer-versus-self evaluation, final Prompt Card, final essay, edit disclosure, and conclusions.
- Update `lab2/runner.py` and `lab2/common.py` only where needed to implement the actual assignment, select the active API profile safely, preserve raw outputs, and write a fresh run manifest.
- Produce Russian and English Markdown and DOCX reports, plus refreshed Russian and English defense guides that use the new run's verified findings.
- Leave student name/group blank for the user to fill. Clearly distinguish measured evidence, model review, and the user's personal judgments.

## Non-goals

- Do not use Nemotron or claim it produced the new experiment.
- Do not overwrite either existing Lab 2 run.
- Do not expose, log, or copy API credentials into reports or artifacts.
- Do not invent the student's own opinions, scores, or manual edits. Any proposed self-evaluation language must be clearly presented for user verification.

## Approaches considered

1. **Repair the report using existing Kimi/Qwen results.** No generation calls are needed, but the present run has a failed reverse review and known report/data defects. It is useful as comparison data, but weaker as the final submission. Not recommended as the sole source.
2. **Run a clean, bounded comparison of Claude Haiku 4.5 and Llama 3.3 70B, then repair the report pipeline and create bilingual outputs.** Both exact IDs are currently available. This yields fresh evidence, follows the assignment's Model A/Model B roles, and avoids Nemotron. Recommended.
3. **Replace the full experiment with a hand-written report only.** This could fill assignment sections quickly but would lack fresh, reproducible outputs and would not repair the report-generation path. Rejected.

## Evidence and accuracy rules

- Use the currently configured lab API profile and its endpoint; never print credential contents. Confirm model availability and selected profile before generating.
- Record the actual model IDs, settings, timestamp, source/prompt/code hashes, and all response statuses in a new results folder.
- Use the required assignment role split: Model A generates the main outputs; Model B receives the task, criteria, final prompt, and Model A answer in a separate review request. Do not treat a reciprocal review as required.
- Count words with one documented rule. If a response misses the 180–220-word requirement, revise the prompt and retry within a bounded attempt limit; preserve failed attempts and report what happened.
- Score quality against the assignment rubric and keep an auditable note for every score. Draft personal agreement/disagreement reflections for the user to confirm rather than attributing unconfirmed opinions to them.
- If API errors, truncation, model unavailability, or quota limits prevent a complete run, report that state plainly; do not manufacture missing outputs.

## Constraints

- The source text and existing run folders remain unchanged.
- Use a unique output directory for the new run.
- Keep Russian and English reports aligned in data and section structure.
- Defense materials must explain the actual code and actual measurements, not predicted results.
- Render and visually inspect every page of each final DOCX.

## Proposed implementation

1. Add explicit profile-aware Lab 2 configuration and validation, reusing the repository's existing Cloud.ru/course profile conventions without duplicating or exposing secrets.
2. Update the runner for the assignment's Model A/Model B roles, reliable context in edge prompts, bounded retries for empty/truncated responses, complete metadata, and a unique run directory.
3. Check availability of the selected pair, then execute the experiment and preserve every raw response and status.
4. Rebuild the report generator around the assignment's 14 tasks. Generate Russian and English Markdown from the same verified run and include complete required prompts, final output, rubric scores, and limitations.
5. Export both reports to DOCX and render/review each page; fix layout issues and render again as needed.
6. Update `DEFENSE_GUIDE_LAB2_RU.md` and `DEFENSE_GUIDE_LAB2_EN.md` with an accurate short presentation, code walkthrough, verified results, and likely instructor questions.
7. Verify the run manifest and report figures against raw artifacts, validate all 14 assignment requirements, scan for placeholders/secrets/truncation, run relevant offline tests, and visually review both DOCX files.

## Acceptance checks

- No request uses Nemotron; model IDs in both reports match the new manifest.
- Model B's review is one-way, independent, and includes all inputs required by the assignment.
- All 14 assignment tasks appear in both reports with matching content and actual results.
- Any failed/truncated response, manual edit, word-limit miss, or incomplete personal judgment is disclosed accurately.
- No fake student details, literal template expressions, unsupported performance claims, or credential values remain.
- Both DOCX files render, and every page is visually checked.
- Both defense guides match the verified report and explain the real execution path.
- Existing run folders are unchanged.

## Open decisions

- The proposed pair is Claude Haiku 4.5 (Model A) and Llama 3.3 70B (Model B), as requested and verified available. The read-only availability check does not guarantee generation quota or request success.
- Student name and group remain blank until supplied.
