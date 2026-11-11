"""Build and execute an evidence-reading notebook without repeating API calls."""
from pathlib import Path
import sys
import argparse
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager
from .pipeline import ROOT

def build(language='ru'):
    nb=nbf.v4.new_notebook(); cells=[]
    def md(text): cells.append(nbf.v4.new_markdown_cell(text))
    def code(text): cells.append(nbf.v4.new_code_cell(text))
    md('# Лабораторная работа 3 Исследование RAG по научным публикациям\n\nТема: квантовая запутанность. Собственные вопросы и инструкция находятся в `lab3/config.py`. Этот ноутбук читает фактические результаты воспроизводимого CLI-запуска. Если API-результаты отсутствуют, соответствующие задания отмечаются как невыполненные. Исходный ноутбук преподавателя сохранён отдельно. Оценки и объяснения требуют подтверждения студентом.')
    code("from pathlib import Path\nimport sys, json, csv\nROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'lab3/pipeline.py').exists())\nsys.path.insert(0, str(ROOT))\nfrom lab3.pipeline import *\nfrom lab3.config import *\nrun_dir = DEFAULT_RUN\nmanifest = prepare(run_dir)\ncalls = read(run_dir/'calls.json') if (run_dir/'calls.json').exists() else {}\ndef show(name):\n    print(json.dumps(calls.get(name, {'status':'not executed'}), ensure_ascii=False, indent=2))\ndef show_csv(name):\n    p=run_dir/name\n    if not p.exists(): print('Not yet generated:', name); return\n    with p.open(encoding='utf-8-sig',newline='') as f:\n        for row in csv.DictReader(f): print(json.dumps(row,ensure_ascii=False))\nprint('Run status:', manifest['status'])")
    md('## Задание 1 Проверка подключения и эмбеддинги\n\nПрогноз записан до API: наиболее близки предложения 1 и 2. Для запроса эмбеддингов используется requests.post и x-bf-vk; для генерации — Bearer. Выполните `python -m lab3.pipeline run` после настройки локального `.env`.')
    code("print(manifest['sentence_prediction'])\np=run_dir/'sentence_experiment.json'\nprint(json.dumps(read(p),ensure_ascii=False,indent=2) if p.exists() else 'Embedding experiment not executed: course API key required.')")
    md('## Задание 2 Датасет и аннотации\n\nАннотации сообщают объект, метод и заявленные результаты, но часто не содержат деталей доказательств, методики, погрешностей и стоимости внедрения.')
    code("papers=read(run_dir/'corpus.json')\nprint(manifest['fields'])\nfor paper in papers[:3]: print(paper['article_id'], paper['title'], '\\n', paper['abstract'], '\\n')")
    md('## Задание 3 Тема и пять собственных вопросов\n\nОтбор первых 100 совпадений по entanglement не является репрезентативной случайной выборкой. Поиск ограничен этим корпусом.')
    code("print({k:manifest[k] for k in ['keyword','scanned','matches','selected']})\nfor i,q in enumerate(QUESTIONS,1): print(i,QUESTION_TYPES[i-1],q)")
    md('## Задание 4 Чтение готовых векторов\n\nJSON → float32; проверяются размерность, конечность и ненулевая норма. Cosine — скалярное произведение нормализованных векторов; смысловое сходство не доказывает истинность.')
    code("matrix=np.load(run_dir/'vectors.npy',allow_pickle=False)\nprint('Shape:',matrix.shape)\nprint('All finite:',np.isfinite(matrix).all())\nprint('First article identifier:',papers[0]['article_id'])")
    md('## Задание 5 Оценка релевантности поиска\n\nДля каждого из пяти вопросов нужно прочитать три найденные аннотации и заполнить оценку 0/1/2 и её обоснование.')
    code("show_csv('retrieval_review.csv')")
    md('## Задание 6 Обычный ответ без документов')
    code("show('q1_plain')")
    md('## Задание 7 Два RAG-промпта на двух вопросах\n\nКонтекст и основная модель одинаковы. Улучшенная инструкция ограничивает выводы аннотациями, задаёт структуру, локальные ссылки и отказ при недостатке сведений.')
    code("print('Simple: Answer the question using these article abstracts.')\nprint('Improved:',MY_RAG_INSTRUCTION)\nfor i in [1,2]:\n    show(f'q{i}_simple'); show(f'q{i}_rag')")
    md('## Задание 8 Пять сравнений с RAG и без RAG\n\nПолные ответы хранятся в CSV. Успешный и проблемный случаи необходимо обосновать содержанием источников.')
    code("show_csv('rag_comparison.csv')")
    md('## Задание 9 k равное 1 3 5 и ручной отбор\n\nПрочитайте пять аннотаций и заполните manual_selection.json. Нельзя выдавать автоматический Top-3 за ручной выбор.')
    code("p=run_dir/'retrieved.json'\nif p.exists():\n    for i,paper in enumerate(read(p)['1'],1): print(i,paper['title'],paper['abstract'])\nselection_path=run_dir/'manual_selection.json'\nchosen_positions=read(selection_path)['positions'] if selection_path.exists() else []\nprint('Chosen positions:',chosen_positions)\nshow_csv('k_experiment.csv')")
    md('## Задание 10 Проверка трёх утверждений\n\nДля каждого утверждения укажите точный фрагмент аннотации и вердикт. Ссылка [S1] не является доказательством сама по себе.')
    code("show_csv('claims_review_template.csv')")
    md('## Задание 11 Рецензия второй модели\n\nСопоставьте обоснованное замечание и замечание, требующее проверки, с собственной проверкой утверждений.')
    code("show('review')")
    md('## Задание 12 Одно изменение\n\nК базовой улучшенной инструкции для вопроса 1 добавлена только одна инструкция. Источники и модель сохраняются. До просмотра результатов нельзя утверждать, что это исправило ошибку.')
    code("print(CORRECTION_ADDITION)\nshow('q1_rag')\nshow('q1_corrected')\np=run_dir/'analysis.json'\nprint(json.dumps(read(p),ensure_ascii=False,indent=2) if p.exists() else 'Manual narrative analysis is pending.')")
    if language == 'en':
        from .notebook_en import MARKDOWN
        markdown_cells=[cell for cell in cells if cell.cell_type=='markdown']
        if len(markdown_cells)!=len(MARKDOWN): raise ValueError('English section map does not match notebook')
        for cell,text in zip(markdown_cells,MARKDOWN): cell.source=text
        for cell in cells:
            if cell.cell_type!='code': continue
            cell.source=cell.source.replace("for row in csv.DictReader(f): print(json.dumps(row,ensure_ascii=False))", "for row in csv.DictReader(f):\\n            row={k:v for k,v in row.items() if not k.endswith('_ru')}\\n            if 'verdict' in row: row['verdict']={'подтверждается':'supported','частично':'partly supported','не подтверждается':'unsupported','противоречит источнику':'contradicted'}.get(row['verdict'],row['verdict'])\\n            print(json.dumps(row,ensure_ascii=False))".replace('\\n','\n'))
            cell.source=cell.source.replace("json.dumps(read(p),ensure_ascii=False,indent=2) if p.exists() else 'Manual narrative analysis is pending.'", "json.dumps({k:v for k,v in read(p).items() if k.endswith('_en') or k=='assessment_author'},ensure_ascii=False,indent=2) if p.exists() else 'Manual narrative analysis is pending.'")
    nb.cells=cells
    nb.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}}
    km=KernelManager(kernel_name='python3'); km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    NotebookClient(nb,km=km,timeout=120,resources={'metadata':{'path':str(ROOT)}}).execute()
    path=ROOT/('lab3/Lab3_RAG_Student_EN.ipynb' if language=='en' else 'lab3/Lab3_RAG_Student.ipynb'); nbf.write(nb,path); print(path)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language',choices=['ru','en','both'],default='both')
    args=parser.parse_args()
    for language in (['ru','en'] if args.language=='both' else [args.language]): build(language)

if __name__=='__main__': main()
