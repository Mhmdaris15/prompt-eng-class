# Lab 3 Scientific publication RAG

The specification is [the teacher's assignment](../docs/assignments/Лабораторная%20работа%203.md).
The original `Lab3_RAG_dataset_Notebook.ipynb` and `dataset.csv` are retained unchanged.
The student notebook is `Lab3_RAG_Student.ipynb`. Run it from the project root or the lab3 directory.

## Setup and execution

```powershell
uv run --with-requirements requirements-lab3.txt python -m lab3.pipeline prepare
uv run --with-requirements requirements-lab3.txt python -m lab3.pipeline run
uv run --with-requirements requirements-lab3.txt python -m lab3.pipeline report
```

Configure `COURSE_API_KEY` (or the teacher’s `AICLAB_API_KEY`) in the worktree's private `.env`. Set `COURSE_MODEL_A` and `COURSE_MODEL_B` to two distinct models available to the course key; defaults match the teacher notebook. Generation uses Bearer authorization. Embeddings use `requests.post` with `x-bf-vk` and exactly `cloud-bge/BAAI/bge-m3`. A Cloud.ru embedding model must not be substituted for the dataset's embedding space.

`prepare` scans up to 10,000 rows, preserves IDs as strings, selects the first 100 entanglement matches, and validates 1,024-dimensional vectors. The full dataset remains local and is ignored by Git because it exceeds GitHub's normal individual-file limit. Store it beside the teacher notebook.

`run` validates models, caches query vectors and individual generation calls, and persists every status, prompt, response, source mapping, and usage record. Repeating a cached call does not spend tokens again. Failed calls remain visible; use a new `--run-dir` for a fresh experiment. The automatic k=3 result is reused consistently in the k comparison. The same primary model handles all ordinary and RAG answers. The second model reviews only.

After reading the five retrieved abstracts for question 1, create `results/lab3_entanglement/manual_selection.json` with `{"positions": [1, 3, 5], "reason": "your source-based justification"}`. The displayed positions are examples, not a prescribed selection. Run the pipeline again to generate the manual-context answer.

## Required evidence

| Assignment tasks | Code and saved evidence |
| --- | --- |
| 1 embedding connection and semantic experiment | `sentence_experiment.json`, prediction in manifest |
| 2–4 dataset, theme and vectors | `corpus.json`, `vectors.npy`, `manifest.json` |
| 5 five questions and top-3 relevance | `retrieved.json`, `retrieval_review.csv`; read and grade all 15 abstracts |
| 6 ordinary answer | `calls.json`: `q1_plain` |
| 7 simple/improved instruction on two questions | `config.py`, `q1_simple`, `q2_simple`, corresponding RAG outputs |
| 8 RAG/plain on five questions | `rag_comparison.csv`; full texts in `calls.json` |
| 9 k=1/3/5 and manual three | `k_experiment.csv`, `manual_selection.json` |
| 10 at least three verified claims | fill `claims_review_template.csv` with exact abstract evidence |
| 11 different model reviewer | `calls.json`: `review`; compare with source-based manual checks |
| 12 change exactly one factor | `q1_rag` versus `q1_corrected`; only one instruction is appended |

Manual grades, claim verdicts, and the selection must be justified against abstracts. Generated review templates are not completed evaluations. The report remains explicitly a draft until those records and the experiment outputs exist. Add bilingual narrative judgments in `analysis.json` with keys `comparison_ru/en`, `k_ru/en`, `review_ru/en`, `correction_ru/en`, and `conclusions_ru/en`.

## File responsibilities

- `config.py`: topic, five question types, prediction sentences, improved prompt, correction.
- `pipeline.py`: streaming CSV loading, vector checks, retrieval, authenticated API calls, caching, result exports and CLI.
- `report.py`: Russian/English Markdown reports under `reports/lab3`, following all twelve assignment tasks.
- `test_pipeline.py`: offline vector and evidence-integrity checks.
- `Lab3_RAG_Student.ipynb`: reproducible notebook walkthrough and saved outputs from the same run.

The old `labs/lab3_rag.py` is a separate historical demo using a small synthetic corpus; it does not implement this assignment.

Generate HTML and DOCX exports:

```powershell
uv run --with-requirements requirements-lab3.txt --with-requirements requirements-report.txt python -m lab3.export_reports
```

The executed run uses Haiku 4.5 and GigaChat 3 Pro. Existing-run model choices are reused from its manifest unless explicitly overridden. The initial 15 unprefixed HTTP 400 requests and two successful routing probes are preserved separately. Chat wire IDs require the `cloud/` prefix specified by the new course connection document.


## Defense and notebook languages

- [Russian defense guide](../docs/defense/DEFENSE_GUIDE_LAB3_RU.md)
- [English defense guide](../docs/defense/DEFENSE_GUIDE_LAB3_EN.md)
- [Russian executed notebook](Lab3_RAG_Student.ipynb)
- [English executed notebook](Lab3_RAG_Student_EN.ipynb)

`python -m lab3.build_notebook` now builds both languages. Use `--language ru` or `--language en` for one version. Both read the same saved experiment and make no new generation requests. English presentation translates explanations and verdict labels; original scientific abstracts, model answers, and Russian similarity-test inputs are preserved as evidence.
