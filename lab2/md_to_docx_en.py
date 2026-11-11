#!/usr/bin/env python3
"""
Convert LAB2_REPORT.md to English DOCX report.
"""
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

# Translation dictionary for Russian -> English
TRANSLATIONS = {
    # Title page
    "Отчёт по лабораторной работе №2": "Lab Report #2",
    "Университет ИТМО": "ITMO University",
    "Дисциплина:": "Discipline:",
    "Промпт-инжиниринг": "Prompt Engineering",
    "Тема:": "Topic:",
    "Основы промпт-инжиниринга: от простых промптов к few-shot, оценка качества и кросс-модельная оценка": "Prompt Engineering Fundamentals: From Simple Prompts to Few-Shot, Quality Assessment and Cross-Model Evaluation",
    "Студент:": "Student:",
    "Группа:": "Group:",
    "Дата эксперимента (UTC):": "Experiment Date (UTC):",
    "Идентификатор запуска:": "Run ID:",
    "Санкт-Петербург, 2026": "Saint Petersburg, 2026",
    
    # Section 2
    "Цель работы": "Objective",
    "Освоить системный подход к промпт-инжинирингу: от базового промпта через структурированные версии (V1, V2, V3) к few-shot примерам, провести анализ влияния примеров на качество генерации, протестировать граничные случаи и реализовать кросс-модельную оценку результатов. Использовать метрики (длина, латентность, маркеры уверенности/осторожности, наличие ссылок/даты/чисел) для количественного сравнения.": "Master a systematic approach to prompt engineering: from basic prompt through structured versions (V1, V2, V3) to few-shot examples, analyze the impact of examples on generation quality, test edge cases, and implement cross-model evaluation of results. Use metrics (length, latency, confidence/caution markers, presence of links/dates/numbers) for quantitative comparison.",
    
    # Section 3
    "Использованные модели и условия": "Models and Conditions Used",
    "Параметр": "Parameter",
    "Значение": "Value",
    "Первичная модель": "Primary Model",
    "Вторичная модель": "Secondary Model",
    "API Endpoint": "API Endpoint",
    "Температура": "Temperature",
    "Макс. токенов": "Max Tokens",
    "Таймаут": "Timeout",
    "Выходная папка": "Output Directory",
    "Модельные параметры запроса:": "Model request parameters:",
    "Исходный текст, параметры, версии пакетов и SHA-256 кода сохранены вместе с результатами. Каждый новый запуск получает отдельную папку; существующую папку нельзя перезаписать.": "Source text, parameters, package versions, and code SHA-256 are saved with results. Each new run gets a separate folder; existing folders cannot be overwritten.",
    
    # Section 4
    "Исходный текст и критерии качества": "Source Text and Quality Criteria",
    "Использован учебный текст": "The educational text",
    "подготовленный для эксперимента. Объём — около 1200 слов, охватывающий: принципы работы LLM, распространённые режимы сбоев (галлюцинации, устаревание знаний, ограничения контекста, сикофантия), стратегии верификации и практические рекомендации для студентов.": "prepared for the experiment. Volume ~1200 words, covering: LLM operating principles, common failure modes (hallucinations, knowledge obsolescence, context limitations, sycophancy), verification strategies, and practical recommendations for students.",
    "Задание (Task)": "Task",
    "Аудитория:": "Audience:",
    "Контекст:": "Context:",
    "Критерии качества (9 критериев)": "Quality Criteria (9 criteria)",
    "Addresses the chosen topic directly": "Addresses the chosen topic directly",
    "Understandable by 9-10th grade students": "Understandable by 9-10th grade students",
    "Has logical structure (intro, main point, examples, explanations, conclusion)": "Has logical structure (intro, main point, examples, explanations, conclusion)",
    "Contains at least two concrete examples": "Contains at least two concrete examples",
    "No fabricated facts, quotes, sources, or dates": "No fabricated facts, quotes, sources, or dates",
    "Style is calm, educational, and appropriately cautious": "Style is calm, educational, and appropriately cautious",
    "Length within 180-220 words": "Length within 180-220 words",
    "Conclusion doesn't introduce new arguments": "Conclusion doesn't introduce new arguments",
    "Text usable after minor manual editing": "Text usable after minor manual editing",
    "Нежелательные ошибки (6 типов)": "Undesirable Errors (6 types)",
    "Fabricated citations or references": "Fabricated citations or references",
    "Invented statistics or precise numbers without basis": "Invented statistics or precise numbers without basis",
    "Overconfident claims without qualification": "Overconfident claims without qualification",
    "Condescending or overly complex language for the audience": "Condescending or overly complex language for the audience",
    "Missing required structural elements": "Missing required structural elements",
    "Exceeding or significantly under word count": "Exceeding or significantly under word count",
    
    # Section 5
    "Ход выполнения": "Execution Process",
    "Запуск эксперимента": "Experiment Launch",
    "Ключевой фрагмент подключения и отправки запроса:": "Key connection and request code snippet:",
    "Внутри": "Inside",
    "используется": "is used",
    "с автоматическим подсчётом метрик (ссылки, годы, числа, маркеры осторожности/уверенности). Для Kimi-моделей автоматически добавляется": "with automatic metrics calculation (links, years, numbers, caution/confidence markers). For Kimi models,",
    "автоматически добавляется": "is automatically added",
    "и увеличивается лимит токенов до 4096+.": "and token limit increased to 4096+.",
    "Задача 1: Выбор темы и критериев": "Task 1: Topic and Criteria Selection",
    "Тема, задание, аудитория, контекст и критерии зафиксированы в": "Topic, task, audience, context, and criteria recorded in",
    "Никаких API-запросов не выполнялось.": "No API requests were executed.",
    "Задача 2: Базовый простой промпт": "Task 2: Basic Simple Prompt",
    "Промпт:": "Prompt:",
    "Результаты:": "Results:",
    "Модель": "Model",
    "Статус": "Status",
    "Длина": "Length",
    "Латентность (с)": "Latency (s)",
    "Finish reason": "Finish reason",
    "Токены (in/out)": "Tokens (in/out)",
    "Задача 3: V1 — Улучшенный структурированный промпт": "Task 3: V1 — Improved Structured Prompt",
    "Компоненты промпта:": "Prompt components:",
    "роль, задача, аудитория, структура, ограничения, формат.": "role, task, audience, structure, constraints, format.",
    "Промпт (начало):": "Prompt (start):",
    "Осторожность": "Caution",
    "Уверенность": "Confidence",
    "Задача 4: Few-shot примеры": "Task 4: Few-Shot Examples",
    "Созданы контрастные примеры для демонстрации желаемого стиля.": "Contrastive examples created to demonstrate desired style.",
    "Слабый пример:": "Weak example:",
    "Почему слабый:": "Why weak:",
    "Сильный пример:": "Strong example:",
    "Почему сильный:": "Why strong:",
    "Сохранено в": "Saved in",
    "Задача 5: V2 — One-shot промпт": "Task 5: V2 — One-Shot Prompt",
    "V1 + один хороший few-shot пример, демонстрирующий уровень специфичности.": "V1 + one good few-shot example demonstrating specificity level.",
    "Задача 6: V3 — Few-shot промпт (3 примера)": "Task 6: V3 — Few-Shot Prompt (3 examples)",
    "V1 + три few-shot примера, каждый обучает конкретному навыку:": "V1 + three few-shot examples, each teaching a specific skill:",
    "Конкретный аргумент — как писать конкретные проверяемые примеры вместо общих фраз": "Concrete argument — how to write concrete verifiable examples instead of generic phrases",
    "Объяснение примера — как объяснять, ПОЧЕМУ пример важен": "Example explanation — how to explain WHY the example matters",
    "Осторожное заключение — как заключать без переоценки": "Cautious conclusion — how to conclude without overstatement",
    "Задача 7: Анализ влияния few-shot": "Task 7: Few-Shot Impact Analysis",
    "Количественное сравнение V1, V2, V3 по метрикам:": "Quantitative comparison of V1, V2, V3 by metrics:",
    "Версия": "Version",
    "Ссылки": "Links",
    "Годы": "Years",
    "Числа": "Numbers",
    "Finish": "Finish",
    "Задача 8: Граничные случаи (Edge Cases)": "Task 8: Edge Cases",
    "Протестировано 5 сценариев на обеих моделях:": "5 scenarios tested on both models:",
    "Кейс": "Case",
    "Описание": "Description",
    "Too general topic - model may give generic response": "Too general topic - model may give generic response",
    "Risk of fabricated facts - ask for specific citations": "Risk of fabricated facts - ask for specific citations",
    "Change audience - adapt for parents instead of students": "Change audience - adapt for parents instead of students",
    "Conflicting requirements - detailed but very short": "Conflicting requirements - detailed but very short",
    "Strict JSON format requirement": "Strict JSON format requirement",
    "Задача 9: Кросс-модельная оценка": "Task 9: Cross-Model Evaluation",
    "Каждая модель оценивает V3-ответ другой модели по 8 критериям (0-2 балла), проверяет копирование few-shot примеров и галлюцинации.": "Each model evaluates the other model's V3 response on 8 criteria (0-2 points), checks for few-shot example copying and hallucinations.",
    "Оценка Qwen → Kimi (промпт v3):": "Qwen → Kimi Evaluation (prompt v3):",
    "Критерий": "Criterion",
    "Балл (0-2)": "Score (0-2)",
    "topic_adherence": "topic_adherence",
    "audience_clarity": "audience_clarity",
    "structure": "structure",
    "specificity": "specificity",
    "style": "style",
    "factual_accuracy": "factual_accuracy",
    "constraints": "constraints",
    "usability": "usability",
    "Копирование few-shot:": "Few-shot copying:",
    "Галлюцинации:": "Hallucinations:",
    "Сильная сторона:": "Strength:",
    "Слабая сторона:": "Weakness:",
    "Общая оценка:": "Overall assessment:",
    "Оценка Kimi → Qwen: Ошибка парсинга JSON": "Kimi → Qwen Evaluation: JSON parsing error",
    "Сырой ответ:": "Raw response:",
    
    # Section 6
    "Результаты и анализ": "Results and Analysis",
    "Сводная статистика": "Summary Statistics",
    "Всего запросов": "Total requests",
    "Успешных": "Successful",
    "Обрезанных (length)": "Truncated (length)",
    "Ошибок": "Errors",
    "Средняя латентность (успешные)": "Average latency (successful)",
    "Средняя длина ответа (успешные)": "Average response length (successful)",
    "симв.": "chars",
    "Сравнение моделей по версиям промптов": "Model Comparison by Prompt Versions",
    "Агрегированные метрики по версиям:": "Aggregated metrics by versions:",
    "Промпт": "Prompt",
    "N": "N",
    
    # General
    "с": "s",
    "stop": "stop",
    "length": "length",
    "ok": "ok",
    "truncated": "truncated",
    "none": "none",
    "Код": "Code",
    "Результат": "Result",
    "Метрики": "Metrics",
    "Анализ": "Analysis",
    "Выводы": "Conclusions",
    "Приложения": "Appendices",
}

def translate_text(text: str) -> str:
    """Translate Russian text to English using dictionary."""
    result = text
    for ru, en in TRANSLATIONS.items():
        result = result.replace(ru, en)
    return result

def parse_markdown_to_docx(md_path: Path, docx_path: Path):
    """Parse markdown and create DOCX with English translation."""
    content = md_path.read_text(encoding='utf-8')
    
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15
    
    # Configure heading styles
    for level in range(1, 5):
        h_style = doc.styles[f'Heading {level}']
        h_style.font.name = 'Times New Roman'
        h_style.font.color.rgb = RGBColor(0, 0, 0)
        if level == 1:
            h_style.font.size = Pt(16)
            h_style.font.bold = True
        elif level == 2:
            h_style.font.size = Pt(14)
            h_style.font.bold = True
        elif level == 3:
            h_style.font.size = Pt(12)
            h_style.font.bold = True
        elif level == 4:
            h_style.font.size = Pt(11)
            h_style.font.bold = True
            h_style.font.italic = True
    
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    code_language = ''
    in_table = False
    table_lines = []
    
    while i < len(lines):
        line = lines[i]
        translated_line = translate_text(line)
        
        # Code block handling
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_language = line.strip()[3:].strip()
                code_lines = []
            else:
                in_code_block = False
                # Add code block to document
                if code_lines:
                    p = doc.add_paragraph()
                    p.style = 'Normal'
                    run = p.add_run('\n'.join(code_lines))
                    run.font.name = 'Consolas'
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(6)
                    # Add shading
                    pPr = p._p.get_or_add_pPr()
                    shading = pPr.makeelement(qn('w:shd'), {
                        qn('w:fill'): 'F2F2F2',
                        qn('w:val'): 'clear'
                    })
                    pPr.append(shading)
            i += 1
            continue
        
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
        
        # Table handling
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
        else:
            if in_table:
                # Process accumulated table
                if table_lines:
                    create_table_from_markdown(doc, table_lines)
                in_table = False
                table_lines = []
        
        if in_table:
            i += 1
            continue
        
        # Headings
        if translated_line.startswith('# '):
            doc.add_heading(translated_line[2:].strip(), level=1)
        elif translated_line.startswith('## '):
            doc.add_heading(translated_line[3:].strip(), level=2)
        elif translated_line.startswith('### '):
            doc.add_heading(translated_line[4:].strip(), level=3)
        elif translated_line.startswith('#### '):
            doc.add_heading(translated_line[5:].strip(), level=4)
        # Bold/italic inline
        elif translated_line.strip().startswith('**') and translated_line.strip().endswith('**'):
            p = doc.add_paragraph()
            run = p.add_run(translated_line.strip()[2:-2])
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
        # Regular paragraph
        elif translated_line.strip():
            p = doc.add_paragraph()
            # Handle inline formatting
            parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', translated_line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(12)
                elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
                    run = p.add_run(part[1:-1])
                    run.italic = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(12)
                elif part.startswith('`') and part.endswith('`'):
                    run = p.add_run(part[1:-1])
                    run.font.name = 'Consolas'
                    run.font.size = Pt(10)
                    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
                else:
                    run = p.add_run(part)
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(12)
        else:
            # Empty line - add spacing
            doc.add_paragraph()
        
        i += 1
    
    # Handle any remaining table
    if in_table and table_lines:
        create_table_from_markdown(doc, table_lines)
    
    doc.save(docx_path)
    print(f"Saved English DOCX to {docx_path}")

def create_table_from_markdown(doc: Document, table_lines: list):
    """Create a Word table from markdown table lines."""
    # Parse rows
    rows = []
    for line in table_lines:
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [cell.strip() for cell in line.strip()[1:-1].split('|')]
            rows.append(cells)
    
    if not rows:
        return
    
    # Skip separator row (---)
    data_rows = [r for r in rows if not all(re.match(r'^[-:\s]+$', cell) for cell in r)]
    
    if not data_rows:
        return
    
    # Create table
    table = doc.add_table(rows=len(data_rows), cols=len(data_rows[0]))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    for row_idx, row_data in enumerate(data_rows):
        for col_idx, cell_text in enumerate(row_data):
            if col_idx < len(table.rows[row_idx].cells):
                cell = table.rows[row_idx].cells[col_idx]
                cell.text = translate_text(cell_text)
                # Format header row
                if row_idx == 0:
                    for paragraph in cell.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for run in paragraph.runs:
                            run.bold = True
                            run.font.name = 'Times New Roman'
                            run.font.size = Pt(10)
                else:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.name = 'Times New Roman'
                            run.font.size = Pt(10)
    
    # Add spacing after table
    doc.add_paragraph()

if __name__ == '__main__':
    md_path = Path('reports/lab2/LAB2_REPORT.md')
    docx_path = Path('reports/lab2/LAB2_REPORT_EN.docx')
    parse_markdown_to_docx(md_path, docx_path)