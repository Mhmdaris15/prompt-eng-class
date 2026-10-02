"""Build a report from one saved run and its completed editorial review.

Usage: python -m lab1.report --run-dir results/lab1_corrected
This command does not send model requests or assign qualitative scores.
"""

import argparse
import csv
import hashlib
import json
import re
import statistics
from pathlib import Path

from lab1.documents import export_document

ROOT = Path(__file__).resolve().parents[1]
SCORE_FIELDS = ['accuracy_1_5', 'completeness_1_5', 'clarity_1_5',
                'instruction_following_1_5', 'structure_1_5', 'verifiability_1_5']


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def table(headers, records):
    def cell(v): return str(v).replace('|', '\\|').replace('\n', '<br>')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in records])


def short(model):
    return 'Kimi' if model.startswith('moonshot') else 'Qwen'


def format_check(row):
    text = row['output'].strip()
    if row['variant'] == 'json':
        try:
            value = json.loads(text)
            return isinstance(value, dict) and set(value) == {'purpose', 'retrieval', 'limitations', 'security'} and all(isinstance(v, str) for v in value.values())
        except (ValueError, TypeError):
            return False
    if row['variant'] == 'list':
        return len(re.findall(r'^\s*[-*+]\s+', text, re.M)) == 4 and all(re.match(r'^\s*[-*+]\s+', line) for line in text.splitlines() if line.strip())
    if row['variant'] == 'plain_text':
        return len(re.split(r'\n\s*\n', text)) == 1 and not re.search(r'^\s*[-*+#]', text, re.M)
    raise ValueError('Unknown format variant')


def build(run_dir, student='', group=''):
    manifest = json.loads((run_dir / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest.get('status') == 'success', 'Do not build the final report from a failed or incomplete run'
    rows = read_csv(run_dir / 'lab1_results.csv')
    scores = read_csv(run_dir / 'quality_scores.csv')
    facts = read_csv(run_dir / 'hallucination_verification.csv')
    notes = json.loads((run_dir / 'review_notes.json').read_text(encoding='utf-8'))
    source = (run_dir / 'source_text.txt').read_text(encoding='utf-8')
    assert hashlib.sha256(source.encode()).hexdigest() == manifest['source_sha256'], 'Source snapshot changed'
    assert len(rows) == len(scores) == 26, 'Expected 26 answers and scores'
    identity = lambda r: (r['model'], r['task'], r['variant'])
    assert {identity(r) for r in rows} == {identity(r) for r in scores}, 'Scores belong to another run'
    assert all(all(1 <= int(r[f]) <= 5 for f in SCORE_FIELDS) for r in scores), 'Incomplete scores'
    assert all(sum(f['model'] == m for f in facts) >= 3 for m in manifest['selected_models'])
    assert all(f['status'] != 'TO_VERIFY' and f['source_or_url_checked'] for f in facts)
    pieces = []
    def add(text): pieces.append(text.strip())
    add(f'''# Отчёт по лабораторной работе №1

## 1. Титульный лист

**Университет ИТМО**  
**Дисциплина:** Промпт-инжиниринг  
**Тема:** Подключение к LLM через API Cloud.ru, базовые запросы и первичный поиск галлюцинаций  
**Студент:** {student or '____________________'}  
**Группа:** {group or '____________________'}  
**Дата эксперимента (UTC):** {manifest['run_date']}  
**Идентификатор запуска:** `{manifest['run_id']}`  
**Санкт-Петербург, 2026**

## 2. Цель работы

Освоить подключение к LLM через OpenAI-совместимый API Cloud.ru, сравнить две модели на одинаковых запросах, исследовать влияние формулировок и формата, проверить соблюдение ограниченного контекста и достоверность конкретных фактов.

## 3. Использованные модели и условия

Выбраны `moonshotai/Kimi-K2.6` и `Qwen/Qwen3-Coder-Next`: обе доступны через один API и позволяют сравнить две разные модели на одном техническом материале. Выбор основан на доступности и пригодности для текстовых запросов, а не на предположении о превосходстве одной модели.

Адрес подключения: `{manifest['base_url']}`. Ключ поступает из `API_KEY` в окружении или `.env`; значение ключа в результаты не записывается. Получено **{manifest['available_models_count']} идентификаторов**; полный список сохранён в приложении А. Наличие идентификатора в списке не означает, что каждый из них проверен на генерацию текста.

| Параметр | Значение |
| --- | --- |
| Python | {manifest['python_version']} |
| openai | {manifest['packages']['openai']} |
| python-dotenv | {manifest['packages']['python-dotenv']} |
| requests | {manifest['packages']['requests']} |
| Температура | {manifest['temperature']} в основных заданиях, 0 в тесте подключения |
| Максимальный бюджет | {manifest['max_tokens']} токенов для обеих моделей во всех запросах |
| Таймаут SDK | {manifest['timeout_seconds']} с; `max_retries={manifest['sdk_max_retries']}` |
| Передача ответа | `stream=False` |
| Число повторов | Один ответ каждой модели на каждый промпт |
| Порядок | Запросы попарно; первая модель чередуется между промптами |
| Основных ответов | {len(rows)}: 13 промптов × 2 модели |

Kimi дополнительно получает запрос `thinking: {{type: disabled}}`. Это пожелание API; наличие или отсутствие поля reasoning фиксируется отдельно. Одинаковый верхний предел токенов не гарантирует одинаковые токенизаторы, внутренние вычисления или стоимость. Поэтому сравнивается наблюдаемое поведение сервисов при указанных условиях.

Исходный текст, параметры, версии пакетов, расход токенов и SHA-256 кода сохранены вместе с результатами. Каждый новый запуск получает отдельную папку; существующую папку нельзя перезаписать. Результаты старого эксперимента сохранены отдельно и в расчёты этого отчёта не включены.

## 4. Исходный текст

Использован учебный текст **{manifest['source_title']}**, подготовленный для эксперимента и сохранённый в `source_text.txt`. Объём — **{manifest['source_word_count']} слов по пробельному разбиению**, рассчитанный примерно на 1–2 страницы обычного учебного текста; фактическое число страниц зависит от шрифта и интервала.

Текст выбран потому, что содержит техническое объяснение, эксплуатационные ограничения и материал для прямых и смысловых вопросов. Автор и год появления RAG в нём не указаны. Это контролируемый учебный материал, не цитата из научной статьи; для внешних исторических фактов используются источники раздела 8. Промпты и ответы англоязычные, анализ — на русском.
''')
    add('\n\n'.join(' '.join(p.splitlines()) for p in source.strip().split('\n\n')))
    add('''## 5. Ход выполнения

### 5.1. Подключение и сохранение результатов

```powershell
python -m pip install -r requirements.txt
python -m unittest lab1.test_runner -v
python -m lab1.runner --max-tokens 8192
```

Последняя команда создаёт новую папку в `results/lab1/runs/`; показанный в отчёте запуск находится в `results/lab1_corrected/`. Повтор с тем же `--output-dir` отклоняется, чтобы сохранить уже заполненные оценки.

Ключевой фрагмент подключения и отправки запроса:

```python
from labs.common import load_config, make_client, list_models
from lab1.runner import call

config = load_config()
client = make_client(config)
available_models = list_models(client)
for model in config.models:
    result = call(client, model, "task_1", "connection_check",
                  "Reply with exactly: connection verified.",
                  max_tokens=8192, temperature=0.0)
    print(model, repr(result.output), result.latency_seconds)
```

Внутри `call()` используется `client.chat.completions.create()` с сообщением роли `user`. Время измеряется монотонным счётчиком `time.perf_counter()`: это время полного клиентского запроса, включая ожидание и возможный повтор SDK, а не время до первого токена.
''')
    add(table(['Модель', 'Ответ (repr)', 'Время, с', 'Завершение'], [[short(r['model']), repr(r['output']), r['latency_seconds'], r['finish_reason']] for r in manifest['connection_checks']]))
    add('''### 5.2. Первый одинаковый запрос

> Explain the concept of retrieval-augmented generation to a second-year software engineering student in 120 words or fewer. Include one practical example.
''')
    add(notes['first_query'])
    add('''### 5.3. Пять формулировок суммаризации

Каждая инструкция дополнялась `Use only the source below.` и полным текстом раздела 4. Все десять ответов приведены в приложении Б.
''')
    summary_table = []
    for variant in ('summary', 'main_points', 'short_recap', 'outline', 'takeaways'):
        pair = sorted((r for r in rows if r['task'] == 'task_3' and r['variant'] == variant), key=lambda r: short(r['model']))
        summary_table.append([variant, pair[0]['prompt'].splitlines()[0], pair[0]['word_count'], pair[1]['word_count'], notes['summaries'][variant]])
    add(table(['Вариант', 'Инструкция', 'Kimi, слов', 'Qwen, слов', 'Сравнение'], summary_table))
    add(notes['summary_conclusion'])
    add('''### 5.4. Вопросы по тексту

Общая инструкция: `Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.` Затем передавался полный текст.
''')
    for variant, label in [('direct', 'Прямой вопрос'), ('inference', 'Смысловой вопрос'), ('unavailable', 'Ответа нет в тексте')]:
        pair = sorted((r for r in rows if r['task'] == 'task_4' and r['variant'] == variant), key=lambda r: short(r['model']))
        add(f"**{label}:** {pair[0]['prompt'].splitlines()[0]}")
        add(table(['Модель', 'Полный ответ'], [[short(r['model']), r['output']] for r in pair]))
    add(notes['questions'])
    add('''### 5.5. Форматы ответа

Во всех трёх запросах одинаковый предмет ответа: **назначение, процесс поиска, ограничения достоверности и требования безопасности**. Меняется только формат. Общая инструкция:

> Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below.

Добавляемые инструкции:

| Формат | Инструкция |
| --- | --- |
| Абзац | Return one paragraph covering all four aspects. |
| Список | Return exactly four bullet points, one per aspect in the given order. |
| JSON | Return valid JSON only, with exactly four string keys: "purpose", "retrieval", "limitations", and "security". No Markdown fences or extra text. |
''')
    add(table(['Модель', 'Формат', 'Проверка структуры', 'Слов'], [[short(r['model']), r['variant'], 'Пройдена' if format_check(r) else 'Не пройдена', r['word_count']] for r in rows if r['task'] == 'task_5']))
    add(notes['formats'])
    add('''### 5.6. Проверяемые факты

Использован отдельный запрос на шесть пронумерованных фактов с датами, числами, технологиями, авторами, точными названиями и URL. Не менее трёх утверждений должны относиться к публикациям или документированным инструментам. Каждый факт требуется пометить как основанный на исходном тексте или внешний; при неуверенности — прямо сообщить об этом. Полная инструкция:
''')
    fact_prompt = next(r['prompt'] for r in rows if r['task'] == 'task_6').replace(source, '[Полный исходный текст раздела 4]')
    add('```text\n' + fact_prompt + '\n```')
    add(notes['fact_probe'])
    add('''### 5.7. Методика оценки

Каждый ответ оценён по шести критериям: точность, полнота, ясность, следование инструкции, структура, проверяемость. Оценки — аналитическая разметка текста при подготовке отчёта, а не автоматический вывод модели или независимая экспертная аттестация. Студенту следует уметь объяснить приведённые комментарии.

Шкала: 5 — нет существенных замечаний; 4 — небольшое упущение или избыточное обобщение; 3 — заметная проблема при сохранении пользы; 2 — большая часть задачи не выполнена; 1 — ответ непригоден. Полнота оценивается относительно задачи: короткий правильный отказ при отсутствии информации может получить 5.

## 6. Таблица результатов

В таблице `слов` соответствует полю `word_count`: буквенно-цифровые группы с сохранением внутренних дефисов и апострофов. Числа тоже считаются единицами. Дополнительно сохранён старый счётчик `length_words` на основе `\\b\\w+\\b`; он иначе обрабатывает дефисы и сокращения. Лимиты слов интерпретируются с учётом этой условности. Символы считаются через `len(output)`, включая пробелы и переносы.
''')
    add(table(['Модель', 'Промпт', 'Время, с', 'Символов', 'Слов', 'Токенов ответа', 'Завершение'], [[short(r['model']), r['task'] + '/' + r['variant'], r['latency_seconds'], r['length_chars'], r['word_count'], r['completion_tokens'], r['finish_reason']] for r in rows]))
    aggregate = []
    for model in manifest['selected_models']:
        subset = [r for r in rows if r['model'] == model]
        times = [float(r['latency_seconds']) for r in subset]
        aggregate.append([short(model), len(subset), f'{statistics.mean(times):.3f}', f'{statistics.median(times):.3f}', sum(r['finish_reason'] == 'length' for r in subset), sum(bool(r['error']) for r in subset)])
    add(table(['Модель', 'Ответов', 'Среднее, с', 'Медиана, с', 'Обрезанных', 'Ошибок API'], aggregate))
    add(notes['latency'])
    add('''Дополнительные счётчики ниже считают вхождения, а не уникальные факты. Числа могут встречаться в нумерации и URL. Языковые маркеры ищутся с границами слов: «точно» больше не совпадает с частью слова «недостаточно». Добавлены английские маркеры, включая `information is unavailable`. Это лексический индикатор, не семантическая оценка уверенности: например, `may` может иметь несколько значений, а отрицание перед `guaranteed` отдельно не анализируется.
''')
    add(table(['Модель', 'Промпт', 'Числа', 'Годы', 'URL', 'Осторожность', 'Уверенность'], [[short(r['model']), r['task'] + '/' + r['variant'], r['number_count'], r['year_count'], r['link_count'], r['caution_marker_count'], r['confident_marker_count']] for r in rows if r['task'] == 'task_6' or r['variant'] == 'unavailable']))
    add('''## 7. Анализ качества

Т — точность; П — полнота; Я — ясность; И — следование инструкции; С — структура; В — проверяемость. Для внешних фактов выводы ограничены проверенной выборкой утверждений.
''')
    add(table(['Модель', 'Промпт', 'Т', 'П', 'Я', 'И', 'С', 'В', 'Комментарий'], [[short(r['model']), r['task'] + '/' + r['variant'], *[r[f] for f in SCORE_FIELDS], r['comment']] for r in scores]))
    add(notes['quality_conclusion'])
    add('''## 8. Проверка фактов и поиск галлюцинаций

Утверждения сопоставлены с первичными открытыми источниками при подготовке отчёта. «Внешнее по отношению к исходному тексту» не означает «ложное». Подтверждение ссылки не подтверждает автоматически все утверждения рядом с ней; поэтому проверяется конкретное содержание. Таблица содержит не менее трёх утверждений каждой модели из задания 6.
''')
    add(table(['Модель', 'Проверяемое утверждение', 'Источник', 'Вердикт', 'Обоснование'], [[short(r['model']), r['candidate_claim'], '[Первичный источник](' + r['source_or_url_checked'] + ')', r['status'], r['comment']] for r in facts]))
    add(notes['verification_conclusion'])
    add('''Для дальнейшего снижения риска можно требовать источник для каждого числа и даты, отделять внешние сведения от текста, разрешать ответ «неизвестно» и не требовать заполнить заданное число фактов при недостатке доказательств. Для задач только по тексту внешние знания нужно явно исключать. Эти меры не заменяют проверку, а влияние каждой из них отдельно в данном запуске не измерялось.

## 9. Выводы
''')
    add(notes['conclusions'])
    add(f'''### Ограничения и воспроизводимость

На каждый промпт сохранён один ответ: статистическая устойчивость различий не установлена. Температура 0,2 снижает случайность, но не гарантирует идентичные повторения. Верхний предел токенов общий, но модели и серверные реализации различаются. Слова, длина и число ссылок не заменяют оценку смысла. Часть формулировок суммаризации одновременно меняет структуру и ожидаемый объём, поэтому нельзя изолировать влияние одного слова.

Статус сбора данных: `{manifest['status']}`. Этот статус означает техническую завершённость запросов, а не фактическую правильность всех ответов. Программные регрессионные проверки выполнены отдельно от обращений к API.

Материалы текущего запуска: `results/lab1_corrected/`. В папке находятся CSV с промптами и ответами, `source_text.txt`, `manifest.json`, снимок исходного кода, заполненные `quality_scores.csv`, `hallucination_verification.csv` и аналитические заметки `review_notes.json`. Поле `manual_verification_required` отражает состояние при сборе данных; завершённая проверка оформлена отдельными файлами.

Для повторного построения документа без новых API-запросов:

```powershell
python -m pip install -r requirements-report.txt
python -m lab1.report --run-dir results/lab1_corrected
```

Предыдущая версия сохранена в `results/lab1_archive/before_fixes_2026-09-30/`. Старые численные результаты и оценки не переносились в новую таблицу.

## Приложение А. Список доступных идентификаторов
''')
    add('```text\n' + '\n'.join(manifest['available_models']) + '\n```')
    add('''## Приложение Б. Все исходные ответы

Приведены все 26 ответов без исправления их содержания. В промптах повтор исходного текста заменён ссылкой на раздел 4; полные сообщения сохранены в CSV. Ответы заключены в кодовые блоки, чтобы отделить их от анализа.
''')
    for number, row in enumerate(rows, 1):
        prompt = row['prompt'].replace(source, '[Полный исходный текст раздела 4]')
        add(f"### Б.{number}. {short(row['model'])} — {row['task']}/{row['variant']}\n\n**Промпт:**\n\n```text\n{prompt}\n```\n\n**Ответ:** {row['latency_seconds']} с; {row['word_count']} слов; `{row['finish_reason']}`.\n\n```text\n{row['output']}\n```")
    target = ROOT / 'LAB1_REPORT.md'
    target.write_text('\n\n'.join(pieces) + '\n', encoding='utf-8')
    export_document(target)
    print(f'Wrote {target.name}, HTML and DOCX from {manifest["run_id"]}.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--student', default='')
    parser.add_argument('--group', default='')
    args = parser.parse_args()
    build(args.run_dir, args.student, args.group)


if __name__ == '__main__':
    main()
