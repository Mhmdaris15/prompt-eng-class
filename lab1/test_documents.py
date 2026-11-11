"""Regression check for Word joining adjacent, differently shaped tables."""
import tempfile
import unittest
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from .documents import export_document

class DocumentTableTests(unittest.TestCase):
    def test_adjacent_tables_keep_separate_headers(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'report.md'
            path.write_text('# Report\n\n| ID | Question |\n| --- | --- |\n| 1 | Why? |\n\n| Q | Article | Score |\n| --- | --- | --- |\n| 1 | 0704.0001 | 2 |\n',encoding='utf-8')
            export_document(path)
            doc=Document(path.with_suffix('.docx'))
            self.assertEqual(len(doc.tables),2)
            elements=list(doc.element.body)
            tables=[i for i,element in enumerate(elements) if element.tag==qn('w:tbl')]
            self.assertTrue(any(element.tag==qn('w:p') for element in elements[tables[0]+1:tables[1]]))
            self.assertEqual(doc.tables[0].cell(0,0).text,'ID')
            self.assertEqual(doc.tables[1].cell(0,0).text,'Q')

if __name__=='__main__': unittest.main()
