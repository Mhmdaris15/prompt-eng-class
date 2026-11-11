"""
Lab 2 Common Utilities
======================
Shared configuration, Cloud.ru client, metrics, and CSV export for Lab 2.
"""

import re
import time
import json
import hashlib
import csv
from collections import Counter
from dataclasses import dataclass, asdict, field, fields
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from labs import common as shared_api


@dataclass
class Lab2Config:
    """Configuration for Lab 2 experiments."""
    api_key: str
    base_url: str = "https://foundation-models.api.cloud.ru/v1"
    primary_model: str = "moonshotai/Kimi-K2.6"
    secondary_model: str = "google/gemini-3.1-pro-preview"
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: float = 120
    output_dir: str = "results/lab2"
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    profile: str = "cloudru"
    
    @classmethod
    def from_env(cls, profile: str | None = None) -> "Lab2Config":
        shared_config = shared_api.load_config(profile)
        if shared_config.max_tokens <= 0 or shared_config.timeout <= 0:
            raise ValueError("Lab 2 token limit and timeout must be positive.")
        return cls(
            api_key=shared_config.api_key,
            base_url=shared_config.base_url,
            primary_model=shared_config.models[0],
            secondary_model=shared_config.models[1],
            max_tokens=shared_config.max_tokens,
            timeout=shared_config.timeout,
            embedding_model=shared_config.embedding_model,
            profile=shared_config.profile,
        )


@dataclass
class CompletionResult:
    """Result of a single model completion."""
    model: str
    prompt_name: str
    prompt: str
    answer: str
    status: str  # "ok", "error", "truncated"
    error: str = ""
    latency_sec: float = 0.0
    answer_length: int = 0
    finish_reason: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    attempt: int = 1
    word_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Metrics
    links_count: int = 0
    years_count: int = 0
    numbers_count: int = 0
    caution_markers_count: int = 0
    confident_markers_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Lab2Client:
    """Profile-aware OpenAI-compatible client for Lab 2."""
    
    def __init__(self, config: Lab2Config):
        self.config = config
        shared_config = shared_api.LabConfig(
            api_key=config.api_key,
            base_url=config.base_url,
            models=(config.primary_model, config.secondary_model),
            embedding_model=config.embedding_model,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            profile=config.profile,
        )
        self.client = shared_api.make_client(shared_config)
        self._models_cache: Optional[List[str]] = None
    
    def list_models(self) -> List[str]:
        """Get available models."""
        if self._models_cache is None:
            self._models_cache = shared_api.list_models(self.client)
        return self._models_cache
    
    def complete(
        self,
        model: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> CompletionResult:
        """Execute a single completion request."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Model-aware token budget: Kimi uses reasoning tokens internally
        effective_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        if "kimi" in model.lower() or "moonshotai" in model.lower():
            effective_max_tokens = max(effective_max_tokens, 4096)

        start_time = time.time()
        try:
            # Try with thinking disabled for Kimi models
            extra_params = {}
            if "kimi" in model.lower() or "moonshotai" in model.lower():
                extra_params["extra_body"] = {"thinking": {"type": "disabled"}}

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=effective_max_tokens,
                **extra_params
            )
            latency = time.time() - start_time

            choice = response.choices[0]
            answer = choice.message.content or ""
            finish_reason = choice.finish_reason or "unknown"

            # Token usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            status = "ok" if answer.strip() else "error"
            error = "" if answer.strip() else "Model returned an empty response."
            if finish_reason == "length":
                status = "truncated"

            return CompletionResult(
                model=model,
                prompt_name="",
                prompt=prompt,
                answer=answer,
                status=status,
                error=error,
                latency_sec=round(latency, 3),
                answer_length=len(answer),
                finish_reason=finish_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
        except Exception as e:
            # Fallback without thinking parameter if it fails
            if "thinking" in str(e).lower() or "extra_body" in str(e).lower():
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature if temperature is not None else self.config.temperature,
                        max_tokens=effective_max_tokens,
                    )
                    latency = time.time() - start_time

                    choice = response.choices[0]
                    answer = choice.message.content or ""
                    finish_reason = choice.finish_reason or "unknown"

                    usage = response.usage
                    prompt_tokens = usage.prompt_tokens if usage else 0
                    completion_tokens = usage.completion_tokens if usage else 0
                    total_tokens = usage.total_tokens if usage else 0

                    status = "ok" if answer.strip() else "error"
                    error = "" if answer.strip() else "Model returned an empty response."
                    if finish_reason == "length":
                        status = "truncated"

                    return CompletionResult(
                        model=model,
                        prompt_name="",
                        prompt=prompt,
                        answer=answer,
                        status=status,
                        error=error,
                        latency_sec=round(latency, 3),
                        answer_length=len(answer),
                        finish_reason=finish_reason,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens
                    )
                except Exception as e2:
                    latency = time.time() - start_time
                    return CompletionResult(
                        model=model,
                        prompt_name="",
                        prompt=prompt,
                        answer="",
                        status="error",
                        error=str(e2),
                        latency_sec=round(latency, 3)
                    )
            else:
                latency = time.time() - start_time
                return CompletionResult(
                    model=model,
                    prompt_name="",
                    prompt=prompt,
                    answer="",
                    status="error",
                    error=str(e),
                    latency_sec=round(latency, 3)
                )
    
    def complete_with_metrics(
        self,
        model: str,
        prompt_name: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> CompletionResult:
        """Execute completion and compute metrics."""
        result = self.complete(model, prompt, temperature, max_tokens, system_prompt)
        result.prompt_name = prompt_name
        result.word_count = len(result.answer.split())
        
        # Compute metrics
        text = result.answer
        result.links_count = count_links(text)
        result.years_count = count_years(text)
        result.numbers_count = count_numbers(text)
        result.caution_markers_count = count_caution_markers(text)
        result.confident_markers_count = count_confident_markers(text)
        
        return result


def count_links(text: str) -> int:
    """Count HTTP/HTTPS links in text."""
    return len(re.findall(r"https?://\S+", str(text)))


def count_years(text: str) -> int:
    """Count years (19xx, 20xx) in text."""
    return len(re.findall(r"\b(19|20)\d{2}\b", str(text)))


def count_numbers(text: str) -> int:
    """Count numbers in text."""
    return len(re.findall(r"\b\d+[\d.,]*\b", str(text)))


def count_caution_markers(text: str) -> int:
    """Count caution/uncertainty markers in text."""
    markers = [
        "возможно", "вероятно", "нужно проверить", "нужно уточнить",
        "недостаточно данных", "зависит от", "требуется проверка",
        "может быть", "предположительно", "примерно", "ориентировочно",
        "не уверен", "не гарантирую", "может отличаться",
        "possibly", "probably", "need to verify", "need to check",
        "insufficient data", "depends on", "verification required",
        "may be", "approximately", "roughly", "not certain",
        "cannot guarantee", "might differ"
    ]
    text_lower = str(text).lower()
    return sum(text_lower.count(marker) for marker in markers)


def count_confident_markers(text: str) -> int:
    """Count confident/assertive markers in text."""
    markers = [
        "точно", "однозначно", "безусловно", "гарантирую",
        "фактически", "доказано", "установлено", "известно",
        "definitely", "certainly", "absolutely", "guaranteed",
        "factually", "proven", "established", "known for certain"
    ]
    text_lower = str(text).lower()
    return sum(text_lower.count(marker) for marker in markers)


def save_results_csv(results: List[CompletionResult], filepath: str) -> None:
    """Save results to CSV with UTF-8-SIG encoding."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    rows = [result.to_dict() for result in results]
    fieldnames = [item.name for item in fields(CompletionResult)]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(results)} results to {filepath}")


def save_results_json(results: List[CompletionResult], filepath: str) -> None:
    """Save results to JSON."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} results to {filepath}")


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def create_manifest(
    config: Lab2Config,
    results: List[CompletionResult],
    source_text_hash: str,
    runner_hash: str
) -> Dict[str, Any]:
    """Create experiment manifest."""
    successful = [r for r in results if r.status == "ok"]
    failed = [r for r in results if r.status != "ok"]
    status_counts = Counter(r.status for r in results)
    requests_by_model: Dict[str, Dict[str, int]] = {}
    for result in results:
        model_counts = requests_by_model.setdefault(result.model, {})
        model_counts[result.status] = model_counts.get(result.status, 0) + 1
    
    return {
        "experiment": "lab2_prompt_engineering",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "api_profile": config.profile,
            "primary_model": config.primary_model,
            "secondary_model": config.secondary_model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
            "output_dir": config.output_dir,
            "base_url": config.base_url,
        },
        "source_text_hash": source_text_hash,
        "runner_hash": runner_hash,
        "summary": {
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "by_status": dict(status_counts),
            "by_model": requests_by_model,
            "avg_latency_sec": round(sum(r.latency_sec for r in successful) / len(successful), 3) if successful else 0,
            "avg_length": round(sum(r.answer_length for r in successful) / len(successful), 1) if successful else 0,
        },
        "models_tested": list(set(r.model for r in results)),
        "prompt_names": list(set(r.prompt_name for r in results)),
    }


def save_manifest(manifest: Dict[str, Any], filepath: str) -> None:
    """Save manifest to JSON."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"Saved manifest to {filepath}")
