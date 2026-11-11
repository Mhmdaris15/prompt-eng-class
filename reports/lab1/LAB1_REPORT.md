# Отчёт по лабораторной работе №1

## 1. Титульный лист

**Университет ИТМО**  
**Дисциплина:** Промпт-инжиниринг  
**Тема:** Подключение к LLM через API Cloud.ru, базовые запросы и первичный поиск галлюцинаций  
**Студент:** ____________________  
**Группа:** ____________________  
**Дата эксперимента (UTC):** 2026-10-01  
**Идентификатор запуска:** `20261001T220850Z_4888b946`  
**Санкт-Петербург, 2026**

## 2. Цель работы

Освоить подключение к LLM через OpenAI-совместимый API Cloud.ru, сравнить две модели на одинаковых запросах, исследовать влияние формулировок и формата, проверить соблюдение ограниченного контекста и достоверность конкретных фактов.

## 3. Использованные модели и условия

Выбраны `moonshotai/Kimi-K2.6` и `Qwen/Qwen3-Coder-Next`: обе доступны через один API и позволяют сравнить две разные модели на одном техническом материале. Выбор основан на доступности и пригодности для текстовых запросов, а не на предположении о превосходстве одной модели.

Адрес подключения: `https://foundation-models.api.cloud.ru/v1`. Ключ поступает из `API_KEY` в окружении или `.env`; значение ключа в результаты не записывается. Получено **95 идентификаторов**; полный список сохранён в приложении А. Наличие идентификатора в списке не означает, что каждый из них проверен на генерацию текста.

| Параметр | Значение |
| --- | --- |
| Python | 3.13.1 |
| openai | 2.44.0 |
| python-dotenv | 1.2.1 |
| requests | 2.32.3 |
| Температура | 0.2 в основных заданиях, 0 в тесте подключения |
| Максимальный бюджет | 8192 токенов для обеих моделей во всех запросах |
| Таймаут SDK | 180.0 с; `max_retries=1` |
| Передача ответа | `stream=False` |
| Число повторов | Один ответ каждой модели на каждый промпт |
| Порядок | Запросы попарно; первая модель чередуется между промптами |
| Основных ответов | 26: 13 промптов × 2 модели |

Kimi дополнительно получает запрос `thinking: {type: disabled}`. Это пожелание API; наличие или отсутствие поля reasoning фиксируется отдельно. Одинаковый верхний предел токенов не гарантирует одинаковые токенизаторы, внутренние вычисления или стоимость. Поэтому сравнивается наблюдаемое поведение сервисов при указанных условиях.

Исходный текст, параметры, версии пакетов, расход токенов и SHA-256 кода сохранены вместе с результатами. Каждый новый запуск получает отдельную папку; существующую папку нельзя перезаписать. Результаты старого эксперимента сохранены отдельно и в расчёты этого отчёта не включены.

## 4. Исходный текст

Использован учебный текст **Retrieval-Augmented Generation in Production Systems**, подготовленный для эксперимента и сохранённый в `source_text.txt`. Объём — **648 слов по пробельному разбиению**, рассчитанный примерно на 1–2 страницы обычного учебного текста; фактическое число страниц зависит от шрифта и интервала.

Текст выбран потому, что содержит техническое объяснение, эксплуатационные ограничения и материал для прямых и смысловых вопросов. Автор и год появления RAG в нём не указаны. Это контролируемый учебный материал, не цитата из научной статьи; для внешних исторических фактов используются источники раздела 8. Промпты и ответы англоязычные, анализ — на русском.

Retrieval-augmented generation (RAG) combines a language model with an external collection of documents. Before answering, a retriever searches that collection for passages related to the user's question. The selected passages are inserted into the prompt as evidence. This reduces dependence on the model's parametric memory and makes an answer easier to inspect.

A typical RAG pipeline includes document loading, chunking, indexing, retrieval, and generation. Chunking divides long documents into smaller fragments, often with overlap. An index stores a representation of each fragment. A keyword index is transparent and easy to debug, while a vector index compares embeddings by a similarity measure such as cosine similarity. A retriever returns the top-k fragments, where k is a configurable number.

RAG does not guarantee truth. Retrieval may return irrelevant passages, the context may be incomplete, and the model may misinterpret the evidence. Applications should ask the model to separate evidence from assumptions, cite the supplied passages, and state when the context is insufficient. Evaluation should measure both answer quality and adherence to the retrieved context.

Production teams monitor latency, retrieval precision, token usage, and failure rates. Caching repeated queries can reduce latency. Access controls are needed when a corpus contains private information. Retrieved documents are untrusted data: prompt injection inside a document must not override the system policy.

Consider a support assistant for an internal software platform. The document collection contains installation instructions, release notes, and troubleshooting guides. A useful answer must refer to the version mentioned in the question. A passage describing an older release may be relevant to the topic but wrong for the requested version. Document metadata can record a title, version, owner, access policy, and update time. Keeping this metadata attached to each fragment helps the application filter results and present meaningful citations.

Chunk size is a design choice rather than a universal constant. Very small fragments can separate an instruction from the condition that makes it valid. Very large fragments can include unrelated material and consume more of the model's context window. Overlap can preserve continuity near boundaries, but it also duplicates text. Teams should evaluate chunking on representative questions and check whether the returned fragments contain enough evidence. Similarly, increasing k may improve coverage while increasing latency and introducing distracting passages. The best setting depends on the documents, questions, retrieval method, and available context budget.

Index maintenance is separate from language-model training. When a document is corrected, the application should update or remove the corresponding indexed fragments. Otherwise, retrieval may continue to surface obsolete information. A citation is useful only if it points to the passage that actually supports the answer. Merely attaching a document title or a plausible URL does not establish that the answer is correct. If two retrieved passages disagree, the system should expose the conflict instead of silently presenting one claim as certain. A human reviewer may need to resolve the disagreement.

Evaluation can use a small collection of questions paired with expected evidence and acceptable answers. Include straightforward questions, questions that require combining passages, and questions that cannot be answered from the corpus. Inspect retrieval and generation separately: a correct passage can be followed by an incorrect answer, and a fluent answer can conceal a retrieval failure. An answer should not receive a high faithfulness score merely because it repeats words from the context. Review whether its main claims follow from the supplied passages and whether important qualifications have been preserved.

Operational safeguards must surround the model. Authorization should be enforced by the application before private passages are exposed to a user. Prompts alone are not an access-control mechanism. Logs used for evaluation should avoid disclosing confidential documents or credentials. Cached answers must respect the user's access permissions and the freshness of the underlying documents. These constraints make RAG an application architecture involving data management, retrieval, generation, and evaluation rather than a guarantee of accurate answers from a language model.

## 5. Ход выполнения

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

| Модель | Ответ (repr) | Время, с | Завершение |
| --- | --- | --- | --- |
| Kimi | ' connection verified.' | 1.092 | stop |
| Qwen | 'connection verified.' | 0.601 | stop |

### 5.2. Первый одинаковый запрос

> Explain the concept of retrieval-augmented generation to a second-year software engineering student in 120 words or fewer. Include one practical example.

Обе модели выполнили лимит 120 слов: Kimi — 103, Qwen — 109. Kimi объяснила retrieval и привела пример компании. Обе фразы о снижении галлюцинаций не означают гарантию; примеры придуманы для объяснения и не являются подтверждёнными случаями.

### 5.3. Пять формулировок суммаризации

Каждая инструкция дополнялась `Use only the source below.` и полным текстом раздела 4. Все десять ответов приведены в приложении Б.

| Вариант | Инструкция | Kimi, слов | Qwen, слов | Сравнение |
| --- | --- | --- | --- | --- |
| summary | Summarize the source in no more than 80 words. | 80 | 104 | Kimi уложилась в 80 слов; Qwen сохранила содержание, но превысила лимит (104 слова). |
| main_points | Extract the five main points from the source. | 325 | 240 | Обе выдали ровно пять пунктов; Kimi подробнее, Qwen компактнее. |
| short_recap | Briefly retell the source for a busy engineer. | 338 | 208 | Оба пересказа учитывают аудиторию инженера; числового ограничения длины не было. |
| outline | Create a concise hierarchical outline of the source. | 547 | 470 | Обе иерархические структуры закончены; Kimi — 547 слов, Qwen — 470. |
| takeaways | List the most useful practical takeaways from the source. | 529 | 275 | Оба списка извлекают конкретные действия; Qwen короче: 275 против 529 слов. |

Для краткого резюме лучше всего сработал явный предел: Kimi уложилась в 80 слов, Qwen превысила его. Пять главных пунктов дали одинаково удобную структуру у обеих моделей. У краткого пересказа и плана не было числовой границы, поэтому ответы получились объёмными. Практические выводы полезны для действий, но это уже рекомендации, а не простой пересказ. Промпты меняют несколько условий сразу, поэтому вывод относится к целым формулировкам.

### 5.4. Вопросы по тексту

Общая инструкция: `Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.` Затем передавался полный текст.

**Прямой вопрос:** According to the source, which similarity measure can a vector index use?

| Модель | Полный ответ |
| --- | --- |
| Kimi |  cosine similarity |
| Qwen | cosine similarity |

**Смысловой вопрос:** Why can RAG improve inspectability while not guaranteeing truth?

| Модель | Полный ответ |
| --- | --- |
| Kimi |  RAG improves inspectability because it inserts selected passages into the prompt as evidence, which reduces dependence on the model's parametric memory and makes an answer easier to inspect. It does not guarantee truth because retrieval may return irrelevant passages, the context may be incomplete, and the model may misinterpret the evidence. |
| Qwen | RAG improves inspectability because it makes the evidence used to generate an answer explicit: the retrieved passages are inserted into the prompt as evidence, allowing humans to verify whether the answer is supported by the provided context. This transparency enables inspection of retrieval (e.g., checking relevance and accuracy of retrieved fragments) and generation (e.g., assessing whether the model correctly uses or misinterprets the evidence). However, RAG does not guarantee truth because retrieval may return irrelevant, incomplete, or outdated passages; the model may misinterpret or hallucinate despite the evidence; and conflicting or erroneous information in the corpus may be faithfully cited. Truth depends on the quality and correctness of the retrieved documents and the model’s faithful reasoning from them—not on the RAG architecture itself. |

**Ответа нет в тексте:** According to the source, who invented RAG and in what year?

| Модель | Полный ответ |
| --- | --- |
| Kimi |  The information is unavailable. |
| Qwen | The information is unavailable. |

Обе модели ответили cosine similarity на прямой вопрос и вернули точную фразу “The information is unavailable.” на вопрос об авторе и годе. На смысловой вопрос обе объяснили прозрачность свидетельств и отсутствие гарантии истины; Qwen подробнее использовала примеры версий и конфликтующих фрагментов из расширенного текста. В этой выборке соблюдение границы контекста одинаково; один пример не гарантирует такое поведение всегда.

### 5.5. Форматы ответа

Во всех трёх запросах одинаковый предмет ответа: **назначение, процесс поиска, ограничения достоверности и требования безопасности**. Меняется только формат. Общая инструкция:

> Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below.

Добавляемые инструкции:

| Формат | Инструкция |
| --- | --- |
| Абзац | Return one paragraph covering all four aspects. |
| Список | Return exactly four bullet points, one per aspect in the given order. |
| JSON | Return valid JSON only, with exactly four string keys: "purpose", "retrieval", "limitations", and "security". No Markdown fences or extra text. |

| Модель | Формат | Проверка структуры | Слов |
| --- | --- | --- | --- |
| Qwen | plain_text | Пройдена | 195 |
| Kimi | plain_text | Пройдена | 208 |
| Kimi | list | Пройдена | 290 |
| Qwen | list | Пройдена | 142 |
| Qwen | json | Пройдена | 155 |
| Kimi | json | Пройдена | 478 |

Автоматическая проверка прошла для всех шести ответов: оба абзаца остались одним абзацем, оба списка имеют ровно четыре пункта, оба JSON разбираются и содержат точные четыре строковых ключа. Содержание одинаково охватывает назначение, retrieval, ограничения и безопасность. JSON Kimi длиннее (478 слов против 155), JSON Qwen быстрее просматривать. Список удобен для человека, JSON — для программы. По соблюдению структуры результат равный.

### 5.6. Проверяемые факты

Использован отдельный запрос на шесть пронумерованных фактов с датами, числами, технологиями, авторами, точными названиями и URL. Не менее трёх утверждений должны относиться к публикациям или документированным инструментам. Каждый факт требуется пометить как основанный на исходном тексте или внешний; при неуверенности — прямо сообщить об этом. Полная инструкция:

```text
Write six concise, numbered, verifiable factual claims about RAG. Across the claims include publication dates, numbers, technology names, author names, exact document titles, and URLs. Include at least three claims about named research papers or documented tools, with a primary source URL for each. Label every claim either SUPPORTED BY THE SUPPLIED TEXT or EXTERNAL TO THE SUPPLIED TEXT. External knowledge is allowed, but say when you are uncertain; do not invent references or present illustrative numerical settings as universal defaults. Keep the answer within 450 words. The supplied text is:

[Полный исходный текст раздела 4]
```

Три выбранные ссылки Kimi ведут на реальные первичные публикации с совпадающими заглавиями, датами и первыми авторами; формулировка «introduced RAG» нуждается в уточнении. В ответе Qwen верна ссылка на Lewis et al., но Ragas приписана неправильным авторам, а ссылка на Hugging Face возвращает 404. Это конкретные находки в небольшом наборе, не оценка общей частоты ошибок модели.

### 5.7. Методика оценки

Каждый ответ оценён по шести критериям: точность, полнота, ясность, следование инструкции, структура, проверяемость. Оценки — аналитическая разметка текста при подготовке отчёта, а не автоматический вывод модели или независимая экспертная аттестация. Студенту следует уметь объяснить приведённые комментарии.

Шкала: 5 — нет существенных замечаний; 4 — небольшое упущение или избыточное обобщение; 3 — заметная проблема при сохранении пользы; 2 — большая часть задачи не выполнена; 1 — ответ непригоден. Полнота оценивается относительно задачи: короткий правильный отказ при отсутствии информации может получить 5.

## 6. Таблица результатов

В таблице `слов` соответствует полю `word_count`: буквенно-цифровые группы с сохранением внутренних дефисов и апострофов. Числа тоже считаются единицами. Дополнительно сохранён старый счётчик `length_words` на основе `\b\w+\b`; он иначе обрабатывает дефисы и сокращения. Лимиты слов интерпретируются с учётом этой условности. Символы считаются через `len(output)`, включая пробелы и переносы.

| Модель | Промпт | Время, с | Символов | Слов | Токенов ответа | Завершение |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi | task_2/identical_explanation | 16.664 | 692 | 103 | 1264 | stop |
| Qwen | task_2/identical_explanation | 1.603 | 725 | 109 | 164 | stop |
| Qwen | task_3/summary | 1.46 | 779 | 104 | 140 | stop |
| Kimi | task_3/summary | 57.495 | 622 | 80 | 4695 | stop |
| Kimi | task_3/main_points | 19.702 | 2373 | 325 | 1553 | stop |
| Qwen | task_3/main_points | 3.008 | 1754 | 240 | 323 | stop |
| Qwen | task_3/short_recap | 3.575 | 1695 | 208 | 393 | stop |
| Kimi | task_3/short_recap | 12.585 | 2495 | 338 | 1189 | stop |
| Kimi | task_3/outline | 30.168 | 4350 | 547 | 2909 | stop |
| Qwen | task_3/outline | 8.701 | 3666 | 470 | 1011 | stop |
| Qwen | task_3/takeaways | 4.047 | 2189 | 275 | 446 | stop |
| Kimi | task_3/takeaways | 15.871 | 3787 | 529 | 1351 | stop |
| Kimi | task_4/direct | 3.36 | 18 | 2 | 218 | stop |
| Qwen | task_4/direct | 0.423 | 17 | 2 | 4 | stop |
| Qwen | task_4/inference | 1.593 | 862 | 126 | 152 | stop |
| Kimi | task_4/inference | 4.129 | 345 | 51 | 288 | stop |
| Kimi | task_4/unavailable | 2.179 | 32 | 4 | 134 | stop |
| Qwen | task_4/unavailable | 0.389 | 31 | 4 | 6 | stop |
| Qwen | task_5/plain_text | 2.291 | 1427 | 195 | 241 | stop |
| Kimi | task_5/plain_text | 24.162 | 1476 | 208 | 2280 | stop |
| Kimi | task_5/list | 35.522 | 2051 | 290 | 3423 | stop |
| Qwen | task_5/list | 1.897 | 1091 | 142 | 190 | stop |
| Qwen | task_5/json | 2.117 | 1171 | 155 | 205 | stop |
| Kimi | task_5/json | 32.264 | 3307 | 478 | 3109 | stop |
| Kimi | task_6/fact_probe | 63.978 | 1356 | 193 | 6176 | stop |
| Qwen | task_6/fact_probe | 4.282 | 1713 | 230 | 456 | stop |

| Модель | Ответов | Среднее, с | Медиана, с | Обрезанных | Ошибок API |
| --- | --- | --- | --- | --- | --- |
| Kimi | 13 | 24.468 | 19.702 | 0 | 0 |
| Qwen | 13 | 2.722 | 2.117 | 0 | 0 |

Qwen была быстрее во всех 13 парных запросах. Среднее/медианное клиентское время: Kimi — 24.468/19.702 с; Qwen — 2.722/2.117 с. Это один запуск для этих моделей и этой сервисной инфраструктуры; цифры не являются универсальной скоростью моделей. Ошибок API и ответов, ограниченных бюджетом токенов, нет.

Дополнительные счётчики ниже считают вхождения, а не уникальные факты. Числа могут встречаться в нумерации и URL. Языковые маркеры ищутся с границами слов: «точно» больше не совпадает с частью слова «недостаточно». Добавлены английские маркеры, включая `information is unavailable`. Это лексический индикатор, не семантическая оценка уверенности: например, `may` может иметь несколько значений, а отрицание перед `guaranteed` отдельно не анализируется.

| Модель | Промпт | Числа | Годы | URL | Осторожность | Уверенность |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi | task_4/unavailable | 0 | 0 | 0 | 1 | 0 |
| Qwen | task_4/unavailable | 0 | 0 | 0 | 1 | 0 |
| Kimi | task_6/fact_probe | 12 | 4 | 3 | 0 | 0 |
| Qwen | task_6/fact_probe | 16 | 7 | 3 | 1 | 0 |

## 7. Анализ качества

Т — точность; П — полнота; Я — ясность; И — следование инструкции; С — структура; В — проверяемость. Для внешних фактов выводы ограничены проверенной выборкой утверждений.

| Модель | Промпт | Т | П | Я | И | С | В | Комментарий |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi | task_2/identical_explanation | 4 | 5 | 5 | 5 | 5 | 4 | Объяснение понятное, пример практический; фраза о том, что RAG сокращает галлюцинации, может прозвучать как гарантия. |
| Qwen | task_2/identical_explanation | 4 | 5 | 5 | 5 | 5 | 4 | Ответ укладывается в лимит и содержит ясный пример; слово «обеспечивает» преувеличивает гарантии актуальности. |
| Qwen | task_3/summary | 5 | 5 | 5 | 2 | 5 | 5 | Хорошее резюме, но 104 слова превышают заданный максимум 80. |
| Kimi | task_3/summary | 5 | 5 | 5 | 5 | 5 | 5 | 80 слов по использованному счётчику; сохранены назначение, этапы, ограничения и меры защиты. |
| Kimi | task_3/main_points | 5 | 5 | 5 | 5 | 5 | 5 | Ровно пять подробных пунктов охватывают основные разделы источника. |
| Qwen | task_3/main_points | 5 | 5 | 5 | 5 | 5 | 5 | Ровно пять более кратких пунктов сохраняют те же основные идеи. |
| Qwen | task_3/short_recap | 5 | 5 | 5 | 5 | 5 | 5 | Связный пересказ для инженера; учитывает версии, индекс и работу со свидетельствами. |
| Kimi | task_3/short_recap | 5 | 5 | 5 | 5 | 5 | 5 | Понятный пересказ с основными ограничениями и эксплуатационными аспектами. |
| Kimi | task_3/outline | 5 | 5 | 5 | 5 | 5 | 5 | Полный иерархический план; 547 слов оправданы подробной структурой. |
| Qwen | task_3/outline | 5 | 5 | 5 | 5 | 5 | 5 | Полный и хорошо вложенный план; 470 слов — короче ответа Kimi. |
| Qwen | task_3/takeaways | 5 | 5 | 5 | 5 | 5 | 5 | Практические пункты охватывают фрагментацию, метаданные, индекс, безопасность и оценку. |
| Kimi | task_3/takeaways | 5 | 5 | 5 | 5 | 5 | 5 | Подробные рекомендации близко следуют расширенному исходному тексту. |
| Kimi | task_4/direct | 5 | 5 | 5 | 5 | 5 | 5 | Точный прямой ответ по исходному тексту. |
| Qwen | task_4/direct | 5 | 5 | 5 | 5 | 5 | 5 | Точный прямой ответ по исходному тексту. |
| Qwen | task_4/inference | 5 | 5 | 5 | 5 | 5 | 5 | Связывает проверяемость с явными свидетельствами и использует обсуждённые в тексте устаревшие и конфликтующие фрагменты. |
| Kimi | task_4/inference | 5 | 5 | 5 | 5 | 5 | 5 | Краткое и точное объяснение, подтверждаемое исходным текстом. |
| Kimi | task_4/unavailable | 5 | 5 | 5 | 5 | 5 | 5 | Выдана запрошенная фраза об отсутствии информации. |
| Qwen | task_4/unavailable | 5 | 5 | 5 | 5 | 5 | 5 | Выдана запрошенная фраза об отсутствии информации. |
| Qwen | task_5/plain_text | 5 | 5 | 5 | 5 | 5 | 5 | Один абзац охватывает все четыре требуемых аспекта. |
| Kimi | task_5/plain_text | 5 | 5 | 5 | 5 | 5 | 5 | Связный абзац описывает назначение, поиск, ограничения и безопасность. |
| Kimi | task_5/list | 5 | 5 | 4 | 5 | 4 | 5 | Ровно четыре корректных пункта; пункты длинные, но смысловые категории различимы. |
| Qwen | task_5/list | 5 | 5 | 5 | 5 | 5 | 5 | Четыре кратких пункта в заданном порядке. |
| Qwen | task_5/json | 5 | 5 | 5 | 5 | 5 | 5 | Валидный JSON с точными четырьмя ключами и строковыми значениями; дополнительного текста нет. |
| Kimi | task_5/json | 5 | 5 | 4 | 5 | 5 | 5 | Валидный JSON с требуемой схемой; 478 слов затрудняют быстрое чтение значений. |
| Kimi | task_6/fact_probe | 4 | 5 | 5 | 5 | 5 | 5 | Три проверенные ссылки ведут на реальные публикации. Формулировка «ввели RAG» шире, чем утверждение статьи о предложенных в ней моделях RAG. |
| Qwen | task_6/fact_probe | 2 | 4 | 4 | 3 | 3 | 3 | Авторы статьи Ragas указаны неверно, а ссылка на репозиторий Hugging Face возвращает 404; остальные выбранные факты подтверждаются. |

В этом запуске Kimi точно выполнила ограничение суммаризации и дала более краткий список фактов. Qwen отвечала быстрее и кратко соблюдала структурированные форматы. Обе правильно обработали отсутствующий ответ и прошли автоматические проверки формата. В выбранной ручной проверке внешних фактов у Qwen выявлены ошибка авторства Ragas и неработающий URL. Выборка и один повтор не позволяют присвоить моделям общий рейтинг.

## 8. Проверка фактов и поиск галлюцинаций

Утверждения сопоставлены с первичными открытыми источниками при подготовке отчёта. «Внешнее по отношению к исходному тексту» не означает «ложное». Подтверждение ссылки не подтверждает автоматически все утверждения рядом с ней; поэтому проверяется конкретное содержание. Таблица содержит не менее трёх утверждений каждой модели из задания 6.

| Модель | Проверяемое утверждение | Источник | Вердикт | Обоснование |
| --- | --- | --- | --- | --- |
| Kimi | Lewis et al. introduced retrieval-augmented generation in the 2020 NeurIPS paper Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. | [Первичный источник](https://arxiv.org/abs/2005.11401) | Подтверждено с уточнением | Название, авторы, дата препринта 2020 года и принятие на NeurIPS подтверждаются. Точнее: в статье представлены определённые модели RAG; она не доказывает первенство всей идеи retrieval augmentation. |
| Kimi | Gao et al. published the survey Retrieval-Augmented Generation for Large Language Models: A Survey in 2023. | [Первичный источник](https://arxiv.org/abs/2312.10997) | Подтверждено | Первая версия arXiv подана 18 декабря 2023 года; название и первый автор совпадают. |
| Kimi | Asai et al. proposed Self-RAG in the 2023 paper Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. | [Первичный источник](https://arxiv.org/abs/2310.11511) | Подтверждено | Запись arXiv подтверждает название, Akari Asai как первого автора и дату первой версии — 17 октября 2023 года. |
| Qwen | The paper by Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks, is from 2020. | [Первичный источник](https://arxiv.org/abs/2005.11401) | Подтверждено с уточнением | Название, Patrick Lewis, соавторы и дата первой версии — 22 мая 2020 года — подтверждаются. Фразу «ввели RAG» следует уточнить: статья представляет конкретные модели RAG. |
| Qwen | The URL https://github.com/huggingface/transformers/tree/main/examples/research_projects/rag contains the RAG implementation and its Apache 2.0 license. | [Первичный источник](https://github.com/huggingface/transformers/tree/main/examples/research_projects/rag) | Ссылка не работает; лицензия не подтверждена | При проверке 2 октября 2026 года указанный путь возвращает 404. Похожий проект есть в отдельном репозитории transformers-research-projects/rag; приведённый URL не подтверждает ни реализацию, ни её лицензию. |
| Qwen | Ragas: Automated Evaluation of Retrieval Augmented Generation was written by Pawar et al. in 2023, arXiv:2309.15217. | [Первичный источник](https://arxiv.org/abs/2309.15217) | Ошибка в авторах; статья и год подтверждены | Идентификатор и дата публикации 2023 года реальны, но авторы — Shahul Es, Jithin James, Luis Espinosa-Anke и Steven Schockaert, а не Pawar et al. |
| Qwen | RAG fragment metadata may include title, version, owner, access policy, and update time. | [Первичный источник](source_text.txt) | Подтверждено исходным текстом | В исходном тексте прямо перечислены эти поля метаданных и описано их использование для фильтрации и цитирования. |

Проверка выявила две конкретные проблемы у Qwen: неверная атрибуция авторов статьи Ragas и неработающий путь GitHub. Остальные выбранные утверждения подтверждены с оговоркой об авторстве и области источника. У Kimi не установлено ложных сведений в трёх выбранных ссылках, но заявление, что статья Lewis et al. ввела всю идею RAG, шире подтверждаемого факта о конкретных RAG-моделях. URL нужно открыть и сверить с точным утверждением.

Для дальнейшего снижения риска можно требовать источник для каждого числа и даты, отделять внешние сведения от текста, разрешать ответ «неизвестно» и не требовать заполнить заданное число фактов при недостатке доказательств. Для задач только по тексту внешние знания нужно явно исключать. Эти меры не заменяют проверку, а влияние каждой из них отдельно в данном запуске не измерялось.

## 9. Выводы

1. **Различия моделей.** Qwen была быстрее во всех 13 запросах; медианы — 2.117 с у Qwen и 19.702 с у Kimi. Все 26 ответов закончены без API-ошибок и обрезки.
2. **Влияние промпта.** Числовой предел 80 слов дал краткое резюме Kimi; запрос пяти пунктов облегчает сравнение; свободный план и пересказ длиннее.
3. **Полезные инструкции.** «Только по этому тексту», точная фраза для отсутствующих данных, одинаковая область четырёх смысловых аспектов и строгая схема JSON повысили проверяемость.
4. **Внешние утверждения.** Запрос фактов разрешал внешний контекст. Проверка выявила у Qwen неверного автора и неработающую ссылку, несмотря на внешне точный ответ.
5. **Необходимость проверки.** Реальный URL не гарантирует правильную атрибуцию или поддержку тезиса; проверять нужно содержание страницы, автора, название, дату и точное утверждение.
6. **Надёжность в рамках эксперимента.** В трёх выбранных внешних утверждениях Kimi было меньше установленных ошибок; Qwen существенно быстрее. Малая выборка не поддерживает универсальный рейтинг.

### Ограничения и воспроизводимость

На каждый промпт сохранён один ответ: статистическая устойчивость различий не установлена. Температура 0,2 снижает случайность, но не гарантирует идентичные повторения. Верхний предел токенов общий, но модели и серверные реализации различаются. Слова, длина и число ссылок не заменяют оценку смысла. Часть формулировок суммаризации одновременно меняет структуру и ожидаемый объём, поэтому нельзя изолировать влияние одного слова.

Статус сбора данных: `success`. Этот статус означает техническую завершённость запросов, а не фактическую правильность всех ответов. Программные регрессионные проверки выполнены отдельно от обращений к API.

Материалы текущего запуска: `results/lab1_corrected/`. В папке находятся CSV с промптами и ответами, `source_text.txt`, `manifest.json`, снимок исходного кода, заполненные `quality_scores.csv`, `hallucination_verification.csv` и аналитические заметки `review_notes.json`. Поле `manual_verification_required` отражает состояние при сборе данных; завершённая проверка оформлена отдельными файлами.

Для повторного построения документа без новых API-запросов:

```powershell
python -m pip install -r requirements-report.txt
python -m lab1.report --run-dir results/lab1_corrected
```

Предыдущая версия сохранена в `results/lab1_archive/before_fixes_2026-09-30/`. Старые численные результаты и оценки не переносились в новую таблицу.

## Приложение А. Список доступных идентификаторов

```text
BAAI/bge-m3
BAAI/bge-reranker-v2-m3
GigaChat/GigaChat-2-Max
GigaChat/GigaChat-3-Pro
MiniMaxAI/MiniMax-M2.5
MiniMaxAI/MiniMax-M3
Qwen/Qwen3-30B-A3B
Qwen/Qwen3-32B
Qwen/Qwen3-Coder-Next
Qwen/Qwen3-Embedding-0.6B
Qwen/Qwen3-Reranker-0.6B
Qwen/Qwen3-VL-Embedding-2B
Qwen/Qwen3-VL-Embedding-8B
Qwen/Qwen3-VL-Reranker-2B
Qwen/Qwen3-VL-Reranker-8B
Qwen/Qwen3.5-397B-A17B
Qwen/Qwen3.6-35B-A3B
ai-sage/GigaChat3-10B-A1.8B
ai-sage/GigaChat3.5-432B-A28B
ai-sage/GigaChat3.5-432B-A28B-Reasoning
anthropic/claude-haiku-4.5
anthropic/claude-opus-4.1
anthropic/claude-opus-4.5
anthropic/claude-opus-4.6
anthropic/claude-opus-4.7
anthropic/claude-opus-4.8
anthropic/claude-sonnet-4
anthropic/claude-sonnet-4.5
anthropic/claude-sonnet-4.6
deepseek-ai/DeepSeek-OCR-2
deepseek-ai/DeepSeek-V4-Flash
deepseek-ai/DeepSeek-V4-Pro
deepseek-ai/DeepSeek-V4.1-Flash
deepseek/deepseek-chat-v3-0324
deepseek/deepseek-r1-distill-llama-70b
deepseek/deepseek-v3.2
google/gemini-2.5-flash
google/gemini-2.5-flash-image
google/gemini-2.5-pro
google/gemini-3-flash-preview
google/gemini-3-pro-image-preview
google/gemini-3.1-flash-image-preview
google/gemini-3.1-flash-lite
google/gemini-3.1-pro-preview
google/gemini-embedding-001
hivetrace/HiveTraceGuard-Pro
meta-llama/llama-3.3-70b-instruct
moonshotai/Kimi-K2.6
moonshotai/kimi-k2-0905
moonshotai/kimi-k2-thinking
moonshotai/kimi-k2.5
openai/chatgpt-4o-latest
openai/gpt-4.1
openai/gpt-4.1-mini
openai/gpt-4.1-nano
openai/gpt-4o-mini
openai/gpt-5
openai/gpt-5-chat
openai/gpt-5-mini
openai/gpt-5-nano
openai/gpt-5.1
openai/gpt-5.1-chat
openai/gpt-5.2
openai/gpt-5.2-chat
openai/gpt-5.2-codex
openai/gpt-5.3-chat
openai/gpt-5.3-codex
openai/gpt-5.4
openai/gpt-5.4-mini
openai/gpt-5.4-nano
openai/gpt-5.4-pro
openai/gpt-5.5
openai/gpt-5.5-pro
openai/gpt-oss-120b
openai/gpt-oss-20b
openai/text-embedding-3-large
openai/text-embedding-3-small
openai/whisper-large-v3
qwen/qwen3-235b-a22b
qwen/qwen3-max-thinking
qwen/qwen3-vl-235b-a22b-instruct
qwen/qwen3-vl-235b-a22b-thinking
qwen/qwen3-vl-30b-a3b-instruct
qwen/qwen3-vl-30b-a3b-thinking
qwen/qwen3-vl-8b-instruct
qwen/qwen3-vl-8b-thinking
xiaomi/mimo-v2.5
xiaomi/mimo-v2.5-pro
z-ai/glm-4.5-air
z-ai/glm-4.6
z-ai/glm-4.6v
z-ai/glm-5
zai-org/GLM-4.7
zai-org/GLM-5.1
zai-org/GLM-5.2
```

## Приложение Б. Все исходные ответы

Приведены все 26 ответов без исправления их содержания. В промптах повтор исходного текста заменён ссылкой на раздел 4; полные сообщения сохранены в CSV. Ответы заключены в кодовые блоки, чтобы отделить их от анализа.

### Б.1. Kimi — task_2/identical_explanation

**Промпт:**

```text
Explain the concept of retrieval-augmented generation to a second-year software engineering student in 120 words or fewer. Include one practical example.
```

**Ответ:** 16.664 с; 103 слов; `stop`.

```text
 Retrieval-Augmented Generation (RAG) enhances LLMs by fetching external data at runtime. When a user asks a question, the system performs a similarity search (e.g., using vector embeddings) over a knowledge base to retrieve relevant documents. It then injects those snippets into the LLM's prompt as context, so the model generates answers grounded in factual, up-to-date sources rather than relying solely on parametric memory. This cuts hallucinations and supports private data.

**Example:** A support bot embeds a company's API docs into a vector database. When asked, "How do I handle rate limiting?" it retrieves the latest documentation and synthesizes an accurate, referenced answer.
```

### Б.2. Qwen — task_2/identical_explanation

**Промпт:**

```text
Explain the concept of retrieval-augmented generation to a second-year software engineering student in 120 words or fewer. Include one practical example.
```

**Ответ:** 1.603 с; 109 слов; `stop`.

```text
Retrieval-Augmented Generation (RAG) combines a *retrieval* system (like a search engine) with a *generation* model (like LLMs). When a user asks a question, RAG first fetches relevant, up-to-date documents from an external knowledge base (e.g., a company’s PDFs or a database), then feeds both the query and retrieved context into the LLM to generate a grounded, accurate response—reducing hallucinations and enabling access to real-time data.

**Example**: A customer support chatbot uses RAG to answer “How do I reset my password?” by retrieving the latest *Security Policy.pdf* from your internal wiki, then generating a step-by-step guide based *only* on that document—ensuring instructions match current company policy.
```

### Б.3. Qwen — task_3/summary

**Промпт:**

```text
Summarize the source in no more than 80 words.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 1.46 с; 104 слов; `stop`.

```text
RAG combines a language model with an external document collection: a retriever finds relevant passages, which are inserted into the prompt as evidence. The pipeline includes document loading, chunking (with overlap), indexing (keyword or vector), retrieval, and generation. RAG does not guarantee truth—retrieval may be irrelevant or incomplete, and models may misinterpret evidence. Applications must enforce citation, expose conflicts, and assess both answer quality and faithfulness to retrieved context. Production systems monitor latency, precision, token usage, and failure rates, while implementing access controls, caching, and metadata-aware filtering. Indexes must be updated when documents change, and evaluation requires questions with expected evidence and answers.
```

### Б.4. Kimi — task_3/summary

**Промпт:**

```text
Summarize the source in no more than 80 words.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 57.495 с; 80 слов; `stop`.

```text
 Retrieval-augmented generation (RAG) augments language models by retrieving document passages to insert as evidence, reducing reliance on internal knowledge. A pipeline involves chunking, indexing, and retrieval, but it does not guarantee truth because retrieval can fail or evidence can be misinterpreted. Success requires careful chunking, metadata filtering, index maintenance, and separate evaluation of retrieval and generation. Production demands security controls, access restrictions, citation accuracy, and monitoring latency and costs, making RAG an application architecture rather than a guarantee of accuracy.
```

### Б.5. Kimi — task_3/main_points

**Промпт:**

```text
Extract the five main points from the source.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 19.702 с; 325 слов; `stop`.

```text
 1. **RAG fundamentals and pipeline** — Retrieval-augmented generation combines a language model with an external document collection. Before generating an answer, a retriever searches the collection for relevant passages and inserts them into the prompt as evidence, reducing dependence on the model’s parametric memory. A typical pipeline comprises document loading, chunking, indexing, retrieval, and generation.

2. **Design tradeoffs in chunking, indexing, and retrieval** — Chunk size, overlap, and top-k settings are application-specific choices rather than universal constants; small fragments can lose necessary context, while large ones waste context window and introduce irrelevant material. Indexes may be keyword-based (transparent, debuggable) or vector-based (embedding similarity), and preserving document metadata—such as version, title, and access policy—helps filter results and produce meaningful citations.

3. **No guarantee of truth and the need for careful evidence handling** — RAG can fail when retrieval returns irrelevant or incomplete passages, when the model misinterprets evidence, or when indexed fragments are obsolete. If two passages conflict, the system should expose the conflict rather than silently choose one. Applications should ask the model to separate evidence from assumptions, cite the passages that actually support the answer, and state when the context is insufficient.

4. **Evaluation must test retrieval and generation separately** — Evaluation should use representative questions, including straightforward ones, ones requiring combined passages, and ones that are unanswerable from the corpus. An answer should not be scored highly merely for repeating words from the context; reviewers must check that main claims follow from the supplied passages and that important qualifications are preserved.

5. **Production safeguards and operational monitoring** — Teams must monitor latency, retrieval precision, token usage, and failure rates, and can cache repeated queries to reduce latency. Retrieved documents are untrusted data, so prompt injection via a document must not override system policy. Access controls and authorization must be enforced by the application—not by prompts alone—before private passages are exposed, and cached answers must respect user permissions and the freshness of the underlying documents.
```

### Б.6. Qwen — task_3/main_points

**Промпт:**

```text
Extract the five main points from the source.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 3.008 с; 240 слов; `stop`.

```text
1. **RAG Pipeline Structure**: A RAG system follows a pipeline of document loading, chunking, indexing, retrieval, and generation—where chunking divides documents into fragments (often with overlap), indexing stores fragment representations (e.g., keyword or vector), and retrieval fetches top-k relevant passages to augment the prompt.

2. **RAG Does Not Guarantee Truth**: Retrieval may yield irrelevant or incomplete passages, and the model may misinterpret evidence; thus, applications should require the model to cite passages, separate evidence from assumptions, and declare insufficient context, with evaluation measuring both answer quality and faithfulness to retrieved context.

3. **Metadata and Contextual Relevance Matter**: Document metadata (e.g., version, title, owner, update time) attached to fragments enables filtering (e.g., by software version) and meaningful citations, ensuring answers reflect the correct context and avoid outdated or irrelevant information.

4. **Design Choices Require Evaluation**: Chunk size and retrieval depth (k) are trade-offs—small chunks risk fragmenting valid instructions, large chunks add noise and context cost, and higher k improves coverage but increases latency and potential distraction; optimal settings depend on documents, queries, retrieval method, and context budget.

5. **Operational Safeguards and Maintenance Are Critical**: Indexes must be updated when documents change to avoid obsolete retrieval; access controls must be enforced at the application layer (not via prompts); logs and caching must protect confidentiality; and systems should surface conflicts between passages rather than silently favor one claim—emphasizing RAG as an application architecture, not a truth guarantee.
```

### Б.7. Qwen — task_3/short_recap

**Промпт:**

```text
Briefly retell the source for a busy engineer.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 3.575 с; 208 слов; `stop`.

```text
**RAG in a Nutshell for Busy Engineers:**  
RAG augments a language model with a retriever that fetches relevant document passages (from a corpus) to ground answers—reducing reliance on the model’s internal knowledge and improving traceability.

**Core Pipeline:**  
1. **Load & chunk** documents (with overlap, tuned size).  
2. **Index** fragments (keyword or vector-based).  
3. **Retrieve** top-*k* relevant passages.  
4. **Generate** answer using retrieved context.

**Key Caveats & Best Practices:**  
- ❌ **Not truth-guaranteed**: retrieval may be irrelevant/incomplete; model may misinterpret.  
- ✅ **Mitigate risks**:  
  - Require citations to *exact passages* (not just doc titles).  
  - Force model to separate evidence vs. assumptions.  
  - Flag insufficient context or conflicting passages.  
- 🔐 **Security & compliance**:  
  - Enforce access controls *outside* the model (not via prompts).  
  - Sanitize logs/caches; respect document freshness & user permissions.  
- 📊 **Evaluate rigorously**:  
  - Measure faithfulness (claims supported by context), not just fluency.  
  - Test retrieval *and* generation separately.  
- ⚙️ **Tune pragmatically**:  
  - Chunk size, *k*, and index type depend on your docs, queries, and latency budget.  
  - Maintain indices *independently* of model training (update/remove stale fragments).  

**Example Use Case:** Internal support assistant—metadata (e.g., version, owner) on fragments ensures answers cite *correct* release info and enforce access policies.  

**Bottom Line:** RAG is an *application architecture*—not a plug-and-play fix. Success hinges on thoughtful data management, retrieval design, and operational safeguards.
```

### Б.8. Kimi — task_3/short_recap

**Промпт:**

```text
Briefly retell the source for a busy engineer.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 12.585 с; 338 слов; `stop`.

```text
 **RAG in a nutshell:** It pairs an LLM with an external document collection. A retriever fetches relevant passages and inserts them into the prompt as evidence. This reduces reliance on the model’s internal knowledge and makes answers inspectable.

**Pipeline:** Document loading → chunking → indexing → retrieval → generation.

**Key design choices**
- **Chunking:** Not one-size-fits-all. Too small splits conditions from instructions; too large wastes context and adds noise. Overlap preserves continuity but duplicates text. Tune on representative questions.
- **Index:** Keyword indexes are transparent and debuggable; vector indexes use embedding similarity (e.g., cosine).
- **Top-k:** Higher *k* can improve coverage but increases latency and may introduce distracting passages.

**It does not guarantee truth**
- Retrieval can miss, context can be incomplete, and the model can misinterpret evidence.
- Require the model to separate evidence from assumptions, cite the supplied passages, and state when context is insufficient.

**Citations & data integrity**
- Keep metadata (title, version, owner, access policy, update time) attached to fragments so you can filter and cite correctly. A passage about an older software version may be on-topic but wrong for the user’s question.
- Update or remove indexed fragments when documents change, or retrieval will serve stale info.
- A citation is useful only if it points to the passage that actually supports the answer. If two passages conflict, expose the conflict rather than silently picking a winner.

**Production & security**
- Monitor latency, retrieval precision, token usage, and failure rates. Cache repeated queries.
- Enforce authorization **in the application** before exposing private passages; prompts are not an access-control mechanism.
- Treat retrieved documents as untrusted data. Prevent prompt injection inside a document from overriding system policy.
- Evaluation logs must avoid leaking confidential documents/credentials. Cache must respect user permissions and document freshness.

**Evaluation tips**
- Test straightforward questions, questions requiring combined passages, and unanswerable questions.
- Inspect retrieval and generation separately. A correct passage can still yield a wrong answer; a fluent answer can conceal retrieval failure.
- Don’t reward answers that merely repeat words from the context. Verify that main claims follow from the passages and that important qualifications are preserved.
```

### Б.9. Kimi — task_3/outline

**Промпт:**

```text
Create a concise hierarchical outline of the source.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 30.168 с; 547 слов; `stop`.

```text
 I. Core Concept  
   A. Definition: Combines a language model with an external document collection.  
   B. Mechanism: A retriever searches the collection for relevant passages and inserts them into the prompt as evidence before generation.  
   C. Benefits: Reduces dependence on parametric memory; makes answers easier to inspect.  

II. Typical Pipeline  
    A. Stages: Document loading, chunking, indexing, retrieval, and generation.  
    B. Chunking: Divides long documents into smaller fragments, often with overlap.  
    C. Indexing: Stores a representation of each fragment.  
       1. Keyword index: Transparent and easy to debug.  
       2. Vector index: Compares embeddings via similarity measures (e.g., cosine similarity).  
    D. Retrieval: Returns the top-k fragments, where k is configurable.  

III. Limitations and Mitigation  
     A. No truth guarantee: Retrieval may return irrelevant passages; context may be incomplete; the model may misinterpret evidence.  
     B. Required model behaviors: Separate evidence from assumptions; cite supplied passages; state when context is insufficient.  
     C. Evaluation criteria: Measure both answer quality and adherence to retrieved context.  

IV. Production Operations  
    A. Monitoring: Latency, retrieval precision, token usage, and failure rates.  
    B. Performance: Cache repeated queries to reduce latency.  
    C. Privacy: Access controls required for corpora containing private information.  
    D. Security: Retrieved documents are untrusted data; prevent document-based prompt injection from overriding system policy.  

V. Application Example: Internal Support Assistant  
   A. Corpus: Installation instructions, release notes, and troubleshooting guides.  
   B. Version sensitivity: Answers must refer to the version mentioned in the question; older passages may be topically relevant but versionally wrong.  
   C. Metadata: Title, version, owner, access policy, and update time should remain attached to fragments to enable filtering and meaningful citations.  

VI. Design Tradeoffs  
    A. Chunk size (not a universal constant):  
       1. Too small: Risks separating an instruction from its valid condition.  
       2. Too large: Risks including unrelated material and consuming excess context window.  
    B. Overlap: Preserves continuity near boundaries but duplicates text.  
    C. Top-k (k): Increasing k may improve coverage but increases latency and can introduce distracting passages.  
    D. Determinants: Optimal settings depend on documents, questions, retrieval method, and available context budget.  
    E. Validation: Evaluate chunking on representative questions; verify returned fragments contain sufficient evidence.  

VII. Index Maintenance and Citations  
     A. Maintenance: Updating or removing indexed fragments when documents are corrected is separate from language-model training; otherwise obsolete information persists.  
     B. Citation integrity: A citation must point to the passage that actually supports the answer; a title or plausible URL alone is insufficient.  
     C. Conflicts: If retrieved passages disagree, expose the conflict rather than silently presenting certainty; human review may be required.  

VIII. Evaluation Methodology  
      A. Test sets: Small collections of questions paired with expected evidence and acceptable answers.  
      B. Question types: Straightforward, multi-passage combination, and unanswerable questions.  
      C. Component inspection: Assess retrieval and generation separately.  
      D. Faithfulness:  
         1. Not measured by mere repetition of words from the context.  
         2. Verify that main claims follow from supplied passages.  
         3. Verify that important qualifications are preserved.  

IX. Operational Safeguards and System Nature  
    A. Authorization: Enforced by the application before exposing private passages; prompts alone are not an access-control mechanism.  
    B. Logging: Avoid disclosing confidential documents or credentials in evaluation logs.  
    C. Caching: Must respect user access permissions and the freshness of underlying documents.  
    D. Nature of RAG: An application architecture encompassing data management, retrieval, generation, and evaluation—not a guarantee of accurate answers from a language model.
```

### Б.10. Qwen — task_3/outline

**Промпт:**

```text
Create a concise hierarchical outline of the source.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 8.701 с; 470 слов; `stop`.

```text
**Hierarchical Outline of the Source on Retrieval-Augmented Generation (RAG)**

I. **Core Concept of RAG**  
 A. Combines a language model with an external document collection  
 B. Retrieval phase: searches for passages relevant to the user’s question  
 C. Evidence injection: selected passages inserted into the prompt  
 D. Benefits: reduces reliance on parametric memory; improves answer inspectability  

II. **Typical RAG Pipeline**  
 A. Document loading  
 B. Chunking  
   1. Divides long documents into smaller fragments  
   2. Often includes overlap to preserve continuity  
   3. Chunk size is a design choice (trade-offs: too small vs. too large)  
 C. Indexing  
   1. Stores representations of fragments  
   2. Types:  
     a. Keyword index (transparent, debuggable)  
     b. Vector index (uses embeddings + similarity measure, e.g., cosine)  
 D. Retrieval  
   1. Returns top-*k* fragments (*k* configurable)  
   2. May return irrelevant, incomplete, or conflicting passages  
 E. Generation  
   1. Language model uses retrieved evidence to generate answer  

III. **Limitations and Risks**  
 A. RAG does not guarantee truth  
   1. Retrieval may be inaccurate or incomplete  
   2. Model may misinterpret evidence  
 B. Mitigation strategies:  
   1. Ask model to separate evidence from assumptions  
   2. Require citation of supplied passages  
   3. Prompt model to state when context is insufficient  

IV. **Production Considerations**  
 A. Monitoring metrics: latency, retrieval precision, token usage, failure rates  
 B. Optimization: caching repeated queries to reduce latency  
 C. Security & access control  
   1. Retrieved documents = untrusted data  
   2. Prompt injection in documents must not override system policy  
   3. Authorization enforced *by application*, not prompts  
   4. Logs and caches must respect confidentiality and permissions  

V. **Metadata and Contextual Relevance**  
 A. Metadata attached to fragments (e.g., title, version, owner, access policy, update time)  
 B. Enables filtering and meaningful citations  
 C. Critical for version-sensitive tasks (e.g., support assistant for software platform)  

VI. **Design Trade-offs and Tuning**  
 A. Chunking:  
   1. Evaluate on representative questions  
   2. Ensure returned fragments contain sufficient evidence  
 B. *k* (number of retrieved fragments):  
   1. Higher *k* improves coverage but increases latency and noise  
 C. Settings depend on: documents, questions, retrieval method, context budget  

VII. **Index Maintenance**  
 A. Separate from language-model training  
 B. Documents updated → indexed fragments must be updated or removed  
 C. Obsolete fragments risk surfacing incorrect information  

VIII. **Citation and Disagreement Handling**  
 A. Citations must point to *actual supporting passage*, not just document title/URL  
 B. If retrieved passages conflict:  
   1. System should expose the disagreement  
   2. May require human review  

IX. **Evaluation Framework**  
 A. Use small test set: questions + expected evidence + acceptable answers  
 B. Include:  
   1. Straightforward questions  
   2. Questions requiring passage combination  
   3. Unanswerable questions (to test coverage)  
 C. Evaluate retrieval and generation *separately*  
 D. Faithfulness assessment:  
   1. Claims must follow from supplied passages  
   2. Important qualifications must be preserved  
   3. Not sufficient to merely repeat context wording  

X. **RAG as an Application Architecture**  
 A. Involves data management, retrieval, generation, and evaluation  
 B. Not a guarantee of accuracy—operational safeguards are essential
```

### Б.11. Qwen — task_3/takeaways

**Промпт:**

```text
List the most useful practical takeaways from the source.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 4.047 с; 275 слов; `stop`.

```text
- **RAG reduces reliance on the model’s parametric memory** by grounding responses in externally retrieved, verifiable evidence.  
- **A RAG pipeline has five core stages**: document loading, chunking, indexing, retrieval, and generation.  
- **Chunking must be carefully tuned**:  
  - Very small chunks may split context (e.g., instructions from their conditions);  
  - Very large chunks may include irrelevant material and waste context budget;  
  - Overlap preserves continuity but duplicates text;  
  - Optimal size depends on document structure, question types, and context limits.  
- **Index choice matters**:  
  - Keyword indexes are transparent and easy to debug;  
  - Vector indexes use embeddings and similarity (e.g., cosine) for semantic search;  
  - Index maintenance is separate from model training—updates to documents require corresponding index updates.  
- **Retrieval is fallible**:  
  - Retrieved passages may be irrelevant, incomplete, or outdated;  
  - Metadata (e.g., version, title, owner, update time) attached to fragments enables filtering and accurate citation.  
- **Answers must be evaluated for faithfulness, not just fluency**:  
  - Check whether claims follow from the *specific* retrieved passages;  
  - Preserve qualifications and caveats from the context;  
  - Avoid high scores for verbatim repetition without logical grounding.  
- **Citation quality is critical**:  
  - Citations must point to the *exact passage* supporting a claim—not just a document title or URL;  
  - If retrieved passages conflict, the system should surface the disagreement rather than present one as certain.  
- **RAG does not guarantee truth**:  
  - Applications should prompt the model to separate evidence from assumptions, cite passages, and declare insufficient context.  
- **Operational safeguards are essential**:  
  - Enforce access controls *at the application level* (not via prompts);  
  - Ensure cached answers respect user permissions and document freshness;  
  - Protect logs and evaluation data from exposing confidential information.  
- **Production monitoring should track**: latency, retrieval precision, token usage, and failure rates.
```

### Б.12. Kimi — task_3/takeaways

**Промпт:**

```text
List the most useful practical takeaways from the source.
Use only the source below.

[Полный исходный текст раздела 4]
```

**Ответ:** 15.871 с; 529 слов; `stop`.

```text
 Here are the most useful practical takeaways from the source:

- **Design the full pipeline, not just the model.** A RAG system requires document loading, chunking, indexing, retrieval, and generation. Treat it as an application architecture involving data management, retrieval, generation, and evaluation rather than a guarantee of accurate answers.

- **Choose chunk size and overlap deliberately.** Very small fragments can separate an instruction from its necessary condition; very large fragments waste context window and introduce irrelevant material. Overlap preserves continuity but duplicates text. Evaluate chunking on representative questions to ensure returned fragments contain enough evidence.

- **Select the index type based on debugging needs.** A keyword index is transparent and easy to debug, while a vector index relies on embedding similarity (e.g., cosine similarity). Pick the approach that fits your retrieval and observability requirements.

- **Tune `k` (number of retrieved fragments) to your context budget.** Increasing `k` can improve coverage, but it also raises latency and may introduce distracting passages. The best setting depends on your documents, questions, retrieval method, and available context window.

- **Instruct the model to separate evidence from assumptions.** Ask it to cite the supplied passages, state when context is insufficient, and avoid presenting speculation as fact. This reduces the risk of misinterpreting retrieved evidence.

- **Attach document metadata to every fragment.** Record title, version, owner, access policy, and update time. Use this metadata to filter results (e.g., match the software version mentioned in the question) and to present meaningful citations.

- **Maintain the index independently of model training.** When a document is corrected, update or remove the corresponding indexed fragments immediately. Otherwise, retrieval will continue to surface obsolete information.

- **Enforce access control in the application layer, not just the prompt.** Authorization must happen before private passages are exposed to a user. Prompts alone are not an access-control mechanism, and cached answers must respect the user’s permissions and the freshness of the underlying documents.

- **Treat retrieved documents as untrusted data.** Prompt injection inside a document must not override system policy. Build operational safeguards around the model to prevent malicious or accidental manipulation via the corpus.

- **Ensure citations actually support the answer.** A citation is useful only if it points to the passage that underpins the claim. Merely attaching a document title or plausible URL does not establish correctness.

- **Expose conflicts instead of silently resolving them.** If two retrieved passages disagree, the system should surface the conflict rather than presenting one claim as certain. A human reviewer may need to resolve the discrepancy.

- **Evaluate retrieval and generation separately.** A correct passage can be followed by an incorrect answer, and a fluent answer can conceal a retrieval failure. Use a small, curated set of questions paired with expected evidence and acceptable answers, including straightforward, multi-passage, and unanswerable cases.

- **Score faithfulness by claim validity, not word overlap.** An answer should not receive a high faithfulness score merely because it repeats words from the context. Verify that its main claims follow from the supplied passages and that important qualifications are preserved.

- **Monitor production metrics closely.** Track latency, retrieval precision, token usage, and failure rates. Cache repeated queries to reduce latency, but ensure logs used for evaluation do not disclose confidential documents or credentials.
```

### Б.13. Kimi — task_4/direct

**Промпт:**

```text
According to the source, which similarity measure can a vector index use?
Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.

[Полный исходный текст раздела 4]
```

**Ответ:** 3.36 с; 2 слов; `stop`.

```text
 cosine similarity
```

### Б.14. Qwen — task_4/direct

**Промпт:**

```text
According to the source, which similarity measure can a vector index use?
Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.

[Полный исходный текст раздела 4]
```

**Ответ:** 0.423 с; 2 слов; `stop`.

```text
cosine similarity
```

### Б.15. Qwen — task_4/inference

**Промпт:**

```text
Why can RAG improve inspectability while not guaranteeing truth?
Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.

[Полный исходный текст раздела 4]
```

**Ответ:** 1.593 с; 126 слов; `stop`.

```text
RAG improves inspectability because it makes the evidence used to generate an answer explicit: the retrieved passages are inserted into the prompt as evidence, allowing humans to verify whether the answer is supported by the provided context. This transparency enables inspection of retrieval (e.g., checking relevance and accuracy of retrieved fragments) and generation (e.g., assessing whether the model correctly uses or misinterprets the evidence). However, RAG does not guarantee truth because retrieval may return irrelevant, incomplete, or outdated passages; the model may misinterpret or hallucinate despite the evidence; and conflicting or erroneous information in the corpus may be faithfully cited. Truth depends on the quality and correctness of the retrieved documents and the model’s faithful reasoning from them—not on the RAG architecture itself.
```

### Б.16. Kimi — task_4/inference

**Промпт:**

```text
Why can RAG improve inspectability while not guaranteeing truth?
Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.

[Полный исходный текст раздела 4]
```

**Ответ:** 4.129 с; 51 слов; `stop`.

```text
 RAG improves inspectability because it inserts selected passages into the prompt as evidence, which reduces dependence on the model's parametric memory and makes an answer easier to inspect. It does not guarantee truth because retrieval may return irrelevant passages, the context may be incomplete, and the model may misinterpret the evidence.
```

### Б.17. Kimi — task_4/unavailable

**Промпт:**

```text
According to the source, who invented RAG and in what year?
Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.

[Полный исходный текст раздела 4]
```

**Ответ:** 2.179 с; 4 слов; `stop`.

```text
 The information is unavailable.
```

### Б.18. Qwen — task_4/unavailable

**Промпт:**

```text
According to the source, who invented RAG and in what year?
Answer only from the source. If the source does not contain the answer, reply exactly: The information is unavailable.

[Полный исходный текст раздела 4]
```

**Ответ:** 0.389 с; 4 слов; `stop`.

```text
The information is unavailable.
```

### Б.19. Qwen — task_5/plain_text

**Промпт:**

```text
Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below. Return one paragraph covering all four aspects.

[Полный исходный текст раздела 4]
```

**Ответ:** 2.291 с; 195 слов; `stop`.

```text
The purpose of RAG is to enhance language model responses by grounding them in external, non-parametric evidence from a document collection, thereby reducing reliance on the model’s internal memory and making answers more inspectable and traceable. The retrieval process involves loading and chunking documents (often with overlap), indexing fragments via keyword or vector-based similarity (e.g., cosine), and returning the top-*k* most relevant passages to be injected into the prompt as context. Reliability limitations include no guarantee of truth—retrieval may yield irrelevant or incomplete passages, the model may misinterpret evidence, and conflicting or outdated fragments can lead to erroneous conclusions; thus, systems must require the model to cite passages, separate evidence from assumptions, and flag insufficient context, while evaluation must assess both answer quality and faithfulness to the retrieved evidence. Security requirements mandate strict access controls to prevent unauthorized exposure of private documents, ensure prompt injection within documents cannot override system policies, enforce authorization before exposing passages to users, and safeguard logs and cached responses to avoid leaking confidential data or credentials—underscoring that RAG is an application architecture requiring robust data management, retrieval, generation, and evaluation, not a standalone guarantee of accuracy.
```

### Б.20. Kimi — task_5/plain_text

**Промпт:**

```text
Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below. Return one paragraph covering all four aspects.

[Полный исходный текст раздела 4]
```

**Ответ:** 24.162 с; 208 слов; `stop`.

```text
 Retrieval-augmented generation (RAG) combines a language model with an external collection of documents to reduce dependence on parametric memory and make answers easier to inspect, using a retriever to search for related passages before answering and inserting the selected passages into the prompt as evidence. The retrieval process follows a pipeline of document loading, chunking long documents into smaller fragments—often with overlap to preserve continuity—and indexing those fragments, whether through transparent keyword indexes or vector indexes that compare embeddings by similarity measures such as cosine similarity, after which the retriever returns the top-k fragments with configurable chunk size, overlap, and k values that trade off coverage against latency and distraction. RAG does not guarantee truth, since retrieval may return irrelevant or obsolete passages if indexes are not updated, the context may be incomplete or contain disagreeing passages, and the model may misinterpret the evidence or produce an incorrect answer even when retrieval succeeds. Security requires access controls enforced by the application—not prompts alone—when corpora contain private information, treatment of retrieved documents as untrusted data so that prompt injection cannot override system policy, and safeguards ensuring that logs avoid disclosing confidential material while cached answers respect user access permissions and the freshness of underlying documents.
```

### Б.21. Kimi — task_5/list

**Промпт:**

```text
Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below. Return exactly four bullet points, one per aspect in the given order.

[Полный исходный текст раздела 4]
```

**Ответ:** 35.522 с; 290 слов; `stop`.

```text
 - **Purpose:** RAG combines a language model with an external collection of documents so that, before answering, a retriever searches the collection for passages related to the user’s question and inserts the selected passages into the prompt as evidence, thereby reducing dependence on the model’s parametric memory and making an answer easier to inspect.
- **Retrieval process:** A typical pipeline includes document loading, chunking, indexing, retrieval, and generation: chunking divides long documents into smaller fragments often with overlap; an index stores a representation of each fragment, using either a transparent keyword index or a vector index that compares embeddings by a similarity measure such as cosine similarity; a retriever returns the top-k fragments, where k is configurable; and metadata such as version, owner, access policy, and update time can remain attached to each fragment to help the application filter results.
- **Reliability limitations:** RAG does not guarantee truth because retrieval may return irrelevant passages, the context may be incomplete, the model may misinterpret the evidence, and if the index is not updated after corrections the system may continue to surface obsolete information; very small fragments can separate an instruction from the condition that makes it valid, increasing k can introduce distracting passages, and if two retrieved passages disagree the system should expose the conflict instead of silently presenting one claim as certain.
- **Security requirements:** Operational safeguards must surround the model, requiring application-level access controls and authorization before private passages are exposed to a user (since prompts alone are not an access-control mechanism), ensuring that prompt injection inside an untrusted retrieved document cannot override the system policy, and making sure that cached answers respect the user’s access permissions and the freshness of the underlying documents while evaluation logs avoid disclosing confidential documents or credentials.
```

### Б.22. Qwen — task_5/list

**Промпт:**

```text
Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below. Return exactly four bullet points, one per aspect in the given order.

[Полный исходный текст раздела 4]
```

**Ответ:** 1.897 с; 142 слов; `stop`.

```text
- **Purpose**: RAG combines a language model with an external document collection to reduce reliance on the model’s parametric memory, making answers easier to inspect by grounding responses in retrieved evidence.  
- **Retrieval process**: A retriever searches the document collection for passages related to the user’s question, using indexing (e.g., keyword or vector-based) on chunked fragments—often with overlap—and returns the top-k most relevant fragments, where k is configurable.  
- **Reliability limitations**: RAG does not guarantee truth; retrieval may yield irrelevant or incomplete passages, the model may misinterpret evidence, and applications must prompt the model to cite passages, separate evidence from assumptions, and disclose insufficient context.  
- **Security requirements**: Operational safeguards include enforcing access controls before exposing private passages, ensuring prompt injection within documents cannot override system policy, protecting logs from confidential data exposure, and respecting user permissions and document freshness in cached answers.
```

### Б.23. Qwen — task_5/json

**Промпт:**

```text
Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below. Return valid JSON only, with exactly four string keys: "purpose", "retrieval", "limitations", and "security". No Markdown fences or extra text.

[Полный исходный текст раздела 4]
```

**Ответ:** 2.117 с; 155 слов; `stop`.

```text
{
  "purpose": "To reduce dependence on the model's parametric memory by inserting retrieved passages as evidence into the prompt, making answers easier to inspect and enabling answers that reference specific external documents.",
  "retrieval": "A retriever searches an indexed collection of document fragments—created via loading, chunking (with configurable size and overlap), and indexing (using keyword or vector methods)—and returns the top-k most relevant fragments based on similarity or keyword matching, where k is configurable.",
  "limitations": "RAG does not guarantee truth; retrieval may return irrelevant or incomplete passages, the model may misinterpret evidence, and answers can be incorrect despite fluency; evaluation must measure adherence to retrieved context and inspect retrieval and generation separately.",
  "security": "Access controls must be enforced by the application before exposing private passages, retrieved documents are untrusted data (prompt injection inside documents must not override system policy), logs must avoid disclosing confidential information, and cached answers must respect user permissions and document freshness."
}
```

### Б.24. Kimi — task_5/json

**Промпт:**

```text
Describe exactly these four aspects of RAG: purpose, retrieval process, reliability limitations, and security requirements. Keep the same scope for all four aspects and use only the source below. Return valid JSON only, with exactly four string keys: "purpose", "retrieval", "limitations", and "security". No Markdown fences or extra text.

[Полный исходный текст раздела 4]
```

**Ответ:** 32.264 с; 478 слов; `stop`.

```text
 {"purpose":"Retrieval-augmented generation combines a language model with an external collection of documents so that, before answering, a retriever searches the collection for passages related to the user's question and inserts the selected passages into the prompt as evidence. This reduces dependence on the model's parametric memory, makes an answer easier to inspect, and makes RAG an application architecture involving data management, retrieval, generation, and evaluation rather than a guarantee of accurate answers from a language model.","retrieval":"The process typically includes document loading, chunking, indexing, retrieval, and generation. Chunking divides long documents into smaller fragments, often with overlap, and an index stores a representation of each fragment, using either a transparent keyword index or a vector index that compares embeddings by a similarity measure such as cosine similarity. A retriever returns the top-k fragments, where k is configurable, and keeping metadata such as title, version, owner, access policy, and update time attached to each fragment helps the application filter results and present meaningful citations. Chunk size and overlap are design choices that should be evaluated on representative questions, and increasing k may improve coverage while increasing latency and introducing distracting passages. When a document is corrected, the application should update or remove the corresponding indexed fragments so retrieval does not continue to surface obsolete information.","limitations":"RAG does not guarantee truth. Retrieval may return irrelevant passages, the context may be incomplete, and the model may misinterpret the evidence. A passage describing an older release may be relevant to the topic but wrong for the requested version, and failure to maintain the index can cause retrieval to surface obsolete information. A citation is useful only if it points to the passage that actually supports the answer, and merely attaching a document title or a plausible URL does not establish correctness. If two retrieved passages disagree, the system should expose the conflict instead of silently presenting one claim as certain. Evaluation should inspect retrieval and generation separately, because a correct passage can be followed by an incorrect answer and a fluent answer can conceal a retrieval failure. An answer should not receive a high faithfulness score merely because it repeats words from the context; review whether its main claims follow from the supplied passages and whether important qualifications have been preserved.","security":"Access controls are needed when a corpus contains private information, and authorization should be enforced by the application before private passages are exposed to a user because prompts alone are not an access-control mechanism. Retrieved documents are untrusted data, so prompt injection inside a document must not override the system policy. Production teams should monitor latency, retrieval precision, token usage, and failure rates, and caching repeated queries can reduce latency. Logs used for evaluation should avoid disclosing confidential documents or credentials, and cached answers must respect the user's access permissions and the freshness of the underlying documents."}
```

### Б.25. Kimi — task_6/fact_probe

**Промпт:**

```text
Write six concise, numbered, verifiable factual claims about RAG. Across the claims include publication dates, numbers, technology names, author names, exact document titles, and URLs. Include at least three claims about named research papers or documented tools, with a primary source URL for each. Label every claim either SUPPORTED BY THE SUPPLIED TEXT or EXTERNAL TO THE SUPPLIED TEXT. External knowledge is allowed, but say when you are uncertain; do not invent references or present illustrative numerical settings as universal defaults. Keep the answer within 450 words. The supplied text is:

[Полный исходный текст раздела 4]
```

**Ответ:** 63.978 с; 193 слов; `stop`.

```text
 1. Lewis et al. introduced retrieval-augmented generation in the 2020 NeurIPS paper *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (https://arxiv.org/abs/2005.11401). EXTERNAL TO THE SUPPLIED TEXT.

2. Gao et al. published the 2023 survey *Retrieval-Augmented Generation for Large Language Models: A Survey* (https://arxiv.org/abs/2312.10997). EXTERNAL TO THE SUPPLIED TEXT.

3. Asai et al. proposed the Self-RAG architecture in the 2023 paper *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection* (https://arxiv.org/abs/2310.11511). EXTERNAL TO THE SUPPLIED TEXT.

4. A typical RAG pipeline includes five stages—document loading, chunking, indexing, retrieval, and generation—and chunking often uses overlapping fragments to preserve continuity near boundaries. SUPPORTED BY THE SUPPLIED TEXT.

5. A vector index compares fragment embeddings by cosine similarity, while a retriever returns a configurable top-k set of fragments that can surface obsolete information if index maintenance lags behind document corrections. SUPPORTED BY THE SUPPLIED TEXT.

6. Retrieved documents are untrusted data, so prompt injection inside a document must not override system policy, and applications should require the model to separate evidence from assumptions and cite supplied passages. SUPPORTED BY THE SUPPLIED TEXT.
```

### Б.26. Qwen — task_6/fact_probe

**Промпт:**

```text
Write six concise, numbered, verifiable factual claims about RAG. Across the claims include publication dates, numbers, technology names, author names, exact document titles, and URLs. Include at least three claims about named research papers or documented tools, with a primary source URL for each. Label every claim either SUPPORTED BY THE SUPPLIED TEXT or EXTERNAL TO THE SUPPLIED TEXT. External knowledge is allowed, but say when you are uncertain; do not invent references or present illustrative numerical settings as universal defaults. Keep the answer within 450 words. The supplied text is:

[Полный исходный текст раздела 4]
```

**Ответ:** 4.282 с; 230 слов; `stop`.

```text
1. RAG combines a language model with an external document collection, using a retriever to fetch relevant passages before generation, reducing reliance on parametric memory.  
**SUPPORTED BY THE SUPPLIED TEXT**

2. A typical RAG pipeline includes document loading, chunking, indexing, retrieval, and generation stages, where chunking often uses overlap to preserve continuity.  
**SUPPORTED BY THE SUPPLIED TEXT**

3. The paper “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks” (Lewis et al., 2020) introduced RAG, with the model architecture and experiments detailed in the ACL Anthology.  
**EXTERNAL TO THE SUPPLIED TEXT**  
*Source: Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. arXiv:2005.11401v4. https://arxiv.org/abs/2005.11401*

4. The RAG repository and implementation (Hugging Face Transformers) provides code for RAG-Token and RAG-Sequences models, released under Apache 2.0 license.  
**EXTERNAL TO THE SUPPLIED TEXT**  
*Source: Hugging Face. (2020). RAG: Retrieval-Augmented Generation. https://github.com/huggingface/transformers/tree/main/examples/research_projects/rag*

5. The paper “RAGAS: Automated Evaluation of Retrieval-Augmented Generation” (Pawar et al., 2023) proposes metrics for faithfulness, answer relevance, and context precision.  
**EXTERNAL TO THE SUPPLIED TEXT**  
*Source: Pawar, S., et al. (2023). RAGAS: Automated Evaluation of Retrieval-Augmented Generation. arXiv:2309.15217. https://arxiv.org/abs/2309.15217*

6. Document metadata in RAG systems may include title, version, owner, access policy, and update time to support filtering, citation, and freshness enforcement.  
**SUPPORTED BY THE SUPPLIED TEXT**
```
