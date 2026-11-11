# Prompt engineering coursework

ITMO laboratory assignments, experiment code, notebooks, reports, and source evidence. Current work continues in `nvidia-model-lab2-worktree` on `codex/lab2-bilingual-execution`.

| Folder | Contents |
| --- | --- |
| [docs/assignments](docs/assignments) | Original assignments for Labs 1–3 and the updated course API instructions |
| [docs/defense](docs/defense) | Earlier defense guides |
| `lab1/`, `lab2/` | Previous assignment implementations and report generators |
| [lab3](lab3/README.md) | Scientific-publication RAG assignment, teacher inputs, student notebook, pipeline |
| [reports/lab1](reports/lab1) | Lab 1 report exports |
| [reports/lab2](reports/lab2) | Lab 2 report exports |
| [reports/lab3](reports/lab3) | Lab 3 reports in Russian and English |
| `results/` | Recorded prompts, responses, metrics, source mappings, and CSV evidence |
| `labs/` | Shared API profiles and older standalone demos |

Two older Lab 2 Word files may also remain at the root because Word has them open. Their report-folder copies are available under `reports/lab2/`.

## Lab 3

Place the teacher's `dataset.csv` in `lab3/`, alongside the original teacher notebook. The large dataset is deliberately ignored by Git. Preserve article IDs as strings.

Put the course key in the private worktree `.env` using `AICLAB_API_KEY` or `COURSE_API_KEY`; see `.env.example` for variable names. Chat requests use Bearer authorization and `cloud/` model routing. Question embeddings require `cloud-bge/BAAI/bge-m3` with `x-bf-vk`. Cloud.ru credentials are separate.

```powershell
uv run --with-requirements requirements-lab3.txt python -m lab3.pipeline prepare
uv run --with-requirements requirements-lab3.txt python -m lab3.pipeline run
uv run --with-requirements requirements-lab3.txt python -m lab3.build_notebook
uv run --with-requirements requirements-lab3.txt --with-requirements requirements-report.txt python -m lab3.export_reports
```

The existing run reuses its recorded primary/reviewer models and cached calls. A changed prompt/model cannot silently overwrite a cached result. Use `--run-dir results/<new-name>` for a separate experiment. Manual review files are retained when tables are regenerated.

Read [the complete Lab 3 pipeline and requirement mapping](lab3/README.md). Defense guides: [Russian](docs/defense/DEFENSE_GUIDE_LAB3_RU.md) and [English](docs/defense/DEFENSE_GUIDE_LAB3_EN.md). Executed notebooks: [Russian](lab3/Lab3_RAG_Student.ipynb) and [English](lab3/Lab3_RAG_Student_EN.ipynb). The older `labs/lab3_rag.py` demo uses a different corpus and does not satisfy the teacher's new assignment.

## Previous reports

Lab 1 and Lab 2 report generators now write under `reports/lab1/` and `reports/lab2/`. Existing results and the teacher's input files are preserved. Original NVIDIA application notes are archived in [docs/LEGACY_NVIDIA_README.md](docs/LEGACY_NVIDIA_README.md).

## Checks

```powershell
uv run --with-requirements requirements-lab3.txt --with-requirements requirements-report.txt python -m unittest lab1.test_runner labs.test_common lab2.test_runner lab3.test_pipeline lab1.test_documents -v
```

The notebook and CSV judgments are assistant-proposed source readings. Read the abstracts and confirm the assessments before submitting them as your own work.
