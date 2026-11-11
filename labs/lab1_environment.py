"""Lab 1: endpoint setup, model discovery, and basic connection checks."""

from __future__ import annotations

import json
from pathlib import Path
import time

from labs.common import OUTPUT_DIR, complete, list_models, load_config, make_client


def main() -> None:
    config = load_config()
    client = make_client(config)
    started = time.time()
    available = list_models(client)
    selected = [model for model in config.models if model in available]
    usage = getattr(client, "_lab_usage_payload", {})
    model_usage = [
        {
            "model": item.get("model_name"),
            "token_limit": (item.get("rate_limit") or {}).get("token_max_limit"),
            "tokens_used": (item.get("rate_limit") or {}).get("token_current_usage", 0),
        }
        for item in usage.get("model_configs", [])
        if item.get("model_name") in selected
    ]
    checks = []
    for model in selected:
        result = complete(
            client,
            model,
            "Reply with exactly: connection verified.",
            max_tokens=32,
            temperature=0.0,
        )
        checks.append(
            {
                "model": model,
                "success": not result.error,
                "latency_seconds": result.latency_seconds,
                "response_length_chars": len(result.output),
                "output": result.output,
                "error": result.error,
            }
        )
    payload = {
        "api_profile": config.profile,
        "base_url": config.base_url,
        "models_available_count": len(available),
        "selected_models": selected,
        "models": available,
        "selected_model_usage": model_usage,
        "connection_checks": checks,
        "total_latency_seconds": round(time.time() - started, 3),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "lab1_environment.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
