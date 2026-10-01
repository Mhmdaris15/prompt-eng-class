# Защита лабораторной работы №1 / Lab 1 Defense Guide

## 1. Краткое выступление / Short presentation

### Русский

В работе я исследовал подключение к большим языковым моделям через
OpenAI-совместимый API Cloud.ru. Я выбрал две доступные модели:
`moonshotai/Kimi-K2.6` и `Qwen/Qwen3-Coder-Next`. Для корректного сравнения
использовал одинаковые исходный текст, температуру и типы заданий.

Я проверил базовое подключение, пять формулировок суммаризации, три типа
вопросов по тексту и три формата ответа: обычный текст, список и JSON. Кроме
самого ответа я записывал задержку, длину, количество чисел, годов, ссылок,
маркеров осторожности и уверенных формулировок. Отдельно я подготовил
проверку галлюцинаций: выбрал конкретные утверждения и сверил их с открытыми
источниками. Итоговая оценка выполнена по шкале от 1 до 5.

Главный вывод: качество ответа зависит не только от модели, но и от точности
инструкции. Ограничение контекста и требование признать отсутствие информации
снижают риск выдуманных фактов, однако не заменяют ручную проверку.

### English

In this work I studied how to connect to large language models through the
Cloud.ru OpenAI-compatible API. I selected two available models:
`moonshotai/Kimi-K2.6` and `Qwen/Qwen3-Coder-Next`. To make the comparison fair,
I used the same source text, temperature, and task categories for both models.

I tested connectivity, five summarization formulations, three types of
questions, and three output formats: plain text, a list, and JSON. In addition
to the generated answer, I recorded latency, response length, numbers, years,
links, caution markers, and confident-language markers. I also performed a
manual hallucination check by verifying concrete claims against public sources.
Finally, I scored the answers from 1 to 5.

The main conclusion is that output quality depends on both the model and the
precision of the prompt. Explicit context boundaries and an instruction to
admit missing information reduce hallucination risk, but they do not replace
human verification.

**Implementation note:** Cloud.ru reports Kimi's reasoning tokens inside the
completion budget. The runner therefore gives Kimi a 4096-token budget so that
its final answer is not truncated by internal reasoning.

## 2. Структура демонстрации / Demonstration order

1. Show `.env` contains `API_KEY` but do not reveal its value.
2. Show `lab1/runner.py` and explain the shared `call()` function.
3. Run `python -m lab1.runner`.
4. Open `results/lab1/manifest.json` and show selected models.
5. Open `lab1_results_with_metrics.csv`.
6. Compare one summarization variant across both models.
7. Compare the unavailable-context question.
8. Show JSON-format compliance.
9. Open `hallucination_verification.csv` and explain manual verification.
10. Open `quality_scores.csv` and explain the 1–5 rubric.

## 3. Вопросы преподавателя / Likely questions

### Why use the same prompt for both models?

**RU:** Чтобы сравнение было контролируемым: различие результата связывается с
моделью, а не с разными инструкциями.

**EN:** To control the experiment. Differences are more plausibly attributed to
the models rather than to different instructions.

### What is a hallucination?

**RU:** Это правдоподобно сформулированное, но неверное или неподтверждённое
утверждение, которое модель представляет как факт.

**EN:** A hallucination is a plausible-looking but false or unsupported claim
presented by the model as if it were a fact.

### Why is one unavailable-context question important?

**RU:** Она проверяет, умеет ли модель ограничиваться данным текстом и признавать
нехватку информации, вместо того чтобы уверенно придумать ответ.

**EN:** It tests whether the model respects the supplied context and admits
missing information instead of inventing a confident answer.

### Why record latency?

**RU:** Задержка важна для практического применения: более длинный ответ не
обязательно лучше, если он слишком медленный.

**EN:** Latency matters for practical use. A longer answer is not necessarily
better if it is too slow for the intended application.

### Why use JSON?

**RU:** JSON проверяет не только смысл, но и пригодность ответа для программной
обработки. Дополнительный текст вне JSON нарушает контракт формата.

**EN:** JSON tests machine-readable output. Extra prose outside the JSON object
breaks the format contract.

### Are automatic metrics enough?

**RU:** Нет. Длина и количество ссылок измеримы, но точность и полезность требуют
проверки человеком.

**EN:** No. Length and link counts are measurable, but accuracy and usefulness
still require human review.

### Is the faster model better?

**RU:** Не обязательно. Нужно рассматривать компромисс между задержкой, точностью,
полнотой и следованием инструкции для конкретной задачи.

**EN:** Not necessarily. The relevant trade-off is latency versus accuracy,
completeness, and instruction following for the specific task.

## 4. Финальная фраза / Closing statement

### Русский

Таким образом, лабораторная работа показала, что промпт-инжиниринг — это
управление условиями эксперимента: контекстом, формулировкой, форматом и
критериями проверки. Надёжность LLM нужно подтверждать наблюдаемыми результатами
и внешними источниками, а не только уверенным стилем ответа.

### English

Therefore, the laboratory work shows that prompt engineering is the controlled
design of context, wording, output format, and evaluation criteria. LLM
reliability must be supported by observed results and external verification,
not by a confident writing style alone.
