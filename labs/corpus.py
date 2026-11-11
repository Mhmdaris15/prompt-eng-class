"""Technical source text used by the summarization, QA, and RAG labs."""

TECHNICAL_TEXT = """
Retrieval-augmented generation (RAG) combines a language model with an external
collection of documents. Before generating an answer, a retriever searches the
collection for passages related to the user question. The selected passages are
inserted into the model prompt as evidence. This reduces dependence on a model's
parametric memory and makes answers easier to inspect.

A typical RAG pipeline has five stages: document loading, chunking, indexing,
retrieval, and generation. Chunking divides long documents into smaller
overlapping fragments. An index stores representations of those fragments.
Keyword indexes are simple and transparent, while vector indexes compare
embeddings using a similarity measure such as cosine similarity. The retriever
returns the top-k fragments, where k is a configurable number.

RAG does not guarantee truth. A retriever can return irrelevant passages, the
context can be incomplete, and the model can still misinterpret evidence.
Applications should therefore instruct the model to distinguish evidence from
assumptions, cite the supplied passages, and say when the context is
insufficient. Evaluation should measure both answer quality and context
adherence.

For production systems, engineers also monitor latency, retrieval precision,
token usage, and failure rates. Caching repeated queries can reduce latency.
Access controls are required when the corpus contains private information.
Prompt injection is another risk: retrieved documents should be treated as
untrusted data rather than as instructions that override the system policy.
"""


def chunks(text: str, words_per_chunk: int = 90) -> list[str]:
    words = text.split()
    return [
        " ".join(words[index : index + words_per_chunk])
        for index in range(0, len(words), words_per_chunk)
    ]
