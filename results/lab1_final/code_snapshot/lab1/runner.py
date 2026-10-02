"""Run all Prompt Engineering Lab 1 tasks with resumable, timestamped outputs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import csv
import json
import platform
import re
import sys
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

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
    "information is unavailable",
    "not specified",
    "not supported",
    "may",
    "might",
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
    max_tokens: int = 0
    temperature: float = 0.2
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


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
    started = time.perf_counter()
    try:
        request_options: dict[str, Any] = {}
        if model == "moonshotai/Kimi-K2.6":
            request_options["extra_body"] = {"thinking": {"type": "disabled"}}
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
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
            round(time.perf_counter() - started, 3),
            finish_reason=response.choices[0].finish_reason or "",
            reasoning=reasoning,
            max_tokens=max_tokens,
            temperature=temperature,
            prompt_tokens=getattr(getattr(response, "usage", None), "prompt_tokens", None),
            completion_tokens=getattr(getattr(response, "usage", None), "completion_tokens", None),
            total_tokens=getattr(getattr(response, "usage", None), "total_tokens", None),
        )
    except Exception as exc:
        return Result(
            task,
            variant,
            model,
            prompt,
            "",
            round(time.perf_counter() - started, 3),
            # Avoid persisting provider exception bodies, which may echo secrets.
            f"{type(exc).__name__} (HTTP {getattr(exc, 'status_code', 'n/a')})",
            max_tokens=max_tokens,
            temperature=temperature,
        )


def marker_count(text: str, markers: tuple[str, ...]) -> int:
    return sum(len(re.findall(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", text)) for marker in markers)


def metrics(text: str) -> dict[str, Any]:
    lower = text.lower()
    return {
        "length_chars": len(text),
        "length_words": len(re.findall(r"\b\w+\b", text, re.UNICODE)),
        "word_count": len(re.findall(r"[^\W_]+(?:[-'’][^\W_]+)*", text, re.UNICODE)),
        "number_count": len(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", text)),
        "year_count": len(re.findall(r"\b(?:19|20)\d{2}\b", text)),
        "link_count": len(re.findall(r"https?://\S+", text)),
        "caution_marker_count": marker_count(lower, CAUTION_MARKERS),
        "confident_marker_count": marker_count(lower, CONFIDENT_MARKERS),
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
        "max_tokens": result.max_tokens,
        "temperature": result.temperature,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "total_tokens": result.total_tokens,
    }
    data.update(metrics(result.output))
    return data


def experiment_prompts() -> list[tuple[str, str, str]]:
    prompts = [("task_2", "identical_explanation",
        "Explain the concept of retrieval-augmented generation to a second-year "
        "software engineering student in 120 words or fewer. Include one practical example.")]
    summaries = {
        "summary": "Summarize the source in no more than 80 words.",
        "main_points": "Extract the five main points from the source.",
        "short_recap": "Briefly retell the source for a busy engineer.",
        "outline": "Create a concise hierarchical outline of the source.",
        "takeaways": "List the most useful practical takeaways from the source.",
    }
    for variant, instruction in summaries.items():
        prompts.append(("task_3", variant, f"{instruction}\nUse only the source below.\n\n{SOURCE_TEXT}"))
    questions = {
        "direct": "According to the source, which similarity measure can a vector index use?",
        "inference": "Why can RAG improve inspectability while not guaranteeing truth?",
        "unavailable": "According to the source, who invented RAG and in what year?",
    }
    for variant, question in questions.items():
        prompts.append(("task_4", variant,
            f'{question}\nAnswer only from the source. If the source does not contain '
            f'the answer, reply exactly: The information is unavailable.\n\n{SOURCE_TEXT}'))
    shared = (
        "Describe exactly these four aspects of RAG: purpose, retrieval process, "
        "reliability limitations, and security requirements. Keep the same scope "
        "for all four aspects and use only the source below. "
    )
    formats = {
        "plain_text": "Return one paragraph covering all four aspects.",
        "list": "Return exactly four bullet points, one per aspect in the given order.",
        "json": 'Return valid JSON only, with exactly four string keys: "purpose", '
                '"retrieval", "limitations", and "security". No Markdown fences or extra text.',
    }
    for variant, instruction in formats.items():
        prompts.append(("task_5", variant, f"{shared}{instruction}\n\n{SOURCE_TEXT}"))
    prompts.append(("task_6", "fact_probe",
        "Write six concise, numbered, verifiable factual claims about RAG. "
        "Across the claims include publication dates, numbers, technology names, "
        "author names, exact document titles, and URLs. Include at least three "
        "claims about named research papers or documented tools, with a primary "
        "source URL for each. Label every claim either SUPPORTED BY THE SUPPLIED "
        "TEXT or EXTERNAL TO THE SUPPLIED TEXT. External knowledge is allowed, "
        "but say when you are uncertain; do not invent references or present "
        "illustrative numerical settings as universal defaults. Keep the answer "
        "within 450 words. The supplied text is:\n\n" + SOURCE_TEXT))
    return prompts


def run(config: LabConfig, client: OpenAI, selected_models: list[str], *,
        output_dir: Path | None = None, progress: bool = False,
        resume: bool = False) -> dict[str, Any]:
    if len(selected_models) != 2 or len(set(selected_models)) != 2:
        raise ValueError("Select exactly two different models.")
    if config.max_tokens <= 0 or config.timeout <= 0:
        raise ValueError("Token budget and timeout must be positive.")
    available_models = list_models(client)
    if any(model not in available_models for model in selected_models):
        raise ValueError("A selected model is absent from the available-model list.")
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    destination = Path(output_dir) if output_dir is not None else OUTPUT_DIR / "runs" / run_id
    existing_manifest_path = destination / "manifest.json"
    if resume:
        if not existing_manifest_path.is_file():
            raise ValueError("Resume requires an existing run folder with a manifest.")
        old_manifest = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        if old_manifest.get("status") == "success":
            raise ValueError("A successful run cannot be resumed.")
        if old_manifest.get("selected_models") != selected_models or old_manifest.get("max_tokens") != config.max_tokens or old_manifest.get("source_sha256") != hashlib.sha256(SOURCE_TEXT.encode()).hexdigest():
            raise ValueError("Resume configuration or source does not match the saved run.")
        run_id = old_manifest["run_id"]
        start_text = old_manifest["started_at_utc"]
        started = datetime.fromisoformat(start_text)
        manifest = old_manifest
        saved = destination / "lab1_results.csv"
        if saved.exists():
            with saved.open(encoding="utf-8-sig", newline="") as handle:
                results = list(csv.DictReader(handle))
        else:
            results = []
        saved_checks = destination / "connection_checks.csv"
        if saved_checks.exists():
            with saved_checks.open(encoding="utf-8-sig", newline="") as handle:
                connection_checks = list(csv.DictReader(handle))
        else:
            connection_checks = []
    else:
        # An existing folder is never reused, even if it contains partial results.
        destination.mkdir(parents=True, exist_ok=False)
        results = []
        connection_checks = []
        manifest = {}
    snapshot = destination / "code_snapshot"
    snapshot.mkdir(exist_ok=resume)
    hashes = {}
    for relative in ("lab1/runner.py", "lab1/source_text.py", "labs/common.py", "requirements.txt"):
        content = (ROOT / relative).read_bytes()
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        hashes[relative] = hashlib.sha256(content).hexdigest()
    (destination / "source_text.txt").write_text(SOURCE_TEXT, encoding="utf-8")
    if resume:
        if manifest.get("code_sha256") != hashes:
            raise ValueError("Resume code snapshot differs; start a new run instead.")
        manifest["resume_count"] = manifest.get("resume_count", 0) + 1
        manifest.setdefault("resume_started_at_utc", []).append(datetime.now(timezone.utc).isoformat())
        manifest["status"] = "running"
    else:
        manifest = {
        "run_id": run_id, "run_date": started.date().isoformat(),
        "started_at_utc": started.isoformat(), "status": "running",
        "output_dir": str(destination.resolve()), "base_url": config.base_url,
        "selected_models": selected_models, "available_models_count": len(available_models),
        "available_models": available_models, "source_title": SOURCE_TITLE,
        "source_word_count": len(SOURCE_TEXT.split()),
        "source_sha256": hashlib.sha256(SOURCE_TEXT.encode()).hexdigest(),
        "code_sha256": hashes, "python_version": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in ("openai", "python-dotenv", "requests")},
        "max_tokens": config.max_tokens, "temperature": 0.2,
        "connection_temperature": 0.0, "timeout_seconds": config.timeout,
        "sdk_max_retries": 1, "stream": False, "repetitions": 1,
        "model_request_options": {m: ({"thinking": {"type": "disabled"}} if m == "moonshotai/Kimi-K2.6" else {}) for m in selected_models},
        "request_order": "Paired by prompt; first model alternates between pairs.",
        "manual_verification_required": True,
        "metrics_version": 2,
        "word_count_definition": "Unicode alphanumeric groups, preserving internal hyphens and apostrophes; numbers included.",
        }

    def checkpoint() -> None:
        write_csv(destination / "lab1_results.csv", results)
        write_csv(destination / "lab1_results_with_metrics.csv", results)
        write_csv(destination / "connection_checks.csv", connection_checks)
        manifest["connection_checks"] = connection_checks
        manifest["result_rows"] = len(results)
        temporary = destination / "manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(destination / "manifest.json")

    def request(model: str, task: str, variant: str, prompt: str, temperature: float) -> dict[str, Any]:
        if progress:
            print(f"{task}/{variant}: {model}", file=sys.stderr, flush=True)
        result = row(call(client, model, task, variant, prompt,
                          max_tokens=config.max_tokens, temperature=temperature))
        if progress:
            print(f"  {result['latency_seconds']}s; finish={result['finish_reason']}; "
                  f"words={result['word_count']}; error={result['error'] or 'none'}", file=sys.stderr, flush=True)
        return result

    checkpoint()
    for model in selected_models:
        if any(r["model"] == model and not r["error"] and r["output"].strip() for r in connection_checks):
            continue
        connection_checks[:] = [r for r in connection_checks if r["model"] != model]
        connection_checks.append(request(model, "task_1", "connection_check",
                                         "Reply with exactly: connection verified.", 0.0))
        checkpoint()
    # Failed/empty connectivity prevents an expensive batch of doomed requests.
    if all(not r["error"] and r["output"].strip() for r in connection_checks):
        for index, (task, variant, prompt) in enumerate(experiment_prompts()):
            order = selected_models if index % 2 == 0 else selected_models[::-1]
            for model in order:
                previous = next((r for r in results if r["model"] == model and r["task"] == task and r["variant"] == variant), None)
                if previous is not None and not previous["error"] and previous["output"].strip() and previous["finish_reason"] == "stop":
                    continue
                results[:] = [r for r in results if not (r["model"] == model and r["task"] == task and r["variant"] == variant)]
                results.append(request(model, task, variant, prompt, 0.2))
                checkpoint()
    all_rows = connection_checks + results
    manifest["error_count"] = sum(bool(r["error"]) for r in all_rows)
    manifest["empty_count"] = sum(not r["output"].strip() for r in all_rows)
    manifest["truncated_count"] = sum(r["finish_reason"] == "length" for r in all_rows)
    manifest["unexpected_finish_count"] = sum(r["finish_reason"] != "stop" for r in all_rows)
    if manifest["error_count"] or manifest["empty_count"]:
        manifest["status"] = "failed"
    elif manifest["unexpected_finish_count"] or len(results) != 26:
        manifest["status"] = "incomplete"
    else:
        manifest["status"] = "success"
    manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    preserve_review(destination / "hallucination_verification.csv",
        hallucination_template(r for r in results if r["task"] == "task_6"),
        ("model", "claim_number"),
        ("candidate_claim", "source_or_url_checked", "status", "comment"))
    preserve_review(destination / "quality_scores.csv", quality_template(results),
        ("model", "task", "variant"),
        ("accuracy_1_5", "completeness_1_5", "clarity_1_5",
         "instruction_following_1_5", "structure_1_5", "verifiability_1_5", "comment"))
    checkpoint()
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


def preserve_review(path: Path, generated: list[dict[str, Any]], key_fields: tuple[str, ...],
                    review_fields: tuple[str, ...]) -> None:
    """Refresh a review CSV without discarding student-entered annotations."""
    previous = {}
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            previous = {tuple(row.get(key, "") for key in key_fields): row
                        for row in csv.DictReader(handle)}
    merged = []
    for row in generated:
        old = previous.get(tuple(str(row.get(key, "")) for key in key_fields), {})
        merged.append({**row, **{field: old[field] for field in review_fields
                                 if old.get(field, "") not in ("", "TO_VERIFY")}})
    write_csv(path, merged)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs=2, metavar=("MODEL_A", "MODEL_B"))
    parser.add_argument("--max-tokens", type=int, help="Same completion budget for both models; defaults to LAB_MAX_TOKENS.")
    parser.add_argument("--output-dir", type=Path, help="New output directory; existing directories are never overwritten.")
    parser.add_argument("--resume", action="store_true", help="Resume failed or interrupted requests in --output-dir.")
    args = parser.parse_args()
    try:
        config = load_config()
        if args.max_tokens is not None:
            config = replace(config, max_tokens=args.max_tokens)
        client = make_client(config)
        selected = list(args.models or config.models)
        manifest = run(config, client, selected, output_dir=args.output_dir, progress=True, resume=args.resume)
        print(json.dumps({k: manifest[k] for k in ("status", "output_dir", "result_rows", "error_count", "truncated_count")}, ensure_ascii=False, indent=2))
        if manifest["status"] != "success":
            raise SystemExit(1)
    except Exception as exc:
        print(f"Lab 1 could not run: {type(exc).__name__}. Check configuration, connectivity, and the selected output directory.", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
