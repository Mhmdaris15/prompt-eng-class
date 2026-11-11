"""Regenerate both Lab 3 reports and export HTML and DOCX."""
import argparse
from pathlib import Path
from .pipeline import ROOT, DEFAULT_RUN
from .report import build_reports
from lab1.documents import export_document

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,default=DEFAULT_RUN)
    args=parser.parse_args(); build_reports(args.run_dir)
    for name,language in [('LAB3_REPORT.md','ru'),('LAB3_REPORT_EN.md','en')]:
        path=ROOT/'reports/lab3'/name
        export_document(path,language=language); print(path.with_suffix('.docx'))

if __name__=='__main__': main()
