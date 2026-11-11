# Lab 2 Defense Guide (English)

## 90-second presentation

I compared `anthropic/claude-haiku-4.5` (Model A) with `meta-llama/llama-3.3-70b-instruct` (Model B) through the Cloud.ru OpenAI-compatible endpoint. The task was to write a 180–220-word essay for 9th–10th grade students about why AI answers should be checked. I tested a simple baseline, a structured prompt (V1), a one-example prompt (V2), and a three-example prompt (V3), then ran five stress prompts and asked Model B to review Model A’s V3 answer.

The run used temperature 0.3, a 4096-token output limit, and a 180-second timeout. It recorded 13 requests: 12 successful and one failed. Claude’s V3 answer was 214 words and within the target; Llama’s was 163 words and short. Llama’s V2 request failed with HTTP 502. Claude’s citation-risk edge response returned plausible references with two author/year mismatches, which I checked against the publisher and arXiv records. This is one small run, so it supports observations about these outputs, not a universal ranking of the models or prompts.

## Demonstration: code and artifacts

1. Show `.env` only if needed; never reveal the key. Explain that `LAB_API_PROFILE` selects the endpoint and key through `labs/common.py`.
2. Show `lab2/source_text.py` for the topic, task, audience, quality criteria, and undesirable errors.
3. Show `lab2/runner.py`: it validates both model IDs before generation; runs Model A’s baseline, paired V1/V2/V3 prompts, five edge cases on Model A, then a one-way Model B review of Model A’s V3 answer. Results and prompts are saved in a new run directory.
4. Show `lab2/common.py`: profile-aware client setup, request statuses and usage, word/latency and text-marker metrics, CSV/JSON persistence, and the manifest. Counts such as links and years are heuristics, not fact-checkers.
5. Show `results/lab2_claude_haiku_llama_20261028_202806/manifest.json` and the raw JSON/CSV. Point out the exact model IDs, settings, hashes, status counts, prompts, and responses. No API key is stored there.
6. Compare the V1/V2/V3 rows. The measured results are mixed: Claude went from 95 words in V1 to 203 in V2 and 214 in V3; Llama returned 166 words in V1, its V2 request failed, and its V3 response had 163 words. This experiment does not isolate a causal few-shot effect because it uses one response per cell and V2 is missing for Llama.
7. Show `task8_edge_cases.json` for the five Model A stress prompts and `task9_evaluations.json` for Model B’s review. Its fenced JSON was recovered for analysis while its raw response was retained. Treat the 2/2 scores cautiously: the reviewer was generous and missed citation metadata errors found by manual source checking.
8. Show `reports/lab2/LAB2_REPORT.md` / `reports/lab2/LAB2_REPORT_EN.md` and their DOCX/HTML exports. The reports include the prompts, outputs, rubric, edge cases, reviewer assessment, Prompt Card, final answer, and limitations. The draft self-assessment and reflection are explicitly for the student to confirm.

## Results to remember

| Item | Verified result |
| --- | --- |
| Models | Model A `anthropic/claude-haiku-4.5`; Model B `meta-llama/llama-3.3-70b-instruct` |
| Profile and settings | Cloud.ru; temperature 0.3; max output 4096 tokens; timeout 180 seconds |
| Requests | 13 total: 12 `ok`, 1 `error`, 0 `truncated` |
| Failure | Model B V2 request returned HTTP 502 (“Request failed”) after about 77.2 seconds |
| V3 length | Model A 214 words (within 180–220); Model B 163 words (below target) |
| Model A V1 | 95 words; response ended mid-sentence despite `finish_reason=stop`—the report discloses this |
| Edge cases | Five run on Model A; the citation-risk answer had two incorrect author/year attributions |
| Reviewer | Model B reviewed Model A only; JSON was inside a code fence; its high scores are not independent proof of quality |

The citations were checked against the [ACM DOI record](https://doi.org/10.1145/3571730) and the [official arXiv record](https://arxiv.org/abs/2005.00661). The former identifies Ji et al. (2023), not Rawte et al.; the latter identifies Maynez et al. (2020), not Zhang et al. The lesson is that a plausible DOI or arXiv identifier does not validate the attached author and year.

## Likely instructor questions

### What changed from V1 to V2 to V3?

V1 adds a role, audience, structure, and explicit constraints. V2 adds one example. V3 adds three examples intended to demonstrate a concrete claim, an explanation of relevance, and a cautious conclusion. In this run, the outputs do not prove that the examples caused an improvement: there was one sample per cell, and Llama’s V2 call failed.

### Which model performed better?

For the narrow word-count requirement on V3, Claude produced 214 words and Llama produced 163. Claude’s final response met that one constraint; that is not enough evidence to say Claude is generally better. Llama’s V2 failure also means this is not a complete paired comparison for all prompt versions.

### Why use a one-way reviewer?

The assignment’s review task is implemented as one separate request in which Model B assesses Model A’s final answer. That keeps the direction clear and avoids implying a reciprocal evaluation that was not run. Model review is still only one perspective and must be checked against the rubric and sources.

### What did the automatic metrics measure?

The runner saves latency, token usage, finish reason, character and whitespace-separated word counts, and counts of links, years, numbers, caution phrases, and confidence phrases. These are simple indicators. They do not determine whether a citation is real or a statement is true; the citation edge case demonstrates why manual verification matters.

### Why is the failed request included?

The Llama V2 request returned HTTP 502 after about 77.2 seconds. It remains in the raw results and manifest as an error; the report does not silently retry or replace it. Transparent status accounting makes the comparison reproducible and exposes the missing cell.

### Did Claude satisfy the edge-case citation request?

It returned three references, but two bibliographic attributions were wrong: it associated the DOI for Ji et al. (2023) with Rawte et al. and the arXiv record for Maynez et al. (2020) with Zhang et al. The answer’s `ok` API status only means text was returned; it does not mean its facts were correct.

### What are the experiment’s main limitations?

There is one sample per planned prompt/model cell, one missing Llama V2 answer, no controlled estimate of variance, and one reviewer response. The automatic markers are lexical heuristics. Also, the V3 examples include an explicitly fictional citation, which can prime citation-like output and should be replaced with a clearly labeled neutral example in a future run.

### What would you improve next?

Repeat each cell with multiple samples, repair the missing V2 cell in a separately labeled run, use blinded human scoring, verify citations against authoritative records, and revise the few-shot examples to avoid plausible fake bibliographic details. Compare quality and latency together.

## Short closing statement

This run shows why prompt engineering needs both structured comparisons and careful validation. Examples may help demonstrate a desired writing pattern, but one run cannot establish causality. A model can return a fluent answer, satisfy the API, and still miss a word limit or misattribute a citation. Saving exact prompts, outputs, settings, failures, and code hashes makes those findings inspectable.
