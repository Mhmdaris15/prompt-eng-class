"""Lab 3: a transparent TF-IDF RAG baseline and comparison."""

from __future__ import annotations

import math
import re

from labs.common import OUTPUT_DIR, complete, load_config, make_client, write_csv
from labs.corpus import TECHNICAL_TEXT, chunks


QUERIES = [
    "What are the stages of a RAG pipeline?",
    "What security risks should engineers monitor?",
    "Does RAG guarantee truthful answers?",
]


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower(), re.UNICODE)


def retrieve(query: str, passages: list[str], top_k: int = 2) -> list[str]:
    """Use sparse TF-IDF cosine similarity without external vector packages."""
    documents = [tokenize(passage) for passage in passages]
    query_tokens = tokenize(query)
    vocabulary = set(query_tokens).union(*(set(document) for document in documents))
    scores = []
    for document in documents:
        score = 0.0
        for term in vocabulary:
            query_tf = query_tokens.count(term)
            doc_tf = document.count(term)
            if query_tf and doc_tf:
                score += (1 + math.log(query_tf)) * (1 + math.log(doc_tf))
        scores.append(score)
    indexes = sorted(range(len(passages)), key=lambda index: scores[index], reverse=True)
    return [passages[index] for index in indexes[:top_k] if scores[index] > 0]


def run() -> None:
    config = load_config()
    client = make_client(config)
    passages = chunks(TECHNICAL_TEXT)
    rows = []
    for model in config.models:
        for query in QUERIES:
            context = "\n\n".join(retrieve(query, passages))
            no_rag = complete(
                client, model, query, max_tokens=300, temperature=0.2
            )
            with_rag = complete(
                client,
                model,
                f"Answer only from the context. If insufficient, say so.\n"
                f"Context:\n{context}\n\nQuestion: {query}",
                max_tokens=300,
                temperature=0.2,
            )
            for mode, result in (("without_rag", no_rag), ("with_rag", with_rag)):
                rows.append(
                    {
                        "model": model,
                        "query": query,
                        "mode": mode,
                        "retrieved_context": context if mode == "with_rag" else "",
                        "output": result.output,
                        "latency_seconds": result.latency_seconds,
                        "response_length_chars": len(result.output),
                        "error": result.error,
                    }
                )
    write_csv(OUTPUT_DIR / "lab3_rag_comparison.csv", rows)
    print(f"Wrote {len(rows)} RAG comparison rows to {OUTPUT_DIR}")


if __name__ == "__main__":
    run()
