# Lab 3 submission contents

The report follows the twelve tasks in the teacher assignment.

- `lab3/Lab3_RAG_Student.ipynb`: executed Russian student notebook (13 code cells). The English version is `lab3/Lab3_RAG_Student_EN.ipynb`, also executed with 13 cells.
- `reports/lab3/LAB3_REPORT.docx` and `_EN.docx`: Russian/English reports; Markdown and HTML copies included.
- `results/lab3_entanglement/retrieval_review.csv`: 15 graded and explained retrieval results.
- `rag_comparison.csv`: five plain/RAG answer pairs with improvement/problem notes.
- `k_experiment.csv`: k=1,3,5 and manual three-source result.
- `claims_review_template.csv`: four filled source checks.
- The same result folder contains full prompts, source mappings, raw answers, reviewer, selected corpus, and diagnostics.
- Code and requirements are included. Put the original teacher dataset.csv in lab3 to rerun preparation; it is not bundled because the teacher supplied the large input separately.

The primary model is Claude Haiku 4.5; GigaChat 3 Pro reviews the answer. All 18 final experimental calls succeeded. The earlier 15 routing failures and two short successful probes are disclosed and retained.

Read and confirm the assistant-proposed relevance grades, claim verdicts, manual source choice, and personal reflection before submission. The prompt correction is a partial/negative result, not a claimed complete fix.

Defense guides: `docs/defense/DEFENSE_GUIDE_LAB3_RU.md` and `docs/defense/DEFENSE_GUIDE_LAB3_EN.md`. Both are included.
