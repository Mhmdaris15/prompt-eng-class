"""Shared OpenAI-compatible client utilities for Cloud.ru and the course API."""

from __future__ import annotations

import csv
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

from dotenv import dotenv_values
from openai import OpenAI
import requests


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "results"
BASE_URL = "https://foundation-models.api.cloud.ru/v1"
COURSE_BASE_URL = "https://proxy-prompts.aiclab.tech/v1"
DEFAULT_MODELS = ("moonshotai/Kimi-K2.6", "Qwen/Qwen3-Coder-Next")
COURSE_DEFAULT_MODELS = ("Qwen/Qwen3-30B-A3B", "GigaChat/GigaChat-3-Pro")


@dataclass(frozen=True)
class LabConfig:
    api_key: str
    base_url: str
    models: tuple[str, str]
    embedding_model: str
    max_tokens: int
    timeout: float
    profile: str = "cloudru"


@dataclass
class CompletionResult:
    model: str
    prompt: str
    output: str
    latency_seconds: float
    error: str = ""
    finish_reason: str = ""
    reasoning: str = ""


def load_config(profile: str | None = None) -> LabConfig:
    """Load a named API profile; credentials and endpoints stay profile-specific."""
    values = dotenv_values(ROOT / ".env")

    def get(name: str, default: str = "") -> str:
        return os.getenv(name) or values.get(name) or default

    selected_profile = (profile or get("LAB_API_PROFILE", "cloudru")).strip().lower()
    if selected_profile == "cloudru":
        api_key_name = "API_KEY"
        api_key = get(api_key_name)
        base_url = get("FOUNDATION_MODELS_BASE_URL", BASE_URL)
        model_a = get("LAB_MODEL_A", DEFAULT_MODELS[0])
        model_b = get("LAB_MODEL_B", DEFAULT_MODELS[1])
        max_tokens = int(get("LAB_MAX_TOKENS", "2048"))
        timeout = float(get("LAB_TIMEOUT", "180"))
    elif selected_profile == "course":
        api_key_name = "COURSE_API_KEY"
        api_key = get(api_key_name)
        base_url = get("COURSE_API_BASE_URL", COURSE_BASE_URL)
        model_a = get("COURSE_MODEL_A", COURSE_DEFAULT_MODELS[0])
        model_b = get("COURSE_MODEL_B", COURSE_DEFAULT_MODELS[1])
        max_tokens = int(get("COURSE_MAX_TOKENS", "2048"))
        timeout = float(get("COURSE_TIMEOUT", "180"))
    else:
        raise ValueError("LAB_API_PROFILE must be 'cloudru' or 'course'.")

    if not api_key or api_key in {
        "your_api_key_here",
        "your_cloud_ru_api_key_here",
        "your_course_api_key_here",
        "sk-bf-ВАШ-КЛЮЧ",
    }:
        raise RuntimeError(
            f"{api_key_name} is not configured. Add it to the project .env file."
        )
    return LabConfig(
        api_key=api_key,
        base_url=base_url,
        models=(model_a, model_b),
        embedding_model=get("LAB_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B"),
        max_tokens=max_tokens,
        timeout=timeout,
        profile=selected_profile,
    )


def make_client(config: LabConfig) -> OpenAI:
    client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
        max_retries=1,
    )
    client._lab_api_profile = config.profile
    return client


def _usage_url(base_url: str) -> str:
    """Build the course API's host-level /usage URL from its OpenAI /v1 URL."""
    parts = urlsplit(base_url.rstrip("/"))
    path = parts.path[:-3] if parts.path.endswith("/v1") else parts.path
    return urlunsplit((parts.scheme, parts.netloc, path.rstrip("/") + "/usage", "", ""))


def course_usage(client: OpenAI) -> dict[str, Any]:
    """Read allowed models and quota metadata from the course API's /usage route."""
    response = requests.get(
        _usage_url(str(client.base_url)),
        headers={"Authorization": f"Bearer {client.api_key}"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Course API /usage returned an unexpected response.")
    return payload


def list_models(client: OpenAI) -> list[str]:
    """Return models available to the configured key on the selected endpoint."""
    if getattr(client, "_lab_api_profile", "cloudru") == "course":
        payload = course_usage(client)
        client._lab_usage_payload = payload
        models = {
            name
            for provider in payload.get("provider_configs", [])
            for name in provider.get("allowed_models", [])
            if isinstance(name, str)
        }
        if not models:
            raise RuntimeError("Course API /usage did not return any allowed models.")
        return sorted(models)
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
