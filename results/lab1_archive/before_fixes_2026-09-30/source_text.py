"""Controlled technical source text used consistently across Lab 1 tasks."""

SOURCE_TITLE = "Retrieval-Augmented Generation in Production Systems"
SOURCE_TEXT = """
Retrieval-augmented generation (RAG) combines a language model with an external
collection of documents. Before answering, a retriever searches that collection
for passages related to the user's question. The selected passages are inserted
into the prompt as evidence. This reduces dependence on the model's parametric
memory and makes an answer easier to inspect.

A typical RAG pipeline includes document loading, chunking, indexing, retrieval,
and generation. Chunking divides long documents into smaller fragments, often
with overlap. An index stores a representation of each fragment. A keyword index
is transparent and easy to debug, while a vector index compares embeddings by a
similarity measure such as cosine similarity. A retriever returns the top-k
fragments, where k is a configurable number.

RAG does not guarantee truth. Retrieval may return irrelevant passages, the
context may be incomplete, and the model may misinterpret the evidence.
Applications should ask the model to separate evidence from assumptions, cite
the supplied passages, and state when the context is insufficient. Evaluation
should measure both answer quality and adherence to the retrieved context.

Production teams monitor latency, retrieval precision, token usage, and failure
rates. Caching repeated queries can reduce latency. Access controls are needed
when a corpus contains private information. Retrieved documents are untrusted
data: prompt injection inside a document must not override the system policy.
"""
