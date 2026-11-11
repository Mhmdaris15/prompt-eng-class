"""Build bilingual Lab 2 Markdown, HTML, and DOCX reports from one run."""

import argparse
from pathlib import Path

from lab1.documents import export_document
from lab2.report import ROOT, build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--student", default="")
    parser.add_argument("--group", default="")
    parser.add_argument("--ru-output", default=str(ROOT / "reports/lab2/LAB2_REPORT.md"))
    parser.add_argument("--en-output", default=str(ROOT / "reports/lab2/LAB2_REPORT_EN.md"))
    args = parser.parse_args()

    outputs = [(Path(args.ru_output), "ru"), (Path(args.en_output), "en")]
    for path, language in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(build(args.run_dir, language, args.student, args.group), encoding="utf-8")
        export_document(path, language=language)
        print(f"Wrote {path}, {path.with_suffix('.html')}, and {path.with_suffix('.docx')}")


if __name__ == "__main__":
    main()
