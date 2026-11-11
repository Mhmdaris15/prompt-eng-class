"""Build an English Lab 1 report from a saved run and completed reviews."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path

from lab1.documents import export_document
from lab1.report import SCORE_FIELDS, format_check, read_csv, short, table

ROOT = Path(__file__).resolve().parents[1]


def build(run_dir: Path, student: str = "", group: str = "") -> Path:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest.get("status") == "success", "Build the report only from a successful run."
    rows = read_csv(run_dir / "lab1_results.csv")
    scores = read_csv(run_dir / "quality_scores.csv")
    facts = read_csv(run_dir / "hallucination_verification.csv")
    source = (run_dir / "source_text.txt").read_text(encoding="utf-8")
    assert hashlib.sha256(source.encode()).hexdigest() == manifest["source_sha256"]
    assert len(rows) == len(scores) == 26
    assert all(all(1 <= int(row[field]) <= 5 for field in SCORE_FIELDS) for row in scores)
    assert all(sum(item["model"] == model for item in facts) >= 3 for model in manifest["selected_models"])
    assert all(item["status"] != "TO_VERIFY" and item["source_or_url_checked"] for item in facts)

    models = manifest["selected_models"]
    label = {model: short(model) for model in models}
    summaries: list[str] = []

    def add(text: str) -> None:
        summaries.append(text.strip())

    add(f"""# Lab Report 1

**ITMO University**  
**Course:** Prompt Engineering  
**Topic:** Connecting to language models through the Cloud.ru-compatible API, prompt experiments, and factuality review  
**Student:** {student or '____________________'}  
**Group:** {group or '____________________'}  
**Run date (UTC):** {manifest['run_date']}  
**Run ID:** `{manifest['run_id']}`

This report documents a paired experiment that compared {label[models[0]]} and {label[models[1]]} on 13 prompts about retrieval-augmented generation (RAG). Both models completed all 26 requests, and all six output-format checks passed. Manual review also found citation and date errors in selected external claims, showing why fluent answers and plausible references still require verification.

## 1. Objective

The objectives were to connect to two language models through an OpenAI-compatible API, compare their responses to identical prompts, test prompt wording and output formats, check whether models respect a supplied source, and review verifiable factual claims.

## 2. Models and experiment settings

The selected models were `{models[0]}` and `{models[1]}`. Both were called through `{manifest['base_url']}` using profile `{manifest.get('api_profile', 'cloudru')}`. The API key value was not stored in the results. The provider listed {manifest['available_models_count']} model identifiers for the key; availability in that list does not by itself prove that every model supports text generation.

| Setting | Value |
| --- | --- |
| Python | {manifest['python_version']} |
| OpenAI SDK | {manifest['packages']['openai']} |
| python-dotenv | {manifest['packages']['python-dotenv']} |
| requests | {manifest['packages']['requests']} |
| Temperature | {manifest['temperature']} for prompts; {manifest['connection_temperature']} for connection checks |
| Maximum completion budget | {manifest['max_tokens']} tokens per request |
| Timeout | {manifest['timeout_seconds']} seconds; SDK retries: {manifest['sdk_max_retries']} |
| Streaming | Disabled |
| Repetitions | One answer per model and prompt |
| Request order | Paired requests; the first model alternated between prompts |
| Main answers | {len(rows)} (13 prompts × 2 models) |

Model-specific request options were `{json.dumps(manifest.get('model_request_options', {}), ensure_ascii=False)}`. A shared maximum token budget does not imply shared tokenization, internal computation, or cost. The comparison describes only observed behavior under this run's settings.

## 3. Source text

The experiment used the prepared teaching text **{manifest['source_title']}**, containing {manifest['source_word_count']} whitespace-separated words. It covers a RAG pipeline, retrieval and chunking choices, reliability limits, evaluation, and security. It does not identify the authors or year of RAG, which makes it suitable for testing whether models respect a source boundary. External factual claims were checked against primary sources in Section 8.
""")
    add("\n\n".join(" ".join(part.splitlines()) for part in source.strip().split("\n\n")))

    add("""## 4. Procedure and prompt experiments

### 4.1. Connection check

Each model received the same short connection prompt. The client saved the full response, request latency, finish reason, and available token usage.
""")
    add(table(
        ["Model", "Response", "Latency (s)", "Finish reason"],
        [[label[row["model"]], repr(row["output"]), row["latency_seconds"], row["finish_reason"]]
         for row in manifest["connection_checks"]],
    ))

    add("""### 4.2. Identical explanation prompt

Both models were asked to explain RAG to a second-year software engineering student in no more than 120 words and include a practical example.
""")
    explanation = [row for row in rows if row["task"] == "task_2"]
    add(table(["Model", "Words", "Observation"], [
        [label[row["model"]], row["word_count"],
         "Includes a practical company-chatbot example; its wording about reducing hallucinations overstates the guarantee." if row["model"] == models[0] else
         "Includes an HR-chatbot example; the claim that RAG prevents hallucinations is too absolute."]
        for row in explanation
    ]))

    add("""### 4.3. Summary prompts

Five instructions elicited a short summary, five main points, a recap for a busy engineer, a hierarchical outline, and practical takeaways. Each prompt included the same source text.
""")
    summary_rows = []
    for variant in ("summary", "main_points", "short_recap", "outline", "takeaways"):
        pair = sorted(
            (row for row in rows if row["task"] == "task_3" and row["variant"] == variant),
            key=lambda row: models.index(row["model"]),
        )
        summary_rows.append([
            variant,
            pair[0]["prompt"].splitlines()[0],
            pair[0]["word_count"],
            pair[1]["word_count"],
            "Both stayed within the explicit 80-word maximum." if variant == "summary" else
            "Both returned five numbered points." if variant == "main_points" else
            "No numeric word limit was specified; one response per model is not enough to infer a stable preference.",
        ])
    add(table(["Variant", "Instruction", label[models[0]] + " words", label[models[1]] + " words", "Observation"], summary_rows))

    add("""### 4.4. Source-bound questions

The three questions tested a directly stated fact, an inference from the text, and information intentionally absent from the text. The common instruction required answers to use only the source and specified an exact response for unavailable information.
""")
    for variant, title in (("direct", "Direct question"), ("inference", "Inference question"), ("unavailable", "Unavailable fact")):
        pair = [row for row in rows if row["task"] == "task_4" and row["variant"] == variant]
        add(f"**{title}:** {pair[0]['prompt'].splitlines()[0]}")
        add(table(["Model", "Answer"], [[label[row["model"]], row["output"]] for row in pair]))
    add("Both models identified cosine similarity, gave a relevant explanation for the inference question, and returned the requested exact abstention for the absent fact. These few cases do not establish general reliability.")

    add("""### 4.5. Output-format comparison

The same four aspects—purpose, retrieval process, reliability limitations, and security—were requested as one paragraph, exactly four ordered bullets, and JSON with four string fields. A structural checker validated paragraph shape, bullet count, and JSON keys and value types.
""")
    format_rows = [row for row in rows if row["task"] == "task_5"]
    passed = sum(format_check(row) for row in format_rows)
    add(table(["Model", "Format", "Structure check", "Words"], [
        [label[row["model"]], row["variant"], "Passed" if format_check(row) else "Failed", row["word_count"]]
        for row in format_rows
    ]))
    add(f"The structural checker passed {passed} of 6 outputs. Format compliance is separate from factual correctness.")

    add("""### 4.6. Factuality probe

Each model was asked for six concise, verifiable claims about RAG, including dates, numbers, technology names, author names, exact titles, and primary-source URLs. Claims had to be labelled as supported by the supplied text or external to it. Three selected external claims per model were checked against primary sources and are listed in Section 8.

### 4.7. Manual quality scoring

Each answer received a 1–5 score for accuracy, completeness, clarity, instruction following, structure, and verifiability. These are reviewer judgments for this run, not model-generated scores or independent expert certification. A score of 5 means no material issue was found; 3 indicates a noticeable limitation; 1 means the response was unusable. Completeness was judged relative to the task, so a correct abstention can receive a high score.

## 5. Results

The reported `words` value uses the runner's Unicode-aware counter, which treats numbers as words and preserves internal hyphens and apostrophes. Character counts include spaces and line breaks. Latency is the total client request time, not time to first token.
""")
    add(table(
        ["Model", "Prompt", "Latency (s)", "Characters", "Words", "Completion tokens", "Finish"],
        [[label[row["model"]], row["task"] + "/" + row["variant"], row["latency_seconds"],
          row["length_chars"], row["word_count"], row["completion_tokens"], row["finish_reason"]]
         for row in rows],
    ))
    aggregate = []
    for model in models:
        subset = [row for row in rows if row["model"] == model]
        times = [float(row["latency_seconds"]) for row in subset]
        aggregate.append([
            label[model], len(subset), f"{statistics.mean(times):.3f}",
            f"{statistics.median(times):.3f}",
            sum(row["finish_reason"] == "length" for row in subset),
            sum(bool(row["error"]) for row in subset),
        ])
    add(table(["Model", "Answers", "Mean (s)", "Median (s)", "Truncated", "API errors"], aggregate))
    add("Latency values reflect this API service and one run; they are not a general speed ranking. No request failed or ended because of the token limit.")
    add(table(
        ["Model", "Prompt", "Numbers", "Years", "URLs", "Caution markers", "Confidence markers"],
        [[label[row["model"]], row["task"] + "/" + row["variant"], row["number_count"],
          row["year_count"], row["link_count"], row["caution_marker_count"], row["confident_marker_count"]]
         for row in rows if row["task"] == "task_6" or row["variant"] == "unavailable"],
    ))
    add("The lexical counters record occurrences, not unique claims or semantic certainty. Numbers may come from numbering or URLs; terms such as `may` can have multiple meanings, and negation is not interpreted.")

    add("""## 6. Quality review

Scores below are the completed human review of the 26 saved answers. For external factual claims, accuracy and verifiability judgments are limited to the selected checks in Section 8.
""")
    task_comments = {
        "identical_explanation": "Clear explanation and example, but the claim that RAG prevents or reduces hallucinations overstates its guarantee.",
        "summary": "Within the 80-word limit and covers the source's main pipeline, limitations, and safeguards.",
        "main_points": "Five organized points cover the main design and reliability themes.",
        "short_recap": "Useful technical recap grounded in the source; no numeric limit was set.",
        "outline": "Hierarchical structure captures the main concepts; no numeric limit was set.",
        "takeaways": "Practical takeaways reflect the supplied material; no numeric limit was set.",
        "direct": "Correctly identifies cosine similarity, which the source names.",
        "inference": "Relevant explanation of inspectability and why RAG does not guarantee truth.",
        "unavailable": "Returns the exact abstention phrase required by the prompt.",
        "plain_text": "One paragraph covers all four requested aspects.",
        "list": "Exactly four ordered bullets cover the requested aspects.",
        "json": "Valid JSON with the four required string fields and no wrapper text.",
        "fact_probe": "Six claims follow the requested format; selected external claims contain citation or date problems noted in Section 8.",
    }
    add(table(
        ["Model", "Prompt", "Accuracy", "Completeness", "Clarity", "Instruction", "Structure", "Verifiability", "Comment"],
        [[label[row["model"]], row["task"] + "/" + row["variant"],
          *[row[field] for field in SCORE_FIELDS], task_comments[row["variant"]]]
         for row in scores],
    ))
    add("Both models followed the tested source boundary and passed the format checks. Their RAG explanations were clear but overstated hallucination reduction. Selected external claims from both models included citation or date errors. These scores describe one reviewed run and do not establish an overall model ranking.")

    add("""## 7. Fact verification and hallucination review

“External to the supplied text” does not mean “false.” Each selected claim was compared with its cited primary source. A real URL does not automatically support every nearby statement, so the title, date, identifier, and exact claim were checked.
""")
    verdicts = {
        "Дата ошибочна": "Incorrect date",
        "Подтверждено": "Supported",
        "Подтверждено с уточнением": "Supported with qualification",
        "Ссылка не подтверждена": "URL not verified",
        "Неверная ссылка и дата": "Incorrect URL and date",
    }
    fact_comments = {
        "Дата ошибочна": "arXiv gives the first submission date as 22 May 2020 UTC, not 23 May. The title and authors otherwise match.",
        "Подтверждено": "The arXiv record confirms the title, authors, identifier, and first submission date of 17 October 2023.",
        "Ссылка не подтверждена": "The supplied URL could not be accessed. The official deepset page for this article uses a different URL and names Isabelle Nguyen as author; do not rely on the generated URL.",
        "Подтверждено с уточнением": "arXiv confirms the title, authors, and 2020 record. The paper presents specific RAG models; it does not establish that it originated all retrieval-augmentation methods.",
        "Неверная ссылка и дата": "The cited identifier points to an unrelated physics paper. REPLUG is arXiv:2301.12652, submitted on 30 January 2023; its title and authors match the corrected record.",
    }
    fact_rows = []
    for item in facts:
        url = item["source_or_url_checked"]
        fact_rows.append([
            label[item["model"]], item["candidate_claim"], f"[Primary source]({url})",
            verdicts.get(item["status"], item["status"]), fact_comments[item["status"]],
        ])
    add(table(["Model", "Claim reviewed", "Primary source", "Verdict", "Finding"], fact_rows))
    add("The review found a one-day date error and an inaccessible citation among Kimi's selected claims, and an unrelated arXiv identifier and incorrect date for Gemini's REPLUG claim. Other selected claims were supported or required a scope qualification. Six selected claims do not estimate either model's overall factual error rate.")

    add("""## 8. Conclusions and limitations

1. **Run completion.** Both models completed all 13 prompts, producing 26 responses with no API errors or truncation.
2. **Prompt compliance.** Both met the explicit 80-word summary limit and the 120-word explanation limit in this run.
3. **Format control.** All six paragraph, list, and JSON responses passed the structural checks.
4. **Source boundary.** Both returned the specified abstention when asked for information absent from the source.
5. **External claims.** Manual checks found date and citation issues in selected claims from both models.
6. **Limits.** One answer per prompt, reviewer-scored quality, and six selected external claims do not support statistical claims or a universal ranking.

The source text, model outputs, settings, package versions, and code hashes are saved with the run. Repeating the prompts may not reproduce identical wording because models and the service can change. Prompt variants also change multiple aspects of the instruction, so the effect of one word or formatting choice cannot be isolated. Length and latency are useful measurements, but they do not replace content review.

The collection status `success` means the requests completed technically; it does not mean every answer is factually correct. Report materials are in `{run_dir.as_posix()}/`. Rebuild all report formats without API calls with:

```powershell
python -m pip install -r requirements-report.txt
python -m lab1.report_en --run-dir {run_dir.as_posix()}
```

## Appendix A. Models available to the API key

The endpoint returned {manifest['available_models_count']} identifiers when the run was made. Availability does not guarantee text-generation support for every identifier.
""")
    add("```text\n" + "\n".join(manifest["available_models"]) + "\n```\n\n## Appendix B. Prompts and complete model responses\n\nThe following appendix reproduces all 26 saved answers without editing their content. Repeated source text in the prompts is replaced by a reference to Section 3; complete prompts are retained in the CSV results.")
    for number, row in enumerate(rows, 1):
        prompt = row["prompt"].replace(source, "[Full source text from Section 3]")
        add(
            f"### B.{number}. {label[row['model']]} — {row['task']}/{row['variant']}\n\n"
            f"**Prompt:**\n\n```text\n{prompt}\n```\n\n"
            f"**Response:** {row['latency_seconds']} s; {row['word_count']} words; `{row['finish_reason']}`.\n\n"
            f"```text\n{row['output']}\n```"
        )

    target = ROOT / "reports/lab1/LAB1_REPORT_EN.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n\n".join(summaries) + "\n", encoding="utf-8")
    export_document(target, language="en")
    print(f"Wrote {target.name}, HTML, and DOCX from run {manifest['run_id']}.")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--student", default="")
    parser.add_argument("--group", default="")
    args = parser.parse_args()
    build(args.run_dir, args.student, args.group)


if __name__ == "__main__":
    main()
