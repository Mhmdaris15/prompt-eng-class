#!/usr/bin/env python3
"""
Convert Lab 2 Markdown report to DOCX format.
"""

import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import markdown


def parse_markdown_to_docx(md_path: Path, docx_path: Path):
    """Convert markdown file to DOCX with proper formatting."""
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15
    
    # Configure heading styles
    for level in range(1, 4):
        heading_style = doc.styles[f'Heading {level}']
        heading_style.font.name = 'Times New Roman'
        heading_style.font.color.rgb = RGBColor(0, 0, 0)
        if level == 1:
            heading_style.font.size = Pt(16)
            heading_style.font.bold = True
        elif level == 2:
            heading_style.font.size = Pt(14)
            heading_style.font.bold = True
        elif level == 3:
            heading_style.font.size = Pt(12)
            heading_style.font.bold = True
    
    # Parse markdown content
    lines = md_content.split('\n')
    i = 0
    in_code_block = False
    code_block_lines = []
    code_block_lang = ''
    in_table = False
    table_rows = []
    
    while i < len(lines):
        line = lines[i]
        
        # Handle code blocks
        if line.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_block_lang = line[3:].strip()
                code_block_lines = []
            else:
                in_code_block = False
                # Add code block as a paragraph with monospace font
                if code_block_lines:
                    p = doc.add_paragraph()
                    p.style = doc.styles['Normal']
                    run = p.add_run('\n'.join(code_block_lines))
                    run.font.name = 'Consolas'
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(51, 51, 51)
                    # Add shading
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(6)
                    p.paragraph_format.left_indent = Cm(1)
            i += 1
            continue
        
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue
        
        # Handle tables
        if line.strip().startswith('|') and line.strip().endswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
            # Parse table row
            cells = [cell.strip() for cell in line.strip()[1:-1].split('|')]
            table_rows.append(cells)
            i += 1
            # Check if next line is separator
            if i < len(lines) and re.match(r'^\s*\|[\s\-:]+\|\s*$', lines[i]):
                i += 1
                continue
            continue
        else:
            if in_table:
                # Create table
                if table_rows:
                    num_cols = len(table_rows[0])
                    table = doc.add_table(rows=len(table_rows), cols=num_cols)
                    table.style = 'Table Grid'
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    
                    for row_idx, row_data in enumerate(table_rows):
                        for col_idx, cell_text in enumerate(row_data):
                            cell = table.cell(row_idx, col_idx)
                            cell.text = cell_text
                            for paragraph in cell.paragraphs:
                                paragraph.style = doc.styles['Normal']
                                for run in paragraph.runs:
                                    run.font.size = Pt(9)
                                    run.font.name = 'Times New Roman'
                                    if row_idx == 0:
                                        run.bold = True
                    # Set column widths
                    for row in table.rows:
                        for idx, cell in enumerate(row.cells):
                            cell.width = Cm(16 / num_cols)
                
                table_rows = []
                in_table = False
                # Don't increment i here, reprocess current line
                continue
        
        # Handle headings
        if line.startswith('# '):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith('#### '):
            doc.add_heading(line[5:].strip(), level=4)
        # Handle horizontal rule
        elif line.strip() == '---' or line.strip() == '***':
            doc.add_paragraph().add_run().add_break()
        # Handle bold/italic inline
        elif line.strip():
            p = doc.add_paragraph()
            # Process inline formatting
            process_inline_formatting(p, line)
        else:
            # Empty line - add small space
            doc.add_paragraph()
        
        i += 1
    
    # Handle any remaining table
    if in_table and table_rows:
        num_cols = len(table_rows[0])
        table = doc.add_table(rows=len(table_rows), cols=num_cols)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for row_idx, row_data in enumerate(table_rows):
            for col_idx, cell_text in enumerate(row_data):
                cell = table.cell(row_idx, col_idx)
                cell.text = cell_text
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                        run.font.name = 'Times New Roman'
                        if row_idx == 0:
                            run.bold = True
    
    # Save document
    doc.save(docx_path)
    print(f"Saved DOCX to {docx_path}")


def process_inline_formatting(paragraph, text):
    """Process markdown inline formatting (bold, italic, code) in a paragraph."""
    # Pattern for **bold**, *italic*, `code`
    # We'll use a simple approach: split by patterns
    
    # First, handle code spans `...`
    parts = re.split(r'(`[^`]+`)', text)
    
    for part in parts:
        if part.startswith('`') and part.endswith('`'):
            run = paragraph.add_run(part[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(51, 51, 51)
        else:
            # Handle **bold** and *italic*
            bold_parts = re.split(r'(\*\*[^*]+\*\*)', part)
            for bp in bold_parts:
                if bp.startswith('**') and bp.endswith('**'):
                    run = paragraph.add_run(bp[2:-2])
                    run.bold = True
                else:
                    italic_parts = re.split(r'(\*[^*]+\*)', bp)
                    for ip in italic_parts:
                        if ip.startswith('*') and ip.endswith('*'):
                            run = paragraph.add_run(ip[1:-1])
                            run.italic = True
                        else:
                            run = paragraph.add_run(ip)
        # Set default font for normal text
        for run in paragraph.runs:
            if run.font.name is None:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(12)


def main():
    md_path = Path(__file__).parent.parent / 'reports/lab2/LAB2_REPORT.md'
    docx_path = Path(__file__).parent.parent / 'reports/lab2/LAB2_REPORT.docx'
    
    if not md_path.exists():
        print(f"Markdown file not found: {md_path}")
        return
    
    parse_markdown_to_docx(md_path, docx_path)
    print("Conversion complete!")


if __name__ == '__main__':
    main()