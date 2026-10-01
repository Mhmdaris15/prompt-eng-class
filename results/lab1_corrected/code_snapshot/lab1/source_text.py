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

Consider a support assistant for an internal software platform. The document
collection contains installation instructions, release notes, and troubleshooting
guides. A useful answer must refer to the version mentioned in the question.
A passage describing an older release may be relevant to the topic but wrong
for the requested version. Document metadata can record a title, version,
owner, access policy, and update time. Keeping this metadata attached to each
fragment helps the application filter results and present meaningful citations.

Chunk size is a design choice rather than a universal constant. Very small
fragments can separate an instruction from the condition that makes it valid.
Very large fragments can include unrelated material and consume more of the
model's context window. Overlap can preserve continuity near boundaries, but
it also duplicates text. Teams should evaluate chunking on representative
questions and check whether the returned fragments contain enough evidence.
Similarly, increasing k may improve coverage while increasing latency and
introducing distracting passages. The best setting depends on the documents,
questions, retrieval method, and available context budget.

Index maintenance is separate from language-model training. When a document is
corrected, the application should update or remove the corresponding indexed
fragments. Otherwise, retrieval may continue to surface obsolete information.
A citation is useful only if it points to the passage that actually supports
the answer. Merely attaching a document title or a plausible URL does not
establish that the answer is correct. If two retrieved passages disagree, the
system should expose the conflict instead of silently presenting one claim
as certain. A human reviewer may need to resolve the disagreement.

Evaluation can use a small collection of questions paired with expected
evidence and acceptable answers. Include straightforward questions, questions
that require combining passages, and questions that cannot be answered from
the corpus. Inspect retrieval and generation separately: a correct passage
can be followed by an incorrect answer, and a fluent answer can conceal a
retrieval failure. An answer should not receive a high faithfulness score
merely because it repeats words from the context. Review whether its main
claims follow from the supplied passages and whether important qualifications
have been preserved.

Operational safeguards must surround the model. Authorization should be
enforced by the application before private passages are exposed to a user.
Prompts alone are not an access-control mechanism. Logs used for evaluation
should avoid disclosing confidential documents or credentials. Cached answers
must respect the user's access permissions and the freshness of the underlying
documents. These constraints make RAG an application architecture involving
data management, retrieval, generation, and evaluation rather than a guarantee
of accurate answers from a language model.
"""
