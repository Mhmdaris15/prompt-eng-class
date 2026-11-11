"""Generate Russian or English Lab 2 reports from one preserved experiment run."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CRITERIA_RU = [
    "Соответствие теме", "Понятность для аудитории", "Логичная структура",
    "Не менее двух конкретных примеров", "Фактическая аккуратность",
    "Подходящий и осторожный стиль", "Объём 180–220 слов",
    "Вывод без новых аргументов", "Пригодность после небольшой правки",
]
CRITERIA_EN = [
    "Topic relevance", "Audience clarity", "Logical structure",
    "At least two concrete examples", "Factual care",
    "Appropriate and cautious style", "180–220 word length",
    "Conclusion adds no new arguments", "Usable after minor editing",
]

ASSIGNMENT_RUBRIC = [
    ("Соответствие теме", "Ответ не уходит в сторону от выбранной темы", "Topic relevance", "The answer stays on the selected topic."),
    ("Понятность аудитории", "Текст понятен выбранной аудитории", "Audience clarity", "The text is understandable to the intended audience."),
    ("Структура", "Есть начало, развитие мысли и завершение", "Structure", "The text has an opening, development, and conclusion."),
    ("Конкретность", "Есть примеры, а не только общие рассуждения", "Specificity", "The answer includes examples, not only general discussion."),
    ("Фактическая аккуратность", "Нет вымышленных фактов, дат, цитат и источников", "Factual care", "There are no fabricated facts, dates, quotations, or sources."),
    ("Стиль", "Тон соответствует задаче", "Style", "The tone fits the task."),
]
ASSIGNMENT_DRAFT_SCORES = [2, 2, 2, 1, 2, 2]

SELF_DRAFT = [2, 2, 2, 1, 2, 2, 2, 2, 1]
EDGE_NOTES = {
    "edge_too_general_topic": (
        "The answer becomes a broad overview of AI applications instead of a focused mini-essay about verification.",
        "It follows the deliberately broad request but does not preserve the lab's narrower task; name the reader and intended format.",
        "Add the intended audience, genre, central question, and two required examples.",
    ),
    "edge_hallucination_risk": (
        "The response returned three references. Two had incorrect author/year attributions: DOI 10.1145/3571730 is Ji et al. (2023), not Rawte et al.; arXiv:2005.00661 is Maynez et al. (2020), not Zhang et al. (2023). A third Ji et al. citation repeated the first DOI.",
        "The answer produced plausible-looking citations, including incorrect author/year metadata. The two records were checked against the [ACM DOI record](https://doi.org/10.1145/3571730) and the [official arXiv record](https://arxiv.org/abs/2005.00661).",
        "Check every title, author list, year, and DOI against the publisher or repository record; do not infer verification from a valid-looking DOI.",
    ),
    "edge_audience_change": (
        "The answer is rewritten for parents using the supplied preceding essay as context.",
        "The context is now explicit and the model can adapt it; inspect whether tone and examples actually change for parents.",
        "Name the parents' needs and request one concrete parent-facing example.",
    ),
    "edge_conflicting_requirements": (
        "The model has to balance a request for detail with a two-sentence maximum.",
        "The output is concise; the length constraint necessarily limits the number of explanations.",
        "Prioritize the sentence limit and ask for one compact example, or remove the conflicting demand for detail.",
    ),
    "edge_strict_json_format": (
        "The parser confirms valid JSON and all five required keys.",
        "Valid JSON does not establish factual accuracy.",
        "Parse the JSON, then check its claims separately.",
    ),
}

EDGE_NOTES_RU = {
    "edge_too_general_topic": (
        "Ответ превращается в общий обзор применений ИИ вместо мини-эссе о проверке ответов.",
        "Он следует намеренно широкому запросу, но теряет узкую задачу лабораторной: не названы аудитория и нужный жанр.",
        "Указать аудиторию, жанр, главный вопрос и два обязательных примера.",
    ),
    "edge_hallucination_risk": (
        "Ответ содержит три ссылки. В двух неверно указаны авторы/год: DOI 10.1145/3571730 относится к Ji et al. (2023), а не Rawte et al.; arXiv:2005.00661 — к Maynez et al. (2020), а не Zhang et al. (2023). Третья ссылка Ji et al. повторяет первый DOI.",
        "Запрос на источники привёл к правдоподобным, но частично неверным ссылкам. Записи сверены с [записью ACM DOI](https://doi.org/10.1145/3571730) и [официальной записью arXiv](https://arxiv.org/abs/2005.00661).",
        "Проверять название, авторов, год и DOI по записи издателя или репозитория; корректный формат DOI не означает, что ссылка подтверждена.",
    ),
    "edge_audience_change": (
        "Модель переписала эссе для родителей, используя предыдущий ответ как контекст.",
        "Контекст передан явно. Далее нужно проверить, действительно ли изменились тон и примеры для родителей.",
        "Уточнить потребности родителей и попросить один пример для этой аудитории.",
    ),
    "edge_conflicting_requirements": (
        "Модель должна была совместить подробное объяснение с ограничением в два предложения.",
        "Ответ получился кратким; ограничение длины неизбежно уменьшает подробность.",
        "Поставить лимит предложений выше и попросить один краткий пример либо убрать противоречивое требование подробности.",
    ),
    "edge_strict_json_format": (
        "Парсер подтвердил корректный JSON и пять обязательных ключей.",
        "Корректный JSON не подтверждает фактическую точность.",
        "Проверить JSON парсером, затем отдельно проверить утверждения.",
    ),
}

CRITERIA_CHECK_RU = [
    "Прямой ответ на задачу", "Уровень языка соответствует аудитории",
    "Вступление, тезис, примеры, пояснения и вывод", "Два различимых примера",
    "Нет неподтверждённых конкретных фактов и ссылок", "Спокойный тон и осторожные формулировки",
    "Подсчёт слов по пробелам: 180–220", "В выводе нет нового аргумента", "Достаточно небольшой правки",
]
CRITERIA_CHECK_EN = [
    "Directly answers the assigned task", "Language level fits the intended audience",
    "Introduction, thesis, examples, explanations, and conclusion", "Two distinguishable examples",
    "No unsupported specific facts or citations", "Calm tone and cautious wording",
    "Whitespace-separated word count: 180–220", "No new argument in the conclusion", "Requires only minor editing",
]
REVIEW_COMMENTS_RU = [
    "Ответ напрямую раскрывает тему необходимости проверки ответов ИИ.",
    "Текст понятен ученикам 9–10 классов.",
    "Есть логичная структура: вступление, тезис, примеры, пояснения и вывод.",
    "Приведены два примера сбоев ИИ: вымышленные сведения и устаревшие данные.",
    "В ответе нет вымышленных фактов, цитат, источников или дат.",
    "Тон на всём протяжении спокойный, учебный и осторожный.",
    "Ответ соответствует диапазону 180–220 слов.",
    "Вывод не вводит новые аргументы и сохраняет осторожность.",
    "Текст можно использовать после небольшой правки; крупных изменений не требуется.",
]
QUALITY_RU = [
    "Прямо отвечает на выбранную тему", "Понятен ученикам 9–10 классов",
    "Логичная структура: вступление, тезис, примеры, пояснения, вывод",
    "Не менее двух конкретных примеров", "Нет вымышленных фактов, цитат, источников или дат",
    "Спокойный, учебный и осторожный стиль", "Объём 180–220 слов",
    "В выводе не появляется новая аргументация", "Можно использовать после небольшой ручной правки",
]
ERRORS_RU = [
    "Вымышленные ссылки или источники", "Выдуманная статистика или точные числа без основания",
    "Чрезмерно уверенные утверждения", "Сложный или снисходительный язык",
    "Отсутствие обязательных частей структуры", "Существенное отклонение от целевого объёма",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(cell(value) for value in row) + " |" for row in rows],
    ])


def fenced(text: str) -> str:
    return "```text\n" + text.rstrip() + "\n```"


def build(run_dir: str | Path, language: str = "ru", student: str = "", group: str = "") -> str:
    run_dir = Path(run_dir).resolve()
    if language not in {"ru", "en"}:
        raise ValueError("language must be 'ru' or 'en'")
    manifest = read_json(run_dir / "manifest.json")
    rows = read_json(run_dir / "lab2_results.json")
    prompts = read_json(run_dir / "prompts_used.json")
    topic = read_json(run_dir / "task1_topic_criteria.json")
    examples = read_json(run_dir / "task4_few_shot_examples.json")
    edge_results = read_json(run_dir / "task8_edge_cases.json")
    evaluations = read_json(run_dir / "task9_evaluations.json")
    config = manifest["config"]
    model_a, model_b = config["primary_model"], config["secondary_model"]
    label = (lambda en, ru: en) if language == "en" else (lambda en, ru: ru)
    criteria = CRITERIA_EN if language == "en" else CRITERIA_RU
    criteria_check = CRITERIA_CHECK_EN if language == "en" else CRITERIA_CHECK_RU
    edge_notes = EDGE_NOTES if language == "en" else EDGE_NOTES_RU
    by_name_model = {(r["prompt_name"], r["model"]): r for r in rows}
    primary_v3 = by_name_model.get(("v3", model_a))
    review = next((e for e in evaluations if e.get("evaluator_model") == model_b), {})
    review_data = review.get("evaluation", {})
    scores = review_data.get("scores", {})
    successful = [r for r in rows if r["status"] == "ok"]
    latencies_a = [r["latency_sec"] for r in successful if r["model"] == model_a]
    latencies_b = [r["latency_sec"] for r in successful if r["model"] == model_b]
    status_counts = {s: sum(r["status"] == s for r in rows) for s in ("ok", "error", "truncated")}

    sections: list[str] = []
    add = sections.append
    add(f"# {label('Lab 2 Report on Prompt Engineering and Few Shot Prompting', 'Отчёт по лабораторной работе №2 по промпт-инжинирингу и few-shot prompting')}\n")
    add(f"## {label('1. Cover page', '1. Титульный лист')}\n\n**ITMO University / Университет ИТМО**  \n**{label('Course', 'Дисциплина')}:** {label('Prompt Engineering', 'Промпт-инжиниринг')}  \n**{label('Student', 'Студент')}:** {student or '____________________'}  \n**{label('Group', 'Группа')}:** {group or '____________________'}  \n**{label('Experiment time', 'Время эксперимента')}:** {manifest['timestamp']}  \n**{label('Run folder', 'Папка запуска')}:** `{run_dir.relative_to(ROOT)}`  \n**{label('Models', 'Модели')}:** A `{model_a}`; B `{model_b}`.\n")
    add(f"## {label('2. Objective and method', '2. Цель и метод')}\n\n{label('The objective was to design and compare a simple prompt, a structured prompt (V1), a one-shot prompt (V2), and a few-shot prompt (V3), then test edge cases and obtain an independent review. Model A produced the baseline and final essay; identical V1, V2, and V3 prompt strings were sent to both models. Model B reviewed Model A’s V3 answer in a separate request. Prompts and model answers are preserved verbatim in their original English.', 'Цель — спроектировать и сравнить простой промпт, структурированный промпт V1, one-shot вариант V2 и few-shot вариант V3, а затем проверить слабые места и получить независимую рецензию. Модель А создала базовый и итоговый текст; одинаковые строки промптов V1, V2 и V3 были отправлены обеим моделям. Модель Б отдельно рецензировала ответ V3 модели А. Промпты и ответы моделей сохранены без изменений на исходном английском языке.')}\n\n{label('Measured word counts use whitespace-separated tokens in the saved answer. The script’s automatic counts for links, years, numbers, and caution/confidence markers are indicators only; they do not establish factual accuracy. The run used one request per planned cell, except the final answer can have at most two attempts; this run required one attempt.', 'Объём считался по токенам, разделённым пробелами, в сохранённом ответе. Автоматические счётчики ссылок, годов, чисел и маркеров осторожности/уверенности — только индикаторы и не доказывают фактическую точность. Для каждой ячейки был запланирован один запрос; для итогового ответа допускается не более двух попыток. В этом запуске хватило одной попытки.')}\n")
    hash_note = label(
        f"The report parser was subsequently improved to recover the JSON object from the reviewer’s fenced response; the original model response remains unchanged in `lab2_results.json`. The manifest source-text hash is `{manifest['source_text_hash']}`. No API key is stored in the run.",
        f"После запуска парсер отчёта был улучшен: теперь он извлекает JSON из ответа рецензента в блоке кода; исходный ответ модели в `lab2_results.json` не менялся. Хеш исходного текста в манифесте: `{manifest['source_text_hash']}`. Ключ API в результатах не сохранялся.",
    )
    add(f"## {label('3. Models and run conditions', '3. Модели и условия запуска')}\n\n" + md_table([label('Parameter', 'Параметр'), label('Value', 'Значение')], [
        [label('Model A', 'Модель A'), model_a], [label('Model B', 'Модель Б'), model_b],
        [label('API profile', 'Профиль API'), config['api_profile']], [label('Endpoint', 'Endpoint'), config['base_url']],
        [label('Temperature', 'Температура'), config['temperature']], [label('Max output tokens', 'Максимум выходных токенов'), config['max_tokens']],
        [label('Timeout', 'Таймаут'), f"{config.get('timeout', 180)} s"],
        [label('Requests', 'Запросы'), f"{status_counts['ok']} {label('successful', 'успешных')}, {status_counts['error']} {label('error' if status_counts['error'] == 1 else 'errors', 'ошибка' if status_counts['error'] == 1 else 'ошибок')}, {status_counts['truncated']} {label('truncated', 'усечённых')}"],
    ]) + f"\n\n{label('Generation-time runner SHA-256', 'SHA-256 runner-кода на момент запуска')}: `{manifest['runner_hash']}`. {hash_note}\n")

    topic_rows = [
        [label('What topic was selected?', 'Какая тема выбрана?'), 'Почему ответы ИИ нужно проверять' if language == 'ru' else 'Why AI answers need verification'],
        [label('What should the model do?', 'Что должна сделать модель?'), 'Написать мини-эссе для учеников 9–10 классов о том, почему ответы ИИ нужно проверять, привести два конкретных примера и сделать осторожный вывод.' if language == 'ru' else 'Write a mini-essay for 9th–10th grade students explaining why AI answers need verification, give two concrete examples, and reach a cautious conclusion.'],
        [label('Who is the text for?', 'Для кого предназначен текст?'), 'Ученики 9–10 классов (14–16 лет)' if language == 'ru' else 'Students in grades 9–10 (ages 14–16)'],
        [label('Where could this text be used?', 'Где такой текст мог бы использоваться?'), 'На уроке информатики или цифровой грамотности; как учебный материал о проверке информации, созданной ИИ.' if language == 'ru' else 'In a computer science or digital literacy class as learning material about checking AI-generated information.'],
        [label('What should a good result look like?', 'Каким должен быть хороший результат?'), 'Мини-эссе на 180–220 слов с понятной структурой, двумя пояснёнными примерами, фактической аккуратностью и осторожным выводом.' if language == 'ru' else 'A 180–220-word mini-essay with a clear structure, two explained examples, factual care, and a cautious conclusion.'],
        [label('Which model errors are especially undesirable here?', 'Какие ошибки модели здесь особенно нежелательны?'), 'Вымышленные источники или факты; необоснованные даты и числа; чрезмерная уверенность; отсутствие нужной структуры; неподходящий аудитории язык.' if language == 'ru' else 'Fabricated sources or facts; unsupported dates or numbers; overconfidence; missing required structure; language unsuitable for the audience.'],
    ]
    add(f"## {label('4. Task 1: Topic and task definition', '4. Задание 1: выбор темы и задачи')}\n\n" + md_table([label('Question', 'Вопрос'), label('Answer', 'Ответ')], topic_rows) + "\n")
    assignment_criteria = [
        [criterion[0] if language == 'ru' else criterion[2], criterion[1] if language == 'ru' else criterion[3], ASSIGNMENT_DRAFT_SCORES[i]]
        for i, criterion in enumerate(ASSIGNMENT_RUBRIC)
    ]
    add(f"## {label('5. Task 2: Quality criteria and rubric', '5. Задание 2: критерии качества и шкала')}\n\n{label('The first table reproduces the six core criteria and descriptions from the assignment. Scores are a draft assessment of Model A’s final V3 answer for the student to confirm. The second table adds operational checks used in this experiment.', 'В первой таблице приведены шесть основных критериев и формулировок из задания. Оценки ответа модели А на финальный промпт V3 являются черновой самооценкой и требуют подтверждения студентом. Во второй таблице отдельно указаны дополнительные операционные проверки эксперимента.')}\n\n" + md_table([label('Criterion', 'Критерий'), label('How to tell it is met', 'Как понять, что он выполнен'), label('Score 0–2', 'Оценка 0–2')], assignment_criteria) + f"\n\n{label('Scale', 'Шкала')}: {label('0 = not met; 1 = partly met; 2 = met. Draft scores must be reviewed by the student.', '0 — критерий не выполнен; 1 — выполнен частично; 2 — выполнен хорошо. Черновые оценки нужно проверить и подтвердить.') }\n\n{label('Supplementary operational rubric', 'Дополнительная операционная рубрика')}\n\n" + md_table([label('Criterion', 'Критерий'), label('How checked', 'Как проверялся'), label('Draft self-score 0–2', 'Черновая самооценка 0–2')], [
        [criteria[i], criteria_check[i], SELF_DRAFT[i]]
        for i in range(9)
    ]) + f"\n\n{label('Scale', 'Шкала')}: {label('0 = not met; 1 = partly met; 2 = met. The draft scores are justified again in the self-review section.', '0 — не выполнен; 1 — выполнен частично; 2 — выполнен. Обоснование черновых баллов дано в разделе самооценки.')}\n")

    simple = by_name_model[("simple", model_a)]
    assessment = label(
        f"the answer is {simple['word_count']} words, which is over the 180–220 target; the prompt does not specify audience, structure, examples, or cautious style. Three observed shortcomings are: (1) length above target; (2) no requirement for two explained examples; (3) no target age or format. These observations motivate V1.",
        f"ответ содержит {simple['word_count']} слов и превышает целевой объём 180–220; промпт не задаёт аудиторию, структуру, примеры и осторожный стиль. Недостатки: (1) объём выше цели; (2) нет требования о двух пояснённых примерах; (3) не заданы возраст и формат. Это мотивирует V1.",
    )
    add(f"## {label('6. Task 3: Simple prompt and first result', '6. Задание 3: простой промпт и первый результат')}\n\n**{label('Prompt', 'Промпт')}:**\n\n{fenced(prompts['simple'])}\n\n**{label('Model A answer', 'Ответ модели А')}:** ({simple['word_count']} {label('words', 'слов')})\n\n{fenced(simple['answer'])}\n\n{label('Draft assessment', 'Черновая оценка')}: {assessment}\n")

    add(f"## {label('7. Task 4: Structured prompt design', '7. Задание 4: проектирование структурированного промпта')}\n\n" + md_table([label('Prompt part', 'Часть промпта'), label('What was added', 'Что вы добавили'), label('Why it is needed', 'Зачем это нужно')], [
        [label('Role', 'Роль'), label('Educational content writer specializing in teen digital literacy', 'Автор учебных текстов о цифровой грамотности подростков'), label('Sets expected expertise and register', 'Задаёт область и регистр')],
        [label('Task', 'Задача'), label('Explain why AI answers need verification', 'Объяснить, почему ответы ИИ нужно проверять'), label('Defines the central question', 'Фиксирует основной вопрос')],
        [label('Audience', 'Аудитория'), label('Grades 9–10, ages 14–16', '9–10 класс, 14–16 лет'), label('Guides vocabulary and explanation', 'Задаёт словарь и уровень пояснений')],
        [label('Context', 'Контекст'), label('Teen digital literacy is implicit in the role; classroom setting is not named explicitly', 'Цифровая грамотность подростков заложена в роли, но школьный контекст явно не назван'), label('Could be made more explicit in a future revision', 'В следующей версии можно задать явнее')],
        [label('Content and structure', 'Содержание и структура'), label('Short introduction, central point, two explained failures, cautious conclusion', 'Короткое вступление, тезис, два пояснённых сбоя, осторожный вывод'), label('Makes expected parts observable', 'Делает структуру проверяемой')],
        [label('Constraints', 'Ограничения'), label('180–220 words; no fabricated facts, dates, sources, or statistics; avoid absolutes', '180–220 слов; без вымышленных фактов, дат, источников и статистики; без категоричности'), label('Limits scope and unsupported precision', 'Ограничивает объём и недоказуемую точность')],
        [label('Format', 'Формат'), label('Plain-text paragraphs', 'Обычные текстовые абзацы'), label('Makes the output easy to reuse', 'Упрощает дальнейшее использование')],
        [label('Quality criteria', 'Критерии'), label('Embedded as content requirements; not a separate numbered checklist in V1', 'Встроены в требования, а не даны отдельным списком'), label('Supports review; a future version could include an explicit checklist', 'Помогают оценке; можно добавить явный список')],
    ]) + "\n")

    add(f"## {label('8. Task 5: V1 prompt and cross-model comparison', '8. Задание 5: промпт V1 и сравнение моделей')}\n\n**V1 {label('verbatim', 'полностью')}:**\n\n{fenced(prompts['v1'])}\n\n")
    for model in (model_a, model_b):
        result = by_name_model[("v1", model)]
        add(f"**{model} — {result['status']}, {result['word_count']} {label('words', 'слов')}, {result['latency_sec']} s:**\n\n{fenced(result['answer']) if result['answer'] else label('No answer returned; the failure is preserved in the run data.', 'Ответ не получен; ошибка сохранена в данных запуска.')}\n\n")
    add(f"**{label('Required simple-prompt versus V1 comparison', 'Сравнение простого промпта и V1 по шаблону задания')}:**\n\n" + md_table([label('Criterion', 'Критерий'), label('Simple prompt', 'Простой промпт'), label('Prompt V1', 'Промпт V1'), label('Comment', 'Комментарий')], [
        [label('Topic relevance', 'Соответствие теме'), label('Addresses verification of AI answers.', 'Рассматривает проверку ответов ИИ.'), label('Same central topic is stated explicitly.', 'Та же тема задана явно.'), label('Both stay on topic.', 'Оба ответа остаются в теме.')],
        [label('Audience clarity', 'Понятность аудитории'), label('Students are mentioned, but age and grade are unspecified.', 'Упомянуты ученики, возраст и класс не заданы.'), label('Grades 9–10 (ages 14–16) are specified.', 'Указаны 9–10 классы (14–16 лет).'), label('V1 gives the model a usable audience definition.', 'В V1 аудитория задана точнее.')],
        [label('Structure', 'Структура'), label('The answer has headings and a closing paragraph, but no requested outline.', 'Есть подзаголовки и заключительный абзац, но структура не была задана.'), label('A five-part outline is required; the returned answer is incomplete and stops mid-sentence.', 'Задана структура из пяти частей, но ответ обрывается на полуслове.'), label('V1 is clearer, but this output is incomplete.', 'Промпт V1 точнее, однако ответ неполный.')],
        [label('Specificity', 'Конкретность'), label('Discusses failure modes generally; two examples are not required.', 'Сбои обсуждаются в общем виде; два примера не требуются.'), label('Two examples are required, but the captured answer stops before providing them.', 'Запрошены два примера, но сохранённый ответ обрывается до их приведения.'), label('The V1 requirement was not fulfilled in this response.', 'В этом ответе требование V1 не выполнено.')],
        [label('Style', 'Стиль'), label('Formal educational tone; audience is not tailored.', 'Формальный учебный тон; аудитория не уточнена.'), label('Calm, plain language for teenagers is requested.', 'Запрошен спокойный и простой язык для подростков.'), label('V1 states the style more precisely.', 'В V1 стиль задан точнее.')],
        [label('Factual care', 'Фактическая аккуратность'), label('No sources are cited; factual claims were not independently verified.', 'Источники не указаны; факты независимо не проверялись.'), label('Fabrication is prohibited; the incomplete answer contains no citations.', 'Вымысел запрещён; в неполном ответе нет ссылок.'), label('Prompt constraints do not replace fact-checking.', 'Ограничения промпта не заменяют проверку фактов.')],
    ]) + "\n")

    add(f"{label('Claude Haiku’s V1 response is substantially under the target at 95 words and ends mid-sentence at “One common issue is Overloaded,” despite finish_reason=stop. Llama’s is also short at 166 words. Neither response meets the range; specifying a range did not guarantee compliance.', 'Ответ Claude Haiku на V1 заметно короче требуемого — 95 слов — и заканчивается на полуслове фразой “One common issue is Overloaded”, хотя finish_reason равен stop. Ответ Llama тоже короче — 166 слов. Ни один ответ не попал в диапазон; указание объёма не гарантировало его соблюдение.')}\n")

    add(f"## {label('9. Task 6: Good and bad few-shot examples', '9. Задание 6: неудачный и удачный few-shot пример')}\n\n" + md_table([label('Example type', 'Тип примера'), label('Example text', 'Текст примера'), label('Why it is good or weak', 'Почему он удачный или неудачный')], [
        [label('Weak', 'Неудачный'), examples['bad_example']['text'], examples['bad_example']['why_weak'] if language == 'en' else 'Слишком общее утверждение: нет конкретной ситуации, условного контекста; фраза похожа на лозунг.'],
        [label('Stronger', 'Удачный'), examples['good_example']['text'], examples['good_example']['why_strong'] if language == 'en' else 'Показана ситуация ученика, есть условие («если использовать для объяснения»), различие между полезным и неудачным применением и осторожный тон.'],
    ]) + f"\n\n{label('The stronger example concerns using AI to learn a difficult concept; it is related to education but does not repeat the essay’s exact verification task.', 'Удачный пример касается применения ИИ для изучения сложной темы: он связан с образованием, но не повторяет точную задачу эссе о проверке ответов.')}\n")

    add(f"## {label('10. Task 7: V2 one-shot prompt', '10. Задание 7: one-shot промпт V2')}\n\n**V2 {label('verbatim', 'полностью')}:**\n\n{fenced(prompts['v2'])}\n\n")
    for model in (model_a, model_b):
        result = by_name_model.get(("v2", model))
        if result:
            add(f"**{model} — {result['status']}, {result['word_count']} {label('words', 'слов')}, {result['latency_sec']} s:**\n\n{fenced(result['answer']) if result['answer'] else label('The request failed and returned no answer.', 'Запрос завершился ошибкой, ответ не получен.')}\n\n")
    add(f"{label('Model A’s V2 output is 203 words, inside the requested range, compared with its 95-word V1 output. It adds more concrete formulations, including invented historical details and fake scientist names as hypothetical examples. Model B’s V2 request returned HTTP 502 (“Request failed”) after 77.191 seconds; there is no B answer to compare for this cell. The one-shot example may have helped Model A reach the length target, but one run cannot establish causation.', 'Ответ модели А на V2 содержит 203 слова и попадает в диапазон; V1 у неё был 95 слов. В тексте появились более конкретные формулировки, включая гипотетические примеры с вымышленными историческими деталями и именами учёных. Запрос модели Б на V2 вернул HTTP 502 («Request failed») через 77,191 секунды; сравнить ответ Б в этой ячейке нельзя. One-shot пример мог помочь модели А попасть в объём, но один запуск не доказывает причинность.')}\n")

    add(f"**{label('Required V1/V2 comparison', 'Сравнение V1 и V2 по таблице задания')}:**\n\n" + md_table([label('Question', 'Вопрос'), label('Answer', 'Ответ')], [
        [label('What changed after adding the example?', 'Что изменилось после добавления примера?'), label('V2 includes one example about asking AI to explain a difficult topic step by step.', 'V2 содержит один пример о просьбе к ИИ объяснить сложную тему по шагам.')],
        [label('Did the answer become more specific?', 'Стал ли ответ конкретнее?'), label('Partly: Model A moved from a general V1 discussion to two named failure types in V2; the examples remain hypothetical.', 'Частично: вместо общего обсуждения в V1 модель А назвала в V2 два типа сбоев; примеры остаются гипотетическими.')],
        [label('Did the style move closer to the target?', 'Стал ли стиль ближе к нужному?'), label('Yes: the V2 answer is plain and student-facing and has 203 words, within the target.', 'Да: ответ V2 написан простым языком для ученика и содержит 203 слова, то есть попадает в целевой диапазон.')],
        [label('Did the model copy the example?', 'Появилось ли копирование примера?'), label('No literal copying was identified; the answer uses its own examples.', 'Дословного копирования не выявлено; модель использовала собственные примеры.')],
        [label('Should the example remain in the prompt?', 'Стоит ли оставлять пример в промпте?'), label('Keep the teaching pattern, but use a neutral hypothetical example and avoid fake names or citations.', 'Сохранить обучающий приём, но использовать нейтральный гипотетический пример без вымышленных имён и ссылок.')],
    ]) + "\n")


    add(f"## {label('11. Task 8: V3 few-shot prompt and comparison', '11. Задание 8: few-shot промпт V3 и сравнение')}\n\n**V3 {label('verbatim', 'полностью')}:**\n\n{fenced(prompts['v3'])}\n\n")
    for model in (model_a, model_b):
        result = by_name_model.get(("v3", model))
        if result:
            add(f"**{model} — {result['status']}, {result['word_count']} {label('words', 'слов')}, {result['latency_sec']} s; caution markers {result['caution_markers_count']}, confident markers {result['confident_markers_count']}:**\n\n{fenced(result['answer']) if result['answer'] else label('No answer returned.', 'Ответ не получен.')}\n\n")
    add(f"**{label('Required version comparison (Model A; draft scores 0–2)', 'Сравнение версий по критериям задания (модель A; черновые оценки 0–2)')}:**\n\n" + md_table([label('Criterion', 'Критерий'), label('V1 without examples', 'V1 без примеров'), label('V2 with one example', 'V2 с одним примером'), label('V3 with several examples', 'V3 с несколькими примерами'), label('Comment', 'Комментарий')], [
        [label('Topic relevance', 'Соответствие теме'), '2', '2', '2', label('All three address verification of AI answers.', 'Все три посвящены проверке ответов ИИ.')],
        [label('Audience clarity', 'Понятность аудитории'), '2', '2', '2', label('All name grades 9–10; V1 is incomplete.', 'Во всех названы 9–10 классы; V1 обрывается.')],
        [label('Structure', 'Структура'), '1', '2', '2', label('V1 ends mid-sentence; V2 and V3 contain the requested parts.', 'V1 обрывается на полуслове; V2 и V3 содержат запрошенные части.')],
        [label('Specificity', 'Конкретность'), '1', '1', '1', label('V2 and V3 name failure types, but neither gives a detailed verifiable case.', 'В V2 и V3 названы типы сбоев, но нет подробного проверяемого случая.')],
        [label('Style', 'Стиль'), '2', '2', '2', label('All use an educational tone; audience fit is clearer in the structured prompts.', 'Тон учебный во всех версиях; структурированные промпты точнее задают аудиторию.')],
        [label('Cautious wording', 'Осторожность формулировок'), '1', '2', '2', label('V2 and V3 explicitly advise checking important claims.', 'В V2 и V3 прямо рекомендуется проверять важные утверждения.')],
        [label('No copying from examples', 'Отсутствие копирования примеров'), label('Not applicable', 'Нет примеров'), '2', '2', label('No literal copying detected; the invented-citation example remains a priming risk.', 'Дословного копирования нет; вымышленная цитата всё же может провоцировать подражание.')],
    ]) + f"\n\n{label('These are draft human judgments, not scores emitted by the API. Model B’s V2 cell is unavailable because its request failed with HTTP 502.', 'Это черновые оценки человека, а не оценки API. Ответ модели Б на V2 отсутствует из-за ошибки HTTP 502.') }\n")


    add(f"{label('Model A’s V3 answer has 214 words and meets the target. It uses two explained failure types (plausible invented details and stale information), a cautious conclusion, and does not repeat the named example citation from the few-shot block. Model B’s V3 answer has 163 words, below target, although it contains a fake-citation example and a stale-knowledge example. On this run, V3 is the strongest answer from Model A against the word and structure requirements; it is not proof that V3 or Model A is universally best. The prompt contains three short teaching examples, but the intentionally fake citation could prime imitation and should be removed or explicitly labeled as a non-reusable placeholder in future work.', 'Ответ модели А на V3 содержит 214 слов и попадает в диапазон. Он поясняет два типа сбоев (правдоподобные вымышленные детали и устаревшие сведения), завершает осторожным выводом и не повторяет конкретную цитату из few-shot блока. Ответ модели Б на V3 содержит 163 слова — меньше нормы, хотя в нём есть примеры вымышленной ссылки и устаревших знаний. В этом запуске V3 — лучший ответ модели А по требованиям объёма и структуры; это не доказывает универсальное превосходство V3 или модели А. В промпте три коротких обучающих примера, но намеренно вымышленная ссылка может провоцировать подражание; в дальнейшем её стоит убрать или явно обозначить как непригодный для повторения шаблон.')}\n")

    add(f"## {label('12. Task 9: Analysis of few-shot effects', '12. Задание 9: анализ влияния few-shot примеров')}\n\n" + md_table([label('Version / model', 'Версия / модель'), label('Words', 'Слова'), label('Latency (s)', 'Латентность (с)'), label('Caution / confident', 'Осторожность / уверенность'), label('Outcome', 'Результат')], [
        [r['prompt_name'].upper(), r['model'], r['word_count'], r['latency_sec'], f"{r['caution_markers_count']} / {r['confident_markers_count']}", r['status']]
        for r in rows if r['prompt_name'] in {'v1', 'v2', 'v3'}
    ]) + "\n")
    if language == "en":
        answers = [
            "1. V2 used the student-learning example; V3 used examples for specificity, explaining relevance, and a cautious conclusion.",
            "2. They target concrete writing skills rather than copy the final topic.",
            "3. The examples were intended to teach specificity, explanation, and calibrated conclusions.",
            "4. Model A’s output grew from 95 words (V1) to 203 (V2); Model B’s V2 call failed.",
            "5. Model A’s V3 answer reached 214 words and included two explained risk types; Model B’s answer was 163 words.",
            "6. Yes. The fabricated citation in V3 is a priming risk; neither V3 answer copied its title verbatim.",
            "7. Compare word count, structure, concrete examples, overlap with example wording, and both model outputs.",
            "8. The example that links an example to why it matters is likely most useful, but this is an analytical judgment, not a measured causal effect.",
            "9. The citation example could be removed because it conflicts with the no-fabrication constraint and may prime invented citations.",
            "10. Use neutral, clearly hypothetical examples and add a checklist for the nine quality criteria.",
        ]
    else:
        answers = [
            "1. В V2 добавлен пример об использовании ИИ для изучения сложной темы; V3 содержит примеры конкретики, пояснения значимости и осторожного вывода.",
            "2. Примеры показывают отдельные навыки письма и не повторяют тему итогового эссе дословно.",
            "3. Они должны были обучить конкретности, пояснению и осторожному заключению.",
            "4. Ответ А вырос с 95 слов в V1 до 203 в V2; запрос модели Б на V2 завершился ошибкой.",
            "5. Ответ А на V3 достиг 214 слов и пояснил два типа риска; ответ Б содержит 163 слова.",
            "6. Да. Вымышленная цитата в V3 создаёт риск подражания; ни один из ответов не скопировал её название дословно.",
            "7. Сопоставляются объём, структура, конкретность, совпадение с примерами и ответы обеих моделей.",
            "8. Вероятно, полезнее пример, который связывает пример с его значением; это аналитическая оценка, а не измеренная причинность.",
            "9. Цитату можно убрать: она конфликтует с запретом на вымышленные источники и может провоцировать такие ссылки.",
            "10. Использовать нейтральные явно гипотетические примеры и добавить проверочный список из девяти критериев.",
        ]
    add("\n".join(answers) + "\n")
    add(f"\n{label('Assignment example analysis table', 'Таблица анализа примеров из задания')}\n\n" + md_table([label('Example', 'Пример'), label('What it should show', 'Что он должен был показать'), label('Helped / did not help', 'Помог / не помог'), label('Why', 'Почему')], [
        [label('Example 1: concrete argument', 'Пример 1: конкретный аргумент'), label('Turn a vague claim into a specific illustration.', 'Заменить общее утверждение конкретной иллюстрацией.'), label('Partly helped', 'Помог частично'), label('The V3 essay describes invented event details, but does not give a verifiable concrete case; the fake-citation example also risks priming.', 'В эссе V3 описаны вымышленные детали события, но конкретный проверяемый случай не приведён; пример ложной ссылки может провоцировать подражание.')],
        [label('Example 2: explain relevance', 'Пример 2: пояснить значимость'), label('Connect the example to why it matters to a student.', 'Связать пример с его значением для ученика.'), label('Helped', 'Помог'), label('Model A explains that a student could copy false details into an essay and be corrected by a teacher.', 'Модель А поясняет, что ученик может перенести ложные детали в эссе и получить замечание учителя.')],
        [label('Example 3: cautious conclusion', 'Пример 3: осторожный вывод'), label('Avoid an absolute conclusion and recommend proportionate checking.', 'Избежать категоричного вывода и предложить разумную проверку.'), label('Helped', 'Помог'), label('The V3 answer recommends checking important claims against reliable sources instead of rejecting AI entirely.', 'Ответ V3 рекомендует сверять важные утверждения с надёжными источниками, а не полностью отказываться от ИИ.')],
    ]) + "\n")

    add(f"## {label('13. Task 10: Edge-case tests', '13. Задание 10: проверка слабых мест')}\n\n{label('Five edge checks were run with Model A. Each prompt and output is saved in the run JSON. The audience-change request included the preceding Model A V3 essay, so the follow-up had its necessary context.', 'Пять граничных проверок выполнены моделью А. Промпты и ответы сохранены в JSON запуска. В запросе о смене аудитории был передан предыдущий ответ V3 модели А, поэтому контекст не потерян.')}\n\n")
    edge_rows = []
    for r in edge_results:
        name = r['case']
        observed, issue, improve = edge_notes["edge_" + name]
        edge_rows.append([label(name, name), r['description'], f"{r['result']['status']}: {observed}", issue, improve])
    add(md_table([label('Check', 'Проверка'), label('What was changed', 'Что вы изменили'), label('What the model did', 'Что сделала модель'), label('Problem that appeared', 'Какая проблема появилась'), label('How to improve the prompt', 'Как можно улучшить промпт')], edge_rows) + "\n")
    strict_case = next((r for r in rows if r['prompt_name'] == 'edge_strict_json_format'), {})
    try:
        strict_text = strict_case.get('answer', '').strip()
        if strict_text.startswith('```'):
            strict_text = strict_text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
        strict_value = json.loads(strict_text)
        strict_valid = isinstance(strict_value, dict) and set(strict_value) == {'introduction', 'main_point', 'example_1', 'example_2', 'conclusion'}
    except (ValueError, TypeError):
        strict_valid = False
    strict_status = label('valid JSON with all five required keys', 'корректный JSON со всеми пятью обязательными ключами') if strict_valid else label('invalid JSON or missing required keys', 'некорректный JSON или отсутствуют обязательные ключи')
    add(f"{label('Manual citation check', 'Ручная проверка ссылок')}: {label('The hallucination-risk response included two mismatched author/year attributions; one DOI correctly identifies Ji et al. (2023), while the other identifies Maynez et al. (2020). The cited records are linked in the edge-case table.', 'в ответе на запрос о галлюцинациях обнаружены две ошибки в авторах/годе; одна ссылка корректно ведёт к работе Ji et al. (2023), другая — к Maynez et al. (2020). Записи приведены в ссылках таблицы граничных случаев.')}\n\n{label('Strict JSON result', 'Результат проверки JSON')}: {strict_status}. {label('The parser strips the code fence before validation. The request failure in Model B’s V2 cell is retained and excluded from quality comparisons.', 'Перед проверкой парсер удаляет оболочку блока кода. Ошибка запроса модели Б на V2 сохранена и исключена из качественного сравнения.')}\n")

    add(f"## {label('14. Task 11: Independent review by Model B', '14. Задание 11: независимая рецензия модели Б')}\n\n{label('Model B received the original task, audience and context, all nine criteria, the full V3 prompt, and Model A’s final V3 answer in a separate request. The response contained a fenced JSON object and extra prose. The report parser recovered the first valid JSON object; the full raw reviewer response is retained in the result record. The reviewer assigned 2/2 to every criterion, found no hallucinations, and said the conclusion could explain cross-checking in more detail. This review is advisory and is not independent fact verification.', 'Модель Б получила исходную задачу, аудиторию и контекст, все девять критериев, полный промпт V3 и итоговый ответ модели А в отдельном запросе. Ответ содержал JSON в блоке кода и дополнительный текст. Парсер отчёта извлёк первый корректный JSON-объект; исходный ответ рецензента сохранён. Рецензент поставил 2/2 по всем критериям, не указал галлюцинаций и отметил, что в выводе можно подробнее объяснить перекрёстную проверку. Рецензия носит рекомендательный характер и не является независимой проверкой фактов.')}\n\n")
    reviewer_rows = []
    for i, criterion in enumerate(criteria, 1):
        reviewer_score = scores.get(f"criterion_{i}", "—")
        explanation = review_data.get('score_explanations', {}).get(f"criterion_{i}", "") if language == 'en' else REVIEW_COMMENTS_RU[i-1]
        reviewer_rows.append([criterion, reviewer_score, explanation, SELF_DRAFT[i-1], label('Student to confirm', 'Подтвердить студенту')])
    def reviewer_comment(index: int) -> str:
        return review_data.get('score_explanations', {}).get(f'criterion_{index}', '') if language == 'en' else REVIEW_COMMENTS_RU[index - 1]

    assignment_review_rows = [
        [label('Task relevance', 'Соответствие задаче'), scores.get('criterion_1', '—'), reviewer_comment(1), label('Draft: partly agree', 'Черновик: скорее согласен(на)'), label('The essay stays on topic; student to confirm.', 'Текст соответствует теме; подтвердить студенту.')],
        [label('Audience clarity', 'Понятность аудитории'), scores.get('criterion_2', '—'), reviewer_comment(2), label('Draft: agree', 'Черновик: согласен(на)'), label('The language is accessible; student to confirm.', 'Язык доступен аудитории; подтвердить студенту.')],
        [label('Structure', 'Структура'), scores.get('criterion_3', '—'), reviewer_comment(3), label('Draft: agree', 'Черновик: согласен(на)'), label('The answer has an opening, examples, and conclusion.', 'В ответе есть вступление, примеры и вывод.')],
        [label('Specificity', 'Конкретность'), scores.get('criterion_4', '—'), reviewer_comment(4), label('Draft: partly disagree', 'Черновик: скорее не согласен(на)'), label('The 2/2 seems generous: the examples describe types of failure but remain broad.', 'Оценка 2/2 кажется завышенной: приведены типы сбоев, но примеры остаются общими.')],
        [label('Use of few-shot examples', 'Работа с few-shot примерами'), '—', label('No separate numeric score was returned.', 'Отдельная числовая оценка не дана.'), label('Draft: not enough evidence', 'Черновик: данных недостаточно'), label('The reviewer returned a separate copying field, not a score for example usefulness.', 'Рецензент вернул отдельное поле о копировании, но не оценку полезности примеров.')],
        [label('No copying from examples', 'Отсутствие копирования примеров'), '—', label(f"few_shot_copying: {review_data.get('few_shot_copying', 'not reported')}", f"Копирование few-shot: {review_data.get('few_shot_copying', 'не указано')}"), label('Draft: partly agree', 'Черновик: скорее согласен(на)'), label('No literal copying was identified, but the invented-citation example could prime imitation.', 'Дословного копирования не выявлено, но вымышленная цитата может провоцировать подражание.')],
        [label('Factual care', 'Фактическая аккуратность'), scores.get('criterion_5', '—'), reviewer_comment(5), label('Draft: partly agree', 'Черновик: скорее согласен(на)'), label('No citations or dates appear in the final essay; this does not verify every general claim.', 'В итоговом эссе нет ссылок и дат; это не подтверждает все общие утверждения.')],
        [label('Style', 'Стиль'), scores.get('criterion_6', '—'), reviewer_comment(6), label('Draft: agree', 'Черновик: согласен(на)'), label('The tone is calm and suitable for the stated audience.', 'Тон спокойный и подходит указанной аудитории.')],
        [label('Overall usability', 'Итоговая пригодность текста'), scores.get('criterion_9', '—'), reviewer_comment(9), label('Draft: partly agree', 'Черновик: скорее согласен(на)'), label('It meets the word range but still needs human fact and audience review.', 'Объём соблюдён, но нужна проверка фактов и соответствия аудитории человеком.')],
    ]
    add(f"\n**{label('Assignment reviewer table', 'Таблица оценки второй моделью по шаблону задания')}:**\n\n" + md_table([label('Criterion', 'Критерий'), label('Second model score 0–2', 'Оценка второй модели 0–2'), label('Second model comment', 'Комментарий второй модели'), label('Agree / disagree', 'Согласен(на) / не согласен(на)'), label('My comment', 'Мой комментарий')], assignment_review_rows) + f"\n\n{label('Scores and agreement statements above are a proposed draft for the student to review. A dash means the model did not return a numeric score for that criterion; no score was inferred.', 'Оценки и согласие выше приведены как черновое предложение для проверки студентом. Тире означает, что модель не поставила числовую оценку по этому критерию; оценка не додумывалась.') }\n")
    add(f"**{label('Expanded reviewer scores from the saved review response', 'Дополнительная таблица оценок из сохранённой рецензии')}:**\n\n" + md_table([label('Criterion', 'Критерий'), label('Model B', 'Модель Б'), label('Reviewer comment', 'Комментарий рецензента'), label('Draft self-score', 'Черновая самооценка'), label('Agreement', 'Согласие')], reviewer_rows) + "\n")
    add(f"**{label('Draft reflection for the student to confirm', 'Черновик рефлексии для подтверждения студентом')}:** {label('I agree that the essay is clear and appropriately cautious, and that the final paragraph could say more about how to cross-check claims. I would not accept the reviewer’s blanket 2/2 without qualification: the examples are concrete in type but not especially specific, and the result still needs a human check for factual accuracy and audience fit. These statements are proposed wording, not a record of the student’s personal view.', 'Я согласен(на), что текст понятен и достаточно осторожен, а в заключении можно подробнее описать перекрёстную проверку утверждений. Я бы не принимал(а) без оговорок одинаковую оценку 2/2: примеры конкретны по типу, но недостаточно детализированы, а фактическую точность и соответствие аудитории всё равно должен проверить человек. Это предложенный текст, а не зафиксированное личное мнение студента.')}\n")

    add(f"## {label('15. Task 12: Final Prompt Card', '15. Задание 12: финальная Prompt Card')}\n\n" + md_table([label('Field', 'Поле'), label('Content', 'Содержание')], [
        [label('Prompt name', 'Название промпта'), label('Evidence-aware student essay about checking AI answers', 'Учебное эссе о проверке ответов ИИ')],
        [label('Task the prompt is used for', 'Для какой задачи используется'), topic['task'] if language == 'en' else 'Подготовить мини-эссе о том, почему ответы ИИ нужно проверять, с двумя примерами и осторожным выводом.'],
        [label('Target audience', 'Целевая аудитория'), topic['audience'] if language == 'en' else 'Ученики 9–10 классов (14–16 лет)'],
        [label('Recommended model', 'Рекомендуемая модель'), f"{model_a} for this measured run; not a universal recommendation." if language == 'en' else f"{model_a} для этого запуска; это не универсальная рекомендация."],
        [label('Input', 'Входные данные'), label('Task and optional source material to verify', 'Задача и при необходимости проверяемые исходные материалы')],
        [label('Expected result', 'Ожидаемый результат'), label('180–220 word mini-essay with introduction, thesis, two explained examples and cautious conclusion', 'Мини-эссе на 180–220 слов: вступление, тезис, два пояснённых примера, осторожный вывод')],
        [label('Model role', 'Роль модели'), label('Educational writer for teen digital literacy', 'Автор образовательных текстов о цифровой грамотности подростков')],
        [label('Core requirements', 'Основные требования'), label('Plain language, two failure examples, explain relevance, distinguish prediction from verified fact', 'Понятный язык, два примера сбоев, пояснение значимости, различение вероятного текста и проверенных фактов')],
        [label('Restrictions', 'Ограничения'), label('No invented facts, quotations, sources, dates, statistics, or categorical claims', 'Без вымышленных фактов, цитат, источников, дат, статистики и чрезмерной категоричности')],
        [label('Output format', 'Формат ответа'), label('Plain-text paragraphs', 'Обычные текстовые абзацы')],
        [label('Few-shot examples', 'Few-shot примеры'), label('One non-topic-specific learning example plus three short style/argument patterns', 'Один пример об обучении вне точной темы и три кратких стилистических/аргументативных образца')],
        [label('What the few-shot examples demonstrate', 'Что показывают few-shot примеры'), label('Specificity, explanation of relevance, and a cautious conclusion', 'Конкретику, пояснение значимости примера и осторожный вывод')],
        [label('Quality criteria', 'Критерии качества'), "; ".join(criteria)],
        [label('Potential model errors', 'Возможные ошибки модели'), "; ".join(topic['undesirable_errors'] if language == 'en' else ERRORS_RU)],
        [label('How to check the result', 'Как проверять результат'), label('Count words, score the criteria, and verify factual claims and citations manually', 'Подсчитать слова, оценить критерии, вручную проверить факты и источники')],
        [label('When not to use the prompt', 'Когда промпт использовать нельзя'), label('The task requires current facts or real citations that cannot be independently verified', 'Нужны актуальные факты или реальные источники без возможности независимой проверки')],
    ]) + f"\n\n**{label('Final prompt', 'Итоговый промпт')}:**\n\n{fenced(prompts['v3'])}\n")

    final_result = primary_v3 or {}
    add(f"## {label('16. Task 13: Final text and edit disclosure', '16. Задание 13: итоговый текст и сведения о правках')}\n\n{label('The text below is Model A’s raw V3 answer, reproduced without editorial changes. Its measured length is 214 words. Its position is that AI should be used thoughtfully and important claims should be checked; it has an introduction, a main point, two explained examples, and a conclusion.', 'Ниже приведён исходный ответ модели А на V3 без редакторских изменений. Измеренный объём — 214 слов. Его позиция: ИИ следует использовать осознанно, а важные утверждения проверять; в тексте есть вступление, основной тезис, два пояснённых примера и заключение.')}\n\n{fenced(final_result.get('answer', ''))}\n\n" + md_table([label('Manual change', 'Ручное изменение'), label('Reason', 'Причина')], [[label('None', 'Нет'), label('The report reproduces the stored model answer; translation is not presented as model output.', 'В отчёте приведён сохранённый ответ модели; перевод не выдаётся за ответ модели.')]]) + "\n")

    add(f"## {label('17. Task 14: Conclusions', '17. Задание 14: выводы')}\n\n" + "\n".join([
        f"1. {label('The simple prompt only names the topic; V3 specifies role, audience, structure, constraints, output format and examples.', 'Простой промпт называет только тему; V3 задаёт роль, аудиторию, структуру, ограничения, формат и примеры.')}",
        f"2. {label('The most useful elements in this run were the audience, explicit structure, word range, and prohibition on invented sources.', 'В этом запуске наиболее полезны описание аудитории, явная структура, диапазон объёма и запрет на вымышленные источники.')}",
        f"3. {label('The educational-writer role framed the voice, but its separate effect was not isolated.', 'Роль образовательного автора задала тон, но её отдельное влияние не измерялось.')}",
        f"4. {label('The audience instruction makes the intended reader explicit; it cannot guarantee perfect age-level fit.', 'Описание аудитории уточняет читателя, но не гарантирует идеальное соответствие возрасту.')}",
        f"5. {label('Model A’s V2 output met the word target while V1 did not; the B V2 request failed.', 'Ответ А на V2 попал в целевой объём, V1 — нет; запрос Б на V2 завершился ошибкой.')}",
        f"6. {label('Model A’s V3 answer also met the word target; Model B’s was shorter. One run is not enough for a general model ranking.', 'Ответ А на V3 также попал в целевой объём, ответ Б оказался короче. Одного запуска недостаточно для общего рейтинга моделей.')}",
        f"7. {label('A fabricated citation in the examples could distract or prime copying; no literal copying was found in V3.', 'Вымышленная ссылка в образцах может отвлекать или провоцировать копирование; дословного копирования в V3 не выявлено.')}",
        f"8. {label('Copying was checked by comparing distinctive example wording with the generated answers; this is a qualitative check.', 'Копирование проверялось сравнением характерных формулировок образцов с ответами; это качественная проверка.')}",
        f"9. {label('Claude Haiku performed better on the word-count target in this run; Llama’s V2 call failed and its V1/V3 answers were short.', 'В этом запуске Claude Haiku лучше выполнила требование объёма; запрос Llama на V2 завершился ошибкой, ответы V1/V3 были короткими.')}",
        f"10. {label('Good few-shot examples teach one transferable skill, stay short, avoid conflicting with the constraints, and are checked for copying.', 'Хорошие few-shot примеры показывают переносимый навык, остаются короткими, не конфликтуют с ограничениями и проверяются на копирование.')}",
    ]) + f"\n\n{label('Interpretation limit', 'Ограничение интерпретации')}: {label('These findings describe one small run at one endpoint and setting; they do not establish general model superiority or causal few-shot effects.', 'Эти результаты относятся к одному небольшому запуску с одним endpoint и настройками; они не доказывают общего превосходства модели или причинного эффекта few-shot примеров.')}\n")

    add(f"## {label('Appendix A: Run summary', 'Приложение А: сводка запуска')}\n\n" + md_table([label('Request', 'Запрос'), label('Model', 'Модель'), label('Status', 'Статус'), label('Words', 'Слова'), label('Latency s', 'Латентность с'), label('Finish', 'Завершение')], [
        [r['prompt_name'], r['model'], r['status'], r.get('word_count', 0), r['latency_sec'], r['finish_reason']]
        for r in rows
    ]) + "\n")
    add(f"\n{label('All full prompts and raw responses, including the failed request and reviewer response, are preserved in the run folder.', 'Полные промпты и исходные ответы, включая неудачный запрос и ответ рецензента, сохранены в папке запуска.')}\n")
    return "\n\n".join(sections).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--language", choices=("ru", "en"), default="ru")
    parser.add_argument("--student", default="")
    parser.add_argument("--group", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    output = Path(args.output) if args.output else ROOT / "reports/lab2" / ("LAB2_REPORT.md" if args.language == "ru" else "LAB2_REPORT_EN.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(run_dir, args.language, args.student, args.group), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
