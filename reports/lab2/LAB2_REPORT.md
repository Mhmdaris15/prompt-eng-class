# Отчёт по лабораторной работе №2 по промпт-инжинирингу и few-shot prompting


## 1. Титульный лист

**ITMO University / Университет ИТМО**  
**Дисциплина:** Промпт-инжиниринг  
**Студент:** ____________________  
**Группа:** ____________________  
**Время эксперимента:** 2026-10-28T20:32:24.058164  
**Папка запуска:** `results\lab2_claude_haiku_llama_20261028_202806`  
**Модели:** A `anthropic/claude-haiku-4.5`; B `meta-llama/llama-3.3-70b-instruct`.


## 2. Цель и метод

Цель — спроектировать и сравнить простой промпт, структурированный промпт V1, one-shot вариант V2 и few-shot вариант V3, а затем проверить слабые места и получить независимую рецензию. Модель А создала базовый и итоговый текст; одинаковые строки промптов V1, V2 и V3 были отправлены обеим моделям. Модель Б отдельно рецензировала ответ V3 модели А. Промпты и ответы моделей сохранены без изменений на исходном английском языке.

Объём считался по токенам, разделённым пробелами, в сохранённом ответе. Автоматические счётчики ссылок, годов, чисел и маркеров осторожности/уверенности — только индикаторы и не доказывают фактическую точность. Для каждой ячейки был запланирован один запрос; для итогового ответа допускается не более двух попыток. В этом запуске хватило одной попытки.


## 3. Модели и условия запуска

| Параметр | Значение |
| --- | --- |
| Модель A | anthropic/claude-haiku-4.5 |
| Модель Б | meta-llama/llama-3.3-70b-instruct |
| Профиль API | cloudru |
| Endpoint | https://foundation-models.api.cloud.ru/v1 |
| Температура | 0.3 |
| Максимум выходных токенов | 4096 |
| Таймаут | 180.0 s |
| Запросы | 12 успешных, 1 ошибка, 0 усечённых |

SHA-256 runner-кода на момент запуска: `17f102573eea7ef847479a4431098393441ad46e8130d9f952c4a3070c119e80`. После запуска парсер отчёта был улучшен: теперь он извлекает JSON из ответа рецензента в блоке кода; исходный ответ модели в `lab2_results.json` не менялся. Хеш исходного текста в манифесте: `13ef01169bfade1627006d0819cfeb2c659c4e2ad65a5e61c65a3b96877836e3`. Ключ API в результатах не сохранялся.


## 4. Задание 1: выбор темы и задачи

| Вопрос | Ответ |
| --- | --- |
| Какая тема выбрана? | Почему ответы ИИ нужно проверять |
| Что должна сделать модель? | Написать мини-эссе для учеников 9–10 классов о том, почему ответы ИИ нужно проверять, привести два конкретных примера и сделать осторожный вывод. |
| Для кого предназначен текст? | Ученики 9–10 классов (14–16 лет) |
| Где такой текст мог бы использоваться? | На уроке информатики или цифровой грамотности; как учебный материал о проверке информации, созданной ИИ. |
| Каким должен быть хороший результат? | Мини-эссе на 180–220 слов с понятной структурой, двумя пояснёнными примерами, фактической аккуратностью и осторожным выводом. |
| Какие ошибки модели здесь особенно нежелательны? | Вымышленные источники или факты; необоснованные даты и числа; чрезмерная уверенность; отсутствие нужной структуры; неподходящий аудитории язык. |


## 5. Задание 2: критерии качества и шкала

В первой таблице приведены шесть основных критериев и формулировок из задания. Оценки ответа модели А на финальный промпт V3 являются черновой самооценкой и требуют подтверждения студентом. Во второй таблице отдельно указаны дополнительные операционные проверки эксперимента.

| Критерий | Как понять, что он выполнен | Оценка 0–2 |
| --- | --- | --- |
| Соответствие теме | Ответ не уходит в сторону от выбранной темы | 2 |
| Понятность аудитории | Текст понятен выбранной аудитории | 2 |
| Структура | Есть начало, развитие мысли и завершение | 2 |
| Конкретность | Есть примеры, а не только общие рассуждения | 1 |
| Фактическая аккуратность | Нет вымышленных фактов, дат, цитат и источников | 2 |
| Стиль | Тон соответствует задаче | 2 |

Шкала: 0 — критерий не выполнен; 1 — выполнен частично; 2 — выполнен хорошо. Черновые оценки нужно проверить и подтвердить.

Дополнительная операционная рубрика

| Критерий | Как проверялся | Черновая самооценка 0–2 |
| --- | --- | --- |
| Соответствие теме | Прямой ответ на задачу | 2 |
| Понятность для аудитории | Уровень языка соответствует аудитории | 2 |
| Логичная структура | Вступление, тезис, примеры, пояснения и вывод | 2 |
| Не менее двух конкретных примеров | Два различимых примера | 1 |
| Фактическая аккуратность | Нет неподтверждённых конкретных фактов и ссылок | 2 |
| Подходящий и осторожный стиль | Спокойный тон и осторожные формулировки | 2 |
| Объём 180–220 слов | Подсчёт слов по пробелам: 180–220 | 2 |
| Вывод без новых аргументов | В выводе нет нового аргумента | 2 |
| Пригодность после небольшой правки | Достаточно небольшой правки | 1 |

Шкала: 0 — не выполнен; 1 — выполнен частично; 2 — выполнен. Обоснование черновых баллов дано в разделе самооценки.


## 6. Задание 3: простой промпт и первый результат

**Промпт:**

```text
Write a short essay about why ai answers need verification for students.
```

**Ответ модели А:** (269 слов)

```text
# Why AI Answers Need Verification for Students

As artificial intelligence becomes increasingly integrated into education, students must understand a critical truth: AI-generated answers require verification. While AI tools offer convenience and speed, they are not infallible sources of truth.

## The Problem of Plausible Errors

AI systems, particularly language models, can generate responses that sound authoritative and well-structured while containing factual errors, outdated information, or logical flaws. These mistakes are often subtle enough to escape casual review, making them particularly dangerous in an educational context. A student who accepts an AI answer at face value may internalize incorrect information and build future learning on a faulty foundation.

## The Learning Imperative

Education is fundamentally about developing critical thinking skills. When students verify AI answers against textbooks, academic sources, and expert knowledge, they engage in active learning rather than passive consumption. This verification process—comparing sources, identifying contradictions, and evaluating evidence—is where genuine understanding develops.

## Accountability and Academic Integrity

Relying on unverified AI answers can blur the line between using technology as a tool and academic dishonesty. Students who verify their sources take responsibility for their work and maintain academic integrity. They also develop the habit of proper citation and source evaluation, skills essential for higher education and professional success.

## Building Digital Literacy

In an age of misinformation, learning to question and verify information from any source—human or artificial—is crucial. Students who develop verification habits now will be better equipped to navigate an increasingly complex information landscape throughout their lives.

AI is a powerful educational tool, but verification transforms it from a shortcut into a genuine learning aid.
```

Черновая оценка: ответ содержит 269 слов и превышает целевой объём 180–220; промпт не задаёт аудиторию, структуру, примеры и осторожный стиль. Недостатки: (1) объём выше цели; (2) нет требования о двух пояснённых примерах; (3) не заданы возраст и формат. Это мотивирует V1.


## 7. Задание 4: проектирование структурированного промпта

| Часть промпта | Что вы добавили | Зачем это нужно |
| --- | --- | --- |
| Роль | Автор учебных текстов о цифровой грамотности подростков | Задаёт область и регистр |
| Задача | Объяснить, почему ответы ИИ нужно проверять | Фиксирует основной вопрос |
| Аудитория | 9–10 класс, 14–16 лет | Задаёт словарь и уровень пояснений |
| Контекст | Цифровая грамотность подростков заложена в роли, но школьный контекст явно не назван | В следующей версии можно задать явнее |
| Содержание и структура | Короткое вступление, тезис, два пояснённых сбоя, осторожный вывод | Делает структуру проверяемой |
| Ограничения | 180–220 слов; без вымышленных фактов, дат, источников и статистики; без категоричности | Ограничивает объём и недоказуемую точность |
| Формат | Обычные текстовые абзацы | Упрощает дальнейшее использование |
| Критерии | Встроены в требования, а не даны отдельным списком | Помогают оценке; можно добавить явный список |


## 8. Задание 5: промпт V1 и сравнение моделей

**V1 полностью:**

```text
You are an educational content writer specializing in digital literacy for teenagers.

Write a mini-essay for 9-10th grade students (ages 14-16) explaining why AI answers need verification.

The essay must include:
1. A brief introduction (2-3 sentences)
2. The main point: AI generates probable text, not verified facts
3. Two concrete examples of AI failures (hallucination, outdated knowledge, or confident errors)
4. An explanation for each example
5. A cautious conclusion that doesn't overstate the case

Constraints:
- Tone: calm, educational, not condescending
- Length: 180-220 words
- No fabricated facts, quotes, sources, dates, or citations
- No made-up statistics or precise numbers
- Do not use overly categorical language
- Write in plain language appropriate for the audience

Format: Plain text paragraphs.
```



**anthropic/claude-haiku-4.5 — ok, 95 слов, 4.346 s:**

```text
# Why You Should Verify AI Answers

You've probably used AI chatbots to help with homework or answer quick questions. They're fast and often helpful, but here's something important to understand: AI doesn't actually "know" things the way you do. Instead, it predicts what words should come next based on patterns in its training data.

This matters because AI can sound confident while being completely wrong. When an AI generates text, it's essentially making educated guesses about what's probable, not checking facts against reliable sources. This can lead to problems.

One common issue is "Overloaded
```



**meta-llama/llama-3.3-70b-instruct — ok, 166 слов, 30.385 s:**

```text
As we increasingly rely on artificial intelligence (AI) for information, it's essential to understand its limitations. AI can generate human-like text, but this doesn't mean the information is accurate or up-to-date. It's crucial to verify AI answers to ensure we're getting reliable information.

AI generates probable text based on patterns and associations, not verified facts. This can lead to errors, such as hallucination, where AI provides information that isn't based on any actual data. For example, AI might describe a fictional event as if it were real. Another issue is outdated knowledge, where AI provides information that was once true but is no longer accurate.

For instance, AI might confidently state that a certain company is still in business, even if it has gone bankrupt. In both cases, AI's errors can be misleading and potentially harmful. It's essential to fact-check AI answers to separate fact from fiction. By being cautious and verifying information, we can use AI as a helpful tool while avoiding its potential pitfalls.
```



**Сравнение простого промпта и V1 по шаблону задания:**

| Критерий | Простой промпт | Промпт V1 | Комментарий |
| --- | --- | --- | --- |
| Соответствие теме | Рассматривает проверку ответов ИИ. | Та же тема задана явно. | Оба ответа остаются в теме. |
| Понятность аудитории | Упомянуты ученики, возраст и класс не заданы. | Указаны 9–10 классы (14–16 лет). | В V1 аудитория задана точнее. |
| Структура | Есть подзаголовки и заключительный абзац, но структура не была задана. | Задана структура из пяти частей, но ответ обрывается на полуслове. | Промпт V1 точнее, однако ответ неполный. |
| Конкретность | Сбои обсуждаются в общем виде; два примера не требуются. | Запрошены два примера, но сохранённый ответ обрывается до их приведения. | В этом ответе требование V1 не выполнено. |
| Стиль | Формальный учебный тон; аудитория не уточнена. | Запрошен спокойный и простой язык для подростков. | В V1 стиль задан точнее. |
| Фактическая аккуратность | Источники не указаны; факты независимо не проверялись. | Вымысел запрещён; в неполном ответе нет ссылок. | Ограничения промпта не заменяют проверку фактов. |


Ответ Claude Haiku на V1 заметно короче требуемого — 95 слов — и заканчивается на полуслове фразой “One common issue is Overloaded”, хотя finish_reason равен stop. Ответ Llama тоже короче — 166 слов. Ни один ответ не попал в диапазон; указание объёма не гарантировало его соблюдение.


## 9. Задание 6: неудачный и удачный few-shot пример

| Тип примера | Текст примера | Почему он удачный или неудачный |
| --- | --- | --- |
| Неудачный | AI is useful for everyone because it makes life easier and helps with many tasks. | Слишком общее утверждение: нет конкретной ситуации, условного контекста; фраза похожа на лозунг. |
| Удачный | AI can help a student understand a difficult concept if used as an explanation assistant rather than a way to just get the answer. For example, asking 'Can you explain how photosynthesis works step by step?' is more useful than asking 'What is the answer to question 5?' | Показана ситуация ученика, есть условие («если использовать для объяснения»), различие между полезным и неудачным применением и осторожный тон. |

Удачный пример касается применения ИИ для изучения сложной темы: он связан с образованием, но не повторяет точную задачу эссе о проверке ответов.


## 10. Задание 7: one-shot промпт V2

**V2 полностью:**

```text
You are an educational content writer specializing in digital literacy for teenagers.

Write a mini-essay for 9-10th grade students (ages 14-16) explaining why AI answers need verification.

The essay must include:
1. A brief introduction (2-3 sentences)
2. The main point: AI generates probable text, not verified facts
3. Two concrete examples of AI failures (hallucination, outdated knowledge, or confident errors)
4. An explanation for each example
5. A cautious conclusion that doesn't overstate the case

Constraints:
- Tone: calm, educational, not condescending
- Length: 180-220 words
- No fabricated facts, quotes, sources, dates, or citations
- No made-up statistics or precise numbers
- Do not use overly categorical language
- Write in plain language appropriate for the audience

Aim for this level of specificity:

Weak formulation:
AI helps people learn.

Better formulation:
AI can help a student understand a difficult concept if used as an explanation assistant rather than a way to just get the answer. For example, asking 'Can you explain how photosynthesis works step by step?' is more useful than asking 'What is the answer to question 5?'

Format: Plain text paragraphs.
```



**anthropic/claude-haiku-4.5 — ok, 203 слов, 5.304 s:**

```text
# Why You Should Check AI Answers

You've probably used AI to help with homework or answer questions. It's fast and often sounds confident. But here's something important: AI doesn't actually know things the way you do. It generates text based on patterns it learned, which means it can sound right while being wrong.

**AI generates probable text, not verified facts.** Think of it like this: AI predicts what words should come next based on what it's seen before. It's really good at this, but prediction isn't the same as knowing. Sometimes AI confidently gives you information that sounds completely real but isn't.

For example, AI might invent details about historical events or create fake names of scientists who don't exist. It does this without hesitation because it's just following patterns, not checking facts. Another common problem is outdated information. If AI was trained on older data, it might give you information that's no longer current, like outdated scientific understanding or old statistics.

**The takeaway:** AI is a useful tool, but treat it like a starting point, not a final answer. Cross-check important information with reliable sources like textbooks, educational websites, or your teacher. Using AI thoughtfully—combined with verification—makes you a smarter learner.
```



**meta-llama/llama-3.3-70b-instruct — error, 0 слов, 77.191 s:**

Запрос завершился ошибкой, ответ не получен.



Ответ модели А на V2 содержит 203 слова и попадает в диапазон; V1 у неё был 95 слов. В тексте появились более конкретные формулировки, включая гипотетические примеры с вымышленными историческими деталями и именами учёных. Запрос модели Б на V2 вернул HTTP 502 («Request failed») через 77,191 секунды; сравнить ответ Б в этой ячейке нельзя. One-shot пример мог помочь модели А попасть в объём, но один запуск не доказывает причинность.


**Сравнение V1 и V2 по таблице задания:**

| Вопрос | Ответ |
| --- | --- |
| Что изменилось после добавления примера? | V2 содержит один пример о просьбе к ИИ объяснить сложную тему по шагам. |
| Стал ли ответ конкретнее? | Частично: вместо общего обсуждения в V1 модель А назвала в V2 два типа сбоев; примеры остаются гипотетическими. |
| Стал ли стиль ближе к нужному? | Да: ответ V2 написан простым языком для ученика и содержит 203 слова, то есть попадает в целевой диапазон. |
| Появилось ли копирование примера? | Дословного копирования не выявлено; модель использовала собственные примеры. |
| Стоит ли оставлять пример в промпте? | Сохранить обучающий приём, но использовать нейтральный гипотетический пример без вымышленных имён и ссылок. |


## 11. Задание 8: few-shot промпт V3 и сравнение

**V3 полностью:**

```text
You are an educational content writer specializing in digital literacy for teenagers.

Write a mini-essay for 9-10th grade students (ages 14-16) explaining why AI answers need verification.

The essay must include:
1. A brief introduction (2-3 sentences)
2. The main point: AI generates probable text, not verified facts
3. Two concrete examples of AI failures (hallucination, outdated knowledge, or confident errors)
4. An explanation for each example
5. A cautious conclusion that doesn't overstate the case

Constraints:
- Tone: calm, educational, not condescending
- Length: 180-220 words
- No fabricated facts, quotes, sources, dates, or citations
- No made-up statistics or precise numbers
- Do not use overly categorical language
- Write in plain language appropriate for the audience

Examples of desired style:

Example 1 - Concrete argument:
Weak: AI can make mistakes.
Better: An AI might invent a fake citation like "Smith et al. 2023, 'Quantum Computing Breakthrough'" — a paper that doesn't exist but looks real.

Example 2 - Explaining an example:
Weak: This is bad because it's wrong.
Better: This matters because a student might use that fake citation in a report, and the teacher would find no such paper.

Example 3 - Cautious conclusion:
Weak: So never trust AI.
Better: So it's wise to check important claims from AI against reliable sources, especially for facts, dates, and references.

Format: Plain text paragraphs.
```



**anthropic/claude-haiku-4.5 — ok, 214 слов, 4.651 s; caution markers 1, confident markers 1:**

```text
# Why You Should Verify AI Answers

You've probably used AI to help with homework or answer questions. It's fast and often helpful. But here's something important: AI doesn't actually "know" facts the way you do. Instead, it predicts the next word based on patterns it learned during training, which means it can sound confident while being completely wrong.

AI sometimes invents information that sounds plausible but doesn't exist. For example, an AI might describe a historical event with specific details—names, dates, locations—that seem real but are actually made up. A student might copy these details into an essay, only to have a teacher point out that the event never happened. The AI wasn't trying to lie; it was just following patterns without checking reality.

Another common problem is outdated knowledge. If an AI was trained on information from several years ago, it might give you answers about current events, recent discoveries, or new technology that are no longer accurate. You could end up with information that was true once but isn't anymore.

The solution isn't to avoid AI—it's to be thoughtful. For important facts, dates, or claims, cross-check what AI tells you with reliable sources like your library database, textbooks, or established websites. This habit protects your work and builds stronger research skills.
```



**meta-llama/llama-3.3-70b-instruct — ok, 163 слов, 12.511 s; caution markers 0, confident markers 0:**

```text
As we increasingly rely on artificial intelligence (AI) for information and answers, it's essential to understand the importance of verifying AI-generated content. AI systems can process vast amounts of data and generate text quickly, but this doesn't mean the information is always accurate. In fact, AI often produces probable text based on patterns and associations, rather than verified facts.

For instance, an AI might invent a fake citation or claim that a certain event occurred on a specific date, even if it didn't. Another example is when AI provides outdated knowledge, such as recommending a treatment for a medical condition that has since been discredited. This matters because students might use such information in their research or reports, only to find that it's incorrect or outdated.

So it's wise to check important claims from AI against reliable sources, especially for facts, dates, and references. By doing so, we can ensure the accuracy and credibility of the information we use and avoid spreading misinformation.
```



**Сравнение версий по критериям задания (модель A; черновые оценки 0–2):**

| Критерий | V1 без примеров | V2 с одним примером | V3 с несколькими примерами | Комментарий |
| --- | --- | --- | --- | --- |
| Соответствие теме | 2 | 2 | 2 | Все три посвящены проверке ответов ИИ. |
| Понятность аудитории | 2 | 2 | 2 | Во всех названы 9–10 классы; V1 обрывается. |
| Структура | 1 | 2 | 2 | V1 обрывается на полуслове; V2 и V3 содержат запрошенные части. |
| Конкретность | 1 | 1 | 1 | В V2 и V3 названы типы сбоев, но нет подробного проверяемого случая. |
| Стиль | 2 | 2 | 2 | Тон учебный во всех версиях; структурированные промпты точнее задают аудиторию. |
| Осторожность формулировок | 1 | 2 | 2 | В V2 и V3 прямо рекомендуется проверять важные утверждения. |
| Отсутствие копирования примеров | Нет примеров | 2 | 2 | Дословного копирования нет; вымышленная цитата всё же может провоцировать подражание. |

Это черновые оценки человека, а не оценки API. Ответ модели Б на V2 отсутствует из-за ошибки HTTP 502.


Ответ модели А на V3 содержит 214 слов и попадает в диапазон. Он поясняет два типа сбоев (правдоподобные вымышленные детали и устаревшие сведения), завершает осторожным выводом и не повторяет конкретную цитату из few-shot блока. Ответ модели Б на V3 содержит 163 слова — меньше нормы, хотя в нём есть примеры вымышленной ссылки и устаревших знаний. В этом запуске V3 — лучший ответ модели А по требованиям объёма и структуры; это не доказывает универсальное превосходство V3 или модели А. В промпте три коротких обучающих примера, но намеренно вымышленная ссылка может провоцировать подражание; в дальнейшем её стоит убрать или явно обозначить как непригодный для повторения шаблон.


## 12. Задание 9: анализ влияния few-shot примеров

| Версия / модель | Слова | Латентность (с) | Осторожность / уверенность | Результат |
| --- | --- | --- | --- | --- |
| V1 | anthropic/claude-haiku-4.5 | 95 | 4.346 | 1 / 0 | ok |
| V1 | meta-llama/llama-3.3-70b-instruct | 166 | 30.385 | 0 / 0 | ok |
| V2 | anthropic/claude-haiku-4.5 | 203 | 5.304 | 1 / 0 | ok |
| V2 | meta-llama/llama-3.3-70b-instruct | 0 | 77.191 | 0 / 0 | error |
| V3 | anthropic/claude-haiku-4.5 | 214 | 4.651 | 1 / 1 | ok |
| V3 | meta-llama/llama-3.3-70b-instruct | 163 | 12.511 | 0 / 0 | ok |


1. В V2 добавлен пример об использовании ИИ для изучения сложной темы; V3 содержит примеры конкретики, пояснения значимости и осторожного вывода.
2. Примеры показывают отдельные навыки письма и не повторяют тему итогового эссе дословно.
3. Они должны были обучить конкретности, пояснению и осторожному заключению.
4. Ответ А вырос с 95 слов в V1 до 203 в V2; запрос модели Б на V2 завершился ошибкой.
5. Ответ А на V3 достиг 214 слов и пояснил два типа риска; ответ Б содержит 163 слова.
6. Да. Вымышленная цитата в V3 создаёт риск подражания; ни один из ответов не скопировал её название дословно.
7. Сопоставляются объём, структура, конкретность, совпадение с примерами и ответы обеих моделей.
8. Вероятно, полезнее пример, который связывает пример с его значением; это аналитическая оценка, а не измеренная причинность.
9. Цитату можно убрать: она конфликтует с запретом на вымышленные источники и может провоцировать такие ссылки.
10. Использовать нейтральные явно гипотетические примеры и добавить проверочный список из девяти критериев.



Таблица анализа примеров из задания

| Пример | Что он должен был показать | Помог / не помог | Почему |
| --- | --- | --- | --- |
| Пример 1: конкретный аргумент | Заменить общее утверждение конкретной иллюстрацией. | Помог частично | В эссе V3 описаны вымышленные детали события, но конкретный проверяемый случай не приведён; пример ложной ссылки может провоцировать подражание. |
| Пример 2: пояснить значимость | Связать пример с его значением для ученика. | Помог | Модель А поясняет, что ученик может перенести ложные детали в эссе и получить замечание учителя. |
| Пример 3: осторожный вывод | Избежать категоричного вывода и предложить разумную проверку. | Помог | Ответ V3 рекомендует сверять важные утверждения с надёжными источниками, а не полностью отказываться от ИИ. |


## 13. Задание 10: проверка слабых мест

Пять граничных проверок выполнены моделью А. Промпты и ответы сохранены в JSON запуска. В запросе о смене аудитории был передан предыдущий ответ V3 модели А, поэтому контекст не потерян.



| Проверка | Что вы изменили | Что сделала модель | Какая проблема появилась | Как можно улучшить промпт |
| --- | --- | --- | --- | --- |
| too_general_topic | Too general topic - model may give generic response | ok: Ответ превращается в общий обзор применений ИИ вместо мини-эссе о проверке ответов. | Он следует намеренно широкому запросу, но теряет узкую задачу лабораторной: не названы аудитория и нужный жанр. | Указать аудиторию, жанр, главный вопрос и два обязательных примера. |
| hallucination_risk | Risk of fabricated facts - ask for specific citations | ok: Ответ содержит три ссылки. В двух неверно указаны авторы/год: DOI 10.1145/3571730 относится к Ji et al. (2023), а не Rawte et al.; arXiv:2005.00661 — к Maynez et al. (2020), а не Zhang et al. (2023). Третья ссылка Ji et al. повторяет первый DOI. | Запрос на источники привёл к правдоподобным, но частично неверным ссылкам. Записи сверены с [записью ACM DOI](https://doi.org/10.1145/3571730) и [официальной записью arXiv](https://arxiv.org/abs/2005.00661). | Проверять название, авторов, год и DOI по записи издателя или репозитория; корректный формат DOI не означает, что ссылка подтверждена. |
| audience_change | Change audience - adapt for parents instead of students | ok: Модель переписала эссе для родителей, используя предыдущий ответ как контекст. | Контекст передан явно. Далее нужно проверить, действительно ли изменились тон и примеры для родителей. | Уточнить потребности родителей и попросить один пример для этой аудитории. |
| conflicting_requirements | Conflicting requirements - detailed but very short | ok: Модель должна была совместить подробное объяснение с ограничением в два предложения. | Ответ получился кратким; ограничение длины неизбежно уменьшает подробность. | Поставить лимит предложений выше и попросить один краткий пример либо убрать противоречивое требование подробности. |
| strict_json_format | Strict JSON format requirement | ok: Парсер подтвердил корректный JSON и пять обязательных ключей. | Корректный JSON не подтверждает фактическую точность. | Проверить JSON парсером, затем отдельно проверить утверждения. |


Ручная проверка ссылок: в ответе на запрос о галлюцинациях обнаружены две ошибки в авторах/годе; одна ссылка корректно ведёт к работе Ji et al. (2023), другая — к Maynez et al. (2020). Записи приведены в ссылках таблицы граничных случаев.

Результат проверки JSON: корректный JSON со всеми пятью обязательными ключами. Перед проверкой парсер удаляет оболочку блока кода. Ошибка запроса модели Б на V2 сохранена и исключена из качественного сравнения.


## 14. Задание 11: независимая рецензия модели Б

Модель Б получила исходную задачу, аудиторию и контекст, все девять критериев, полный промпт V3 и итоговый ответ модели А в отдельном запросе. Ответ содержал JSON в блоке кода и дополнительный текст. Парсер отчёта извлёк первый корректный JSON-объект; исходный ответ рецензента сохранён. Рецензент поставил 2/2 по всем критериям, не указал галлюцинаций и отметил, что в выводе можно подробнее объяснить перекрёстную проверку. Рецензия носит рекомендательный характер и не является независимой проверкой фактов.




**Таблица оценки второй моделью по шаблону задания:**

| Критерий | Оценка второй модели 0–2 | Комментарий второй модели | Согласен(на) / не согласен(на) | Мой комментарий |
| --- | --- | --- | --- | --- |
| Соответствие задаче | 2 | Ответ напрямую раскрывает тему необходимости проверки ответов ИИ. | Черновик: скорее согласен(на) | Текст соответствует теме; подтвердить студенту. |
| Понятность аудитории | 2 | Текст понятен ученикам 9–10 классов. | Черновик: согласен(на) | Язык доступен аудитории; подтвердить студенту. |
| Структура | 2 | Есть логичная структура: вступление, тезис, примеры, пояснения и вывод. | Черновик: согласен(на) | В ответе есть вступление, примеры и вывод. |
| Конкретность | 2 | Приведены два примера сбоев ИИ: вымышленные сведения и устаревшие данные. | Черновик: скорее не согласен(на) | Оценка 2/2 кажется завышенной: приведены типы сбоев, но примеры остаются общими. |
| Работа с few-shot примерами | — | Отдельная числовая оценка не дана. | Черновик: данных недостаточно | Рецензент вернул отдельное поле о копировании, но не оценку полезности примеров. |
| Отсутствие копирования примеров | — | Копирование few-shot: none | Черновик: скорее согласен(на) | Дословного копирования не выявлено, но вымышленная цитата может провоцировать подражание. |
| Фактическая аккуратность | 2 | В ответе нет вымышленных фактов, цитат, источников или дат. | Черновик: скорее согласен(на) | В итоговом эссе нет ссылок и дат; это не подтверждает все общие утверждения. |
| Стиль | 2 | Тон на всём протяжении спокойный, учебный и осторожный. | Черновик: согласен(на) | Тон спокойный и подходит указанной аудитории. |
| Итоговая пригодность текста | 2 | Текст можно использовать после небольшой правки; крупных изменений не требуется. | Черновик: скорее согласен(на) | Объём соблюдён, но нужна проверка фактов и соответствия аудитории человеком. |

Оценки и согласие выше приведены как черновое предложение для проверки студентом. Тире означает, что модель не поставила числовую оценку по этому критерию; оценка не додумывалась.


**Дополнительная таблица оценок из сохранённой рецензии:**

| Критерий | Модель Б | Комментарий рецензента | Черновая самооценка | Согласие |
| --- | --- | --- | --- | --- |
| Соответствие теме | 2 | Ответ напрямую раскрывает тему необходимости проверки ответов ИИ. | 2 | Подтвердить студенту |
| Понятность для аудитории | 2 | Текст понятен ученикам 9–10 классов. | 2 | Подтвердить студенту |
| Логичная структура | 2 | Есть логичная структура: вступление, тезис, примеры, пояснения и вывод. | 2 | Подтвердить студенту |
| Не менее двух конкретных примеров | 2 | Приведены два примера сбоев ИИ: вымышленные сведения и устаревшие данные. | 1 | Подтвердить студенту |
| Фактическая аккуратность | 2 | В ответе нет вымышленных фактов, цитат, источников или дат. | 2 | Подтвердить студенту |
| Подходящий и осторожный стиль | 2 | Тон на всём протяжении спокойный, учебный и осторожный. | 2 | Подтвердить студенту |
| Объём 180–220 слов | 2 | Ответ соответствует диапазону 180–220 слов. | 2 | Подтвердить студенту |
| Вывод без новых аргументов | 2 | Вывод не вводит новые аргументы и сохраняет осторожность. | 2 | Подтвердить студенту |
| Пригодность после небольшой правки | 2 | Текст можно использовать после небольшой правки; крупных изменений не требуется. | 1 | Подтвердить студенту |


**Черновик рефлексии для подтверждения студентом:** Я согласен(на), что текст понятен и достаточно осторожен, а в заключении можно подробнее описать перекрёстную проверку утверждений. Я бы не принимал(а) без оговорок одинаковую оценку 2/2: примеры конкретны по типу, но недостаточно детализированы, а фактическую точность и соответствие аудитории всё равно должен проверить человек. Это предложенный текст, а не зафиксированное личное мнение студента.


## 15. Задание 12: финальная Prompt Card

| Поле | Содержание |
| --- | --- |
| Название промпта | Учебное эссе о проверке ответов ИИ |
| Для какой задачи используется | Подготовить мини-эссе о том, почему ответы ИИ нужно проверять, с двумя примерами и осторожным выводом. |
| Целевая аудитория | Ученики 9–10 классов (14–16 лет) |
| Рекомендуемая модель | anthropic/claude-haiku-4.5 для этого запуска; это не универсальная рекомендация. |
| Входные данные | Задача и при необходимости проверяемые исходные материалы |
| Ожидаемый результат | Мини-эссе на 180–220 слов: вступление, тезис, два пояснённых примера, осторожный вывод |
| Роль модели | Автор образовательных текстов о цифровой грамотности подростков |
| Основные требования | Понятный язык, два примера сбоев, пояснение значимости, различение вероятного текста и проверенных фактов |
| Ограничения | Без вымышленных фактов, цитат, источников, дат, статистики и чрезмерной категоричности |
| Формат ответа | Обычные текстовые абзацы |
| Few-shot примеры | Один пример об обучении вне точной темы и три кратких стилистических/аргументативных образца |
| Что показывают few-shot примеры | Конкретику, пояснение значимости примера и осторожный вывод |
| Критерии качества | Соответствие теме; Понятность для аудитории; Логичная структура; Не менее двух конкретных примеров; Фактическая аккуратность; Подходящий и осторожный стиль; Объём 180–220 слов; Вывод без новых аргументов; Пригодность после небольшой правки |
| Возможные ошибки модели | Вымышленные ссылки или источники; Выдуманная статистика или точные числа без основания; Чрезмерно уверенные утверждения; Сложный или снисходительный язык; Отсутствие обязательных частей структуры; Существенное отклонение от целевого объёма |
| Как проверять результат | Подсчитать слова, оценить критерии, вручную проверить факты и источники |
| Когда промпт использовать нельзя | Нужны актуальные факты или реальные источники без возможности независимой проверки |

**Итоговый промпт:**

```text
You are an educational content writer specializing in digital literacy for teenagers.

Write a mini-essay for 9-10th grade students (ages 14-16) explaining why AI answers need verification.

The essay must include:
1. A brief introduction (2-3 sentences)
2. The main point: AI generates probable text, not verified facts
3. Two concrete examples of AI failures (hallucination, outdated knowledge, or confident errors)
4. An explanation for each example
5. A cautious conclusion that doesn't overstate the case

Constraints:
- Tone: calm, educational, not condescending
- Length: 180-220 words
- No fabricated facts, quotes, sources, dates, or citations
- No made-up statistics or precise numbers
- Do not use overly categorical language
- Write in plain language appropriate for the audience

Examples of desired style:

Example 1 - Concrete argument:
Weak: AI can make mistakes.
Better: An AI might invent a fake citation like "Smith et al. 2023, 'Quantum Computing Breakthrough'" — a paper that doesn't exist but looks real.

Example 2 - Explaining an example:
Weak: This is bad because it's wrong.
Better: This matters because a student might use that fake citation in a report, and the teacher would find no such paper.

Example 3 - Cautious conclusion:
Weak: So never trust AI.
Better: So it's wise to check important claims from AI against reliable sources, especially for facts, dates, and references.

Format: Plain text paragraphs.
```


## 16. Задание 13: итоговый текст и сведения о правках

Ниже приведён исходный ответ модели А на V3 без редакторских изменений. Измеренный объём — 214 слов. Его позиция: ИИ следует использовать осознанно, а важные утверждения проверять; в тексте есть вступление, основной тезис, два пояснённых примера и заключение.

```text
# Why You Should Verify AI Answers

You've probably used AI to help with homework or answer questions. It's fast and often helpful. But here's something important: AI doesn't actually "know" facts the way you do. Instead, it predicts the next word based on patterns it learned during training, which means it can sound confident while being completely wrong.

AI sometimes invents information that sounds plausible but doesn't exist. For example, an AI might describe a historical event with specific details—names, dates, locations—that seem real but are actually made up. A student might copy these details into an essay, only to have a teacher point out that the event never happened. The AI wasn't trying to lie; it was just following patterns without checking reality.

Another common problem is outdated knowledge. If an AI was trained on information from several years ago, it might give you answers about current events, recent discoveries, or new technology that are no longer accurate. You could end up with information that was true once but isn't anymore.

The solution isn't to avoid AI—it's to be thoughtful. For important facts, dates, or claims, cross-check what AI tells you with reliable sources like your library database, textbooks, or established websites. This habit protects your work and builds stronger research skills.
```

| Ручное изменение | Причина |
| --- | --- |
| Нет | В отчёте приведён сохранённый ответ модели; перевод не выдаётся за ответ модели. |


## 17. Задание 14: выводы

1. Простой промпт называет только тему; V3 задаёт роль, аудиторию, структуру, ограничения, формат и примеры.
2. В этом запуске наиболее полезны описание аудитории, явная структура, диапазон объёма и запрет на вымышленные источники.
3. Роль образовательного автора задала тон, но её отдельное влияние не измерялось.
4. Описание аудитории уточняет читателя, но не гарантирует идеальное соответствие возрасту.
5. Ответ А на V2 попал в целевой объём, V1 — нет; запрос Б на V2 завершился ошибкой.
6. Ответ А на V3 также попал в целевой объём, ответ Б оказался короче. Одного запуска недостаточно для общего рейтинга моделей.
7. Вымышленная ссылка в образцах может отвлекать или провоцировать копирование; дословного копирования в V3 не выявлено.
8. Копирование проверялось сравнением характерных формулировок образцов с ответами; это качественная проверка.
9. В этом запуске Claude Haiku лучше выполнила требование объёма; запрос Llama на V2 завершился ошибкой, ответы V1/V3 были короткими.
10. Хорошие few-shot примеры показывают переносимый навык, остаются короткими, не конфликтуют с ограничениями и проверяются на копирование.

Ограничение интерпретации: Эти результаты относятся к одному небольшому запуску с одним endpoint и настройками; они не доказывают общего превосходства модели или причинного эффекта few-shot примеров.


## Приложение А: сводка запуска

| Запрос | Модель | Статус | Слова | Латентность с | Завершение |
| --- | --- | --- | --- | --- | --- |
| simple | anthropic/claude-haiku-4.5 | ok | 269 | 5.106 | stop |
| v1 | anthropic/claude-haiku-4.5 | ok | 95 | 4.346 | stop |
| v1 | meta-llama/llama-3.3-70b-instruct | ok | 166 | 30.385 | stop |
| v2 | anthropic/claude-haiku-4.5 | ok | 203 | 5.304 | stop |
| v2 | meta-llama/llama-3.3-70b-instruct | error | 0 | 77.191 |  |
| v3 | anthropic/claude-haiku-4.5 | ok | 214 | 4.651 | stop |
| v3 | meta-llama/llama-3.3-70b-instruct | ok | 163 | 12.511 | stop |
| edge_too_general_topic | anthropic/claude-haiku-4.5 | ok | 218 | 21.286 | stop |
| edge_hallucination_risk | anthropic/claude-haiku-4.5 | ok | 461 | 8.038 | stop |
| edge_audience_change | anthropic/claude-haiku-4.5 | ok | 284 | 3.319 | stop |
| edge_conflicting_requirements | anthropic/claude-haiku-4.5 | ok | 64 | 2.216 | stop |
| edge_strict_json_format | anthropic/claude-haiku-4.5 | ok | 285 | 5.252 | stop |
| evaluation | meta-llama/llama-3.3-70b-instruct | ok | 334 | 76.187 | stop |



Полные промпты и исходные ответы, включая неудачный запрос и ответ рецензента, сохранены в папке запуска.
