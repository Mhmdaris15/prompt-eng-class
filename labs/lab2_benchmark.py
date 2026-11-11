"""Labs 1-2: prompt variants, QA, formats, and automated metrics."""

from __future__ import annotations

from labs.common import OUTPUT_DIR, complete, load_config, make_client, metrics, write_csv
from labs.corpus import TECHNICAL_TEXT


SUMMARY_PROMPTS = {
    "summary": "Summarize the source in 80 words.",
    "main_points": "Extract the five most important points from the source.",
    "shorten": "Rewrite the source as a concise executive brief.",
    "outline": "Create a brief hierarchical outline of the source.",
    "takeaways": "List the key takeaways for a software engineer.",
}

QUESTIONS = {
    "direct_fact": "According to the source, what similarity measure can a vector index use?",
    "inference": "Why can RAG improve inspectability while still failing to guarantee truth?",
    "out_of_context": "What was the exact stock price of NVIDIA on 15 March 2024?",
}

FORMATS = {
    "plain_text": "Answer in one plain-text paragraph.",
    "bullets": "Answer as exactly four bullet points.",
    "structured": "Answer as a Markdown table with columns Claim and Evidence.",
}


def run() -> None:
    config = load_config()
    client = make_client(config)
    rows: list[dict[str, object]] = []
    for model in config.models:
        for name, instruction in SUMMARY_PROMPTS.items():
            prompt = f"{instruction}\nUse only this source:\n{TECHNICAL_TEXT}"
            result = complete(client, model, prompt, max_tokens=config.max_tokens)
            rows.append(_row("summarization", name, model, result))
        for name, question in QUESTIONS.items():
            prompt = (
                f"{question}\nUse only the source below. If the source does not "
                f"contain the answer, explicitly say that it is unavailable.\n{TECHNICAL_TEXT}"
            )
            rows.append(_row("qa", name, model, complete(client, model, prompt, max_tokens=300)))
        for name, format_instruction in FORMATS.items():
            prompt = (
                f"{format_instruction}\nUse only this source and explain the "
                f"main purpose of RAG.\n{TECHNICAL_TEXT}"
            )
            rows.append(_row("format", name, model, complete(client, model, prompt, max_tokens=300)))

    write_csv(OUTPUT_DIR / "results.csv", rows)
    write_csv(OUTPUT_DIR / "results_with_metrics.csv", rows)
    print(f"Wrote {len(rows)} benchmark rows to {OUTPUT_DIR}")


def _row(category: str, variant: str, model: str, result) -> dict[str, object]:
    row: dict[str, object] = {
        "category": category,
        "variant": variant,
        "model": model,
        "prompt": result.prompt,
        "output": result.output,
        "latency_seconds": result.latency_seconds,
        "error": result.error,
    }
    row.update(metrics(result.output))
    return row


if __name__ == "__main__":
    run()
