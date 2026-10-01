"""Run all tasks from Prompt Engineering Laboratory 1.

The runner is deliberately deterministic in its inputs and records raw model
outputs so that qualitative judgments can be made from evidence, not memory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from openai import OpenAI

from labs.common import LabConfig, list_models, load_config, make_client, write_csv
from lab1.source_text import SOURCE_TEXT, SOURCE_TITLE


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "results" / "lab1"
CAUTION_MARKERS = (
    "возможно",
    "вероятно",
    "нужно уточнить",
    "недостаточно данных",
    "требуется проверка",
    "insufficient information",
    "cannot determine",
    "uncertain",
)
CONFIDENT_MARKERS = (
    "точно",
    "однозначно",
    "безусловно",
    "гарантированно",
    "definitely",
    "certainly",
    "guaranteed",
)


@dataclass
class Result:
    task: str
    variant: str
    model: str
    prompt: str
    output: str
    latency_seconds: float
    error: str = ""
    finish_reason: str = ""
    reasoning: str = ""


def call(
    client: OpenAI,
    model: str,
    task: str,
    variant: str,
    prompt: str,
    *,
    max_tokens: int,
    temperature: float = 0.2,
) -> Result:
    started = time.time()
    try:
        effective_max_tokens = max_tokens
        if model == "moonshotai/Kimi-K2.6":
            # Cloud.ru exposes Kimi's reasoning tokens within the completion
            # budget. Keep enough budget for both reasoning and final content.
            effective_max_tokens = max(max_tokens, 8192 if task == "task_6" else 4096)
        request_options: dict[str, Any] = {}
        if model == "moonshotai/Kimi-K2.6":
            request_options["extra_body"] = {"thinking": {"type": "disabled"}}
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=effective_max_tokens,
            temperature=temperature,
            stream=False,
            **request_options,
        )
        message = response.choices[0].message
        output = message.content or ""
        reasoning = getattr(message, "reasoning", "") or getattr(
            message, "reasoning_content", ""
        ) or ""
        return Result(
            task,
            variant,
            model,
            prompt,
            output,
            round(time.time() - started, 3),
            finish_reason=response.choices[0].finish_reason or "",
            reasoning=reasoning,
        )
    except Exception as exc:
        return Result(
            task,
            variant,
            model,
            prompt,
            "",
            round(time.time() - started, 3),
            f"{type(exc).__name__}: {exc}",
        )


def metrics(text: str) -> dict[str, Any]:
    lower = text.lower()
    return {
        "length_chars": len(text),
        "length_words": len(re.findall(r"\b\w+\b", text, re.UNICODE)),
        "number_count": len(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", text)),
        "year_count": len(re.findall(r"\b(?:19|20)\d{2}\b", text)),
        "link_count": len(re.findall(r"https?://\S+", text)),
        "caution_marker_count": sum(lower.count(marker) for marker in CAUTION_MARKERS),
        "confident_marker_count": sum(lower.count(marker) for marker in CONFIDENT_MARKERS),
    }


def row(result: Result) -> dict[str, Any]:
    data = {
        "task": result.task,
        "variant": result.variant,
        "model": result.model,
        "prompt": result.prompt,
        "output": result.output,
        "latency_seconds": result.latency_seconds,
        "error": result.error,
        "finish_reason": result.finish_reason,
        "reasoning_length_chars": len(result.reasoning),
    }
    data.update(metrics(result.output))
    return data


def run(config: LabConfig, client: OpenAI, selected_models: list[str]) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    # Task 1: model discovery and equal connection check.
    available_models = list_models(client)
    connection_checks = []
    for model in selected_models:
        result = call(
            client,
            model,
            "task_1",
            "connection_check",
            "Reply with exactly: connection verified.",
            max_tokens=256,
            temperature=0.0,
        )
        connection_checks.append(row(result))

    # Task 2: identical first conceptual explanation prompt.
    first_prompt = (
        "Explain the concept of retrieval-augmented generation to a second-year "
        "software engineering student in 120 words or fewer. Include one practical example."
    )
    for model in selected_models:
        results.append(row(call(client, model, "task_2", "identical_explanation", first_prompt, max_tokens=256)))

    # Task 3: five formulations of the same summarization task.
    summary_prompts = {
        "summary": "Summarize the source in no more than 80 words.",
        "main_points": "Extract the five main points from the source.",
        "short_recap": "Briefly retell the source for a busy engineer.",
        "outline": "Create a concise hierarchical outline of the source.",
        "takeaways": "List the most useful practical takeaways from the source.",
    }
    for model in selected_models:
        for variant, instruction in summary_prompts.items():
            prompt = f"{instruction}\nUse only the source below.\n\n{SOURCE_TEXT}"
            results.append(row(call(client, model, "task_3", variant, prompt, max_tokens=256)))

    # Task 4: direct, inferential, and unavailable-context questions.
    questions = {
        "direct": "According to the source, which similarity measure can a vector index use?",
        "inference": "Why can RAG improve inspectability while not guaranteeing truth?",
        "unavailable": "According to the source, who invented RAG and in what year?",
    }
    for model in selected_models:
        for variant, question in questions.items():
            prompt = (
                f"{question}\nAnswer only from the source. If the source does not "
                f"contain the answer, say exactly that the information is unavailable.\n\n{SOURCE_TEXT}"
            )
            results.append(row(call(client, model, "task_4", variant, prompt, max_tokens=256)))

    # Task 5: equivalent content with three output constraints.
    formats = {
        "plain_text": "Explain the main purpose of RAG in one paragraph.",
        "list": "Explain the main purpose of RAG as exactly four bullet points.",
        "json": (
            "Return valid JSON only with exactly two keys: "
            '"purpose" (string) and "limitations" (array of strings).'
        ),
    }
    for model in selected_models:
        for variant, instruction in formats.items():
            prompt = f"{instruction}\nUse only the source below.\n\n{SOURCE_TEXT}"
            results.append(row(call(client, model, "task_5", variant, prompt, max_tokens=256)))

    # Task 6: deliberately fact-heavy prompt; manual verification is a separate artifact.
    hallucination_prompt = (
        "Write a fact-heavy technical answer about RAG. Include at least three "
        "dates, numbers, technology names, author names, document titles, and URLs. "
        "Clearly label each claim as either supported by the supplied source or "
        "not supported by it. The supplied source is:\n\n" + SOURCE_TEXT
    )
    hallucination_results = []
    for model in selected_models:
        result = call(client, model, "task_6", "fact_probe", hallucination_prompt, max_tokens=512)
        hallucination_results.append(row(result))
        results.append(hallucination_results[-1])

    write_csv(OUTPUT_DIR / "lab1_results.csv", results)
    write_csv(OUTPUT_DIR / "lab1_results_with_metrics.csv", results)
    write_csv(OUTPUT_DIR / "connection_checks.csv", connection_checks)
    write_csv(OUTPUT_DIR / "hallucination_verification.csv", hallucination_template(hallucination_results))
    write_csv(OUTPUT_DIR / "quality_scores.csv", quality_template(results))

    manifest = {
        "run_date": str(date.today()),
        "base_url": config.base_url,
        "selected_models": selected_models,
        "available_models_count": len(available_models),
        "available_models": available_models,
        "source_title": SOURCE_TITLE,
        "source_word_count": len(SOURCE_TEXT.split()),
        "connection_checks": connection_checks,
        "result_rows": len(results),
        "manual_verification_required": True,
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def hallucination_template(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for result in rows:
        for index in range(1, 4):
            output.append(
                {
                    "model": result["model"],
                    "claim_number": index,
                    "candidate_claim": "",
                    "source_or_url_checked": "",
                    "status": "TO_VERIFY",
                    "comment": "Copy a concrete date, number, name, title, URL, or capability claim from the raw output and verify it manually.",
                    "raw_output_file": "lab1_results.csv",
                }
            )
    return output


def quality_template(results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "model": result["model"],
            "task": result["task"],
            "variant": result["variant"],
            "accuracy_1_5": "",
            "completeness_1_5": "",
            "clarity_1_5": "",
            "instruction_following_1_5": "",
            "structure_1_5": "",
            "verifiability_1_5": "",
            "comment": "Fill after reviewing the raw output; do not infer quality from latency alone.",
        }
        for result in results
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs=2, metavar=("MODEL_A", "MODEL_B"))
    args = parser.parse_args()
    try:
        config = load_config()
        client = make_client(config)
        selected = list(args.models or config.models)
        manifest = run(config, client, selected)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"Lab 1 could not run: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
