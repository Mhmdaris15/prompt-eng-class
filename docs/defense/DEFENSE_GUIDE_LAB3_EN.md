# Lab 3 Defense Guide English

## A 90 second presentation

I built a RAG assistant for scientific publications on quantum entanglement. I scanned 10,000 supplied records, found 156 keyword matches, and selected the first 100. This is a convenience subset, so I cannot generalize the results to all scientific literature.

The articles already contain 1,024-dimensional BGE-M3 vectors. I embed only the questions with the matching course model, normalize the vectors, and rank articles by cosine similarity. For each question, the primary model receives three abstracts with local source labels. I compare ordinary answers, a simple RAG prompt, and my improved instruction. Claude Haiku 4.5 generates the answers; GigaChat 3 Pro reviews one answer.

RAG helped connect question 2 to specific error-correction and communication studies. It also exposed limits: question 4 retrieved a graph-theory paper using the same word entanglement, while question 5 lacked current commercial measurements. Four claim checks found three supported claims and one partly supported interpretation. The reviewer repeated part of that interpretation. One added instruction produced only a partial correction. My conclusion is that retrieval, citations, and a reviewer help organize evidence but still require checking claims against the abstracts.

## The pipeline and each file

`dataset.csv → keyword subset → validated article vectors → query embedding → cosine ranking → selected abstracts → prompt → primary-model answer → source checking → reviewer → correction`

| File | Responsibility |
| --- | --- |
| `lab3/config.py` | Topic, five questions, custom RAG instruction, correction |
| `lab3/pipeline.py` | CSV loading, vector validation, search_articles, ask_llm, API routing, caches, CSV exports |
| `lab3/report.py` | Builds both reports from saved results and reading judgments |
| `lab3/build_notebook.py` | Executes the Russian and English evidence walkthroughs |
| `lab3/notebook_en.py` | English explanations for the same experiment |
| `lab3/export_reports.py` | Produces HTML and Word reports |
| `results/lab3_entanglement/` | Full prompts, answers, sources, vectors, grades, and diagnostics |

Building the notebook reads saved evidence; it does not repeat generation calls. To perform API experiments, use `python -m lab3.pipeline run`. The original teacher notebook is retained separately. The English similarity-test explanation translates the original Russian inputs for the reader; the actual vectors are unchanged.

## Where to find every required task

| Task | What to show |
| --- | --- |
| 1 connection and embeddings | `sentence_experiment.json`: pair 1–2 has cosine 0.72985, higher than the other two pairs |
| 2 dataset | Dataset fields and the three sample abstracts in the report/notebook; article_id stays a string |
| 3 topic | `manifest.json`: entanglement, 10,000 scanned, 156 matches, 100 selected; five questions in config |
| 4 ready vectors | `vectors.npy`: shape 100 × 1024; normalization and cosine in pipeline.py |
| 5 relevance | `retrieval_review.csv`: all 15 grades with reasons and full abstracts |
| 6 plain answer | `calls.json`, q1_plain; no external context |
| 7 two prompts | q1_simple/q2_simple versus q1_rag/q2_rag; identical context within each pair |
| 8 five comparisons | `rag_comparison.csv`; successful question 2 and problematic question 4 |
| 9 context size | `k_experiment.csv`: automatic k=1,3,5 plus manual three; `manual_selection.json` explains positions 1,3,4 |
| 10 claims | `claims_review_template.csv`: four completed checks, not an empty template |
| 11 reviewer | `calls.json`, review; compare its claims with your own source readings |
| 12 correction | q1_rag versus q1_corrected; only one instruction added, same question/model/sources |

## Numbers and source labels to remember

- Primary: `anthropic/claude-haiku-4.5`; reviewer: `GigaChat/GigaChat-3-Pro`.
- Embeddings: `cloud-bge/BAAI/bge-m3`; chat wire names use `cloud/` plus the model name.
- Embeddings use `x-bf-vk`; chat uses Bearer authorization. Never display the key during the defense.
- Generation: temperature 0.2; maximum 1,400 output tokens.
- There are 18 successful saved experiment calls, including the exploratory q3_corrected call. The main Task 12 correction is q1_corrected.
- The earlier 15 HTTP 400 requests lacked cloud/ routing; they are preserved separately. Two short successful routing probes are also recorded. These are connection diagnostics, not evidence of model quality.
- The implementation passed 43 tests when the reports were prepared.

For the checked q1_rag answer: S1 = 0705.1308, S2 = 0704.0251, S3 = 0704.1506. In the manual context, the optical paper becomes S2. Source labels are local to each answer.

## Likely instructor questions

**What is RAG?** Retrieval-Augmented Generation retrieves external documents and supplies them as context to a language model. It does not retrain the model. The model can still misread or overinterpret that context.

**What is an embedding?** A numeric representation of text used to compare semantic similarity. Here each article and query has 1,024 coordinates. k is the number of retrieved articles included in the generation context.

**How do retrieval and generation errors differ?** Retrieval can select the wrong material, as with the graph-theory paper. Generation can add unsupported meaning even to a relevant source, as with the Schmidt-number comparison.

**Why must the query embedding model match the dataset?** Both vectors must represent text in the same coordinate space. Matching dimension alone is insufficient. Recomputing article vectors with another model would create a different experiment.

**What does cosine similarity mean?** It compares vector direction: dot product divided by the product of norms. It is not a probability of relevance or a measure of factual truth.

**What failed in retrieval?** For question 4, the top result, 0705.0419, concerns graph complexity rather than quantum entanglement. It shares vocabulary and scores about 0.572 but receives relevance 0 after reading the abstract.

**Where did RAG help?** In question 2 it tied error correction, atomic-ensemble connection, and photon swapping to supplied abstracts. It did not establish measured deployment performance.

**Did the improved prompt always improve accuracy?** No. It exposed limitations more clearly, but q1_rag added a comparison baseline not explicitly stated in S3. Structure and caution are useful without guaranteeing factual care.

**Why can k=1 be too small?** Its answer overemphasized multipartite scope and underused the abstract's explicit bipartite partial-entropy statement. With k=3, the context also includes subspace and optical methods.

**Why not always use k=5?** It adds negativity bounds and a narrower spin-system application. More coverage also adds material to interpret; this small run does not establish an optimal k.

**What was the manual selection?** Positions 1,3,4 after reading all five abstracts: an entropy framework, photon measurement, and negativity bounds. This replaces a code-focused paper with a more direct quantification method. It is a proposed reading judgment, not proof of higher accuracy.

**What is the partly supported claim?** S3 says the Schmidt-number estimate is substantially lower, but does not explicitly identify previously reported values as the baseline or attribute the difference to measurement limitations. The primary answer adds those interpretations.

**Did the reviewer catch it?** It correctly notes that the abstract lacks a numeric Schmidt number, but repeats the previously reported values attribution. Its claim that absent algorithms make a method non-operational is also stronger than the abstract supports.

**Did the correction work?** Only partly. The new instruction asks the model not to infer an unnamed comparison baseline. The answer adds a baseline-is-unspecified caveat but still refers to prior experimental measurements. This negative result is explicitly reported.

**What does supported mean?** Supported by the supplied abstract, not independently proven true in the world. We did not inspect full papers or externally validate every scientific result.

## Demonstration order

1. Open the English report and show its twelve task sections.
2. Open `lab3/Lab3_RAG_Student_EN.ipynb` and show the recorded vectors, questions, and source grades.
3. Show the graph-theory false positive and the q1 claim/evidence table.
4. Show the second-model critique and the before/after correction excerpts.
5. Explain the limitations: 100 keyword-selected papers, abstracts only, one sample per variant, and proposed manual judgments requiring your confirmation.

Before presenting, read the abstracts supporting your grades and choose wording you personally agree with. Do not claim that the tests establish answer truth; they check implementation behavior and evidence handling.
