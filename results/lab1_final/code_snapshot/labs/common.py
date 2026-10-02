"""Shared Cloud.ru OpenAI-compatible client and experiment utilities."""

from __future__ import annotations

import csv
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from dotenv import dotenv_values
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "results"
BASE_URL = "https://foundation-models.api.cloud.ru/v1"
DEFAULT_MODELS = ("moonshotai/Kimi-K2.6", "Qwen/Qwen3-Coder-Next")


@dataclass(frozen=True)
class LabConfig:
    api_key: str
    base_url: str
    models: tuple[str, str]
    embedding_model: str
    max_tokens: int
    timeout: float


@dataclass
class CompletionResult:
    model: str
    prompt: str
    output: str
    latency_seconds: float
    error: str = ""
    finish_reason: str = ""
    reasoning: str = ""


def load_config() -> LabConfig:
    """Load lab configuration without requiring shell environment mutation."""
    values = dotenv_values(ROOT / ".env")

    def get(name: str, default: str = "") -> str:
        return os.getenv(name) or values.get(name) or default

    api_key = get("API_KEY")
    if not api_key or api_key in {"your_api_key_here", "your_cloud_ru_api_key_here"}:
        raise RuntimeError(
            "API_KEY is not configured. Add API_KEY to the project .env file."
        )
    model_a = get("LAB_MODEL_A", DEFAULT_MODELS[0])
    model_b = get("LAB_MODEL_B", DEFAULT_MODELS[1])
    return LabConfig(
        api_key=api_key,
        base_url=get("FOUNDATION_MODELS_BASE_URL", BASE_URL),
        models=(model_a, model_b),
        embedding_model=get("LAB_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B"),
        max_tokens=int(get("LAB_MAX_TOKENS", "2048")),
        timeout=float(get("LAB_TIMEOUT", "180")),
    )


def make_client(config: LabConfig) -> OpenAI:
    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
        max_retries=1,
    )


def list_models(client: OpenAI) -> list[str]:
    """Return model identifiers exposed by the configured endpoint."""
    return sorted(model.id for model in client.models.list().data)


def complete(
    client: OpenAI,
    model: str,
    prompt: str,
    *,
    max_tokens: int,
    temperature: float = 0.2,
    system: str | None = None,
) -> CompletionResult:
    """Run one completion and capture latency and errors instead of aborting a batch."""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    started = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        output = response.choices[0].message.content or ""
        return CompletionResult(
            model=model,
            prompt=prompt,
            output=output,
            latency_seconds=round(time.time() - started, 3),
        )
    except Exception as exc:  # A batch must preserve failures as result rows.
        return CompletionResult(
            model=model,
            prompt=prompt,
            output="",
            latency_seconds=round(time.time() - started, 3),
            error=f"{type(exc).__name__}: {exc}",
        )


def metrics(text: str) -> dict[str, int]:
    """Extract simple, reproducible indicators required by the assignment."""
    caution_words = (
        "возможно",
        "вероятно",
        "недостаточно данных",
        "неизвестно",
        "cannot determine",
        "insufficient information",
        "uncertain",
    )
    lower = text.lower()
    return {
        "response_length_chars": len(text),
        "response_length_words": len(re.findall(r"\b\w+\b", text, re.UNICODE)),
        "number_count": len(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", text)),
        "date_year_count": len(re.findall(r"\b(?:19|20)\d{2}\b", text)),
        "link_count": len(re.findall(r"https?://\S+", text)),
        "caution_marker_count": sum(lower.count(word) for word in caution_words),
    }


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Write UTF-8 with BOM for reliable opening in spreadsheet software."""
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
