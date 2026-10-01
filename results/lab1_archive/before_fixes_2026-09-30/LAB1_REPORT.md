# Отчёт по лабораторной работе №1

## 1. Титульный лист

**Университет ИТМО**  
**Дисциплина:** Промпт-инжиниринг  
**Тема:** Подключение к LLM через API Cloud.ru, базовые запросы и первичный поиск галлюцинаций  
**Студент:** ____________________  
**Группа:** ____________________  
**Дата эксперимента:** 26 сентября 2026 г. — по сохранённому `manifest.json`  
**Дата подготовки отчёта и проверки источников:** 30 сентября 2026 г.  
**Санкт-Петербург, 2026**

## 2. Цель работы

Освоить подключение к большим языковым моделям через OpenAI-совместимый API Cloud.ru, сравнить ответы двух моделей на одинаковые запросы, исследовать влияние формулировок и формата ответа, проверить работу с ограниченным контекстом и выявить неподтверждённые утверждения путём сопоставления с первичными источниками.

## 3. Использованные модели и условия эксперимента

В работе использованы `moonshotai/Kimi-K2.6` (далее Kimi) и `Qwen/Qwen3-Coder-Next` (далее Qwen). Обе модели присутствуют в сохранённом списке Cloud.ru и успешно прошли тест подключения. Выбор позволяет сравнить две разные модели на одном техническом материале; выводы относятся к этим идентификаторам и настройкам.

Подключение выполнено через `https://foundation-models.api.cloud.ru/v1` с помощью Python SDK `openai`. Ключ читается из переменной `API_KEY` или файла `.env`. В `requirements.txt` указаны `openai>=1.50.0`, `python-dotenv>=1.0.0`, `requests>=2.31.0`. Точные установленные версии библиотек на момент исходного запуска не сохранены. При подготовке отчёта локально доступен Python 3.13.1; это не отдельное доказательство версии интерпретатора исходного запуска.

Источником результатов служит каталог `results/lab1/`: в его манифесте указано **95 доступных идентификаторов**, 26 основных ответов и две проверки подключения. Полный список приведён в приложении А. Идентификаторы воспроизведены из сохранённого ответа API; наличие в списке не означает, что для каждого из них проверена генерация текста.

Отдельный файл `results/lab1_environment.json` содержит другой снимок списка из 98 идентификаторов и неуспешные тесты с ошибкой ключа. Он не объединяется с основным запуском: отчёт опирается на согласованные файлы внутри `results/lab1/`.

### Параметры и ограничения сравнения

| Условие | Kimi | Qwen |
| --- | --- | --- |
| Основные промпты | Одинаковые для обеих моделей | Одинаковые для обеих моделей |
| Температура основных запросов | 0,2 | 0,2 |
| Температура проверки подключения | 0,0 | 0,0 |
| `max_tokens`, задания 2–5 | 4096 | 256 |
| `max_tokens`, задание 6 | 8192 | 512 |
| `max_tokens`, проверка подключения | 4096 | 256 |
| Потоковая выдача | `stream=False` | `stream=False` |
| Дополнительный параметр | `thinking: {type: disabled}` | Не задаётся |
| Повторы каждого основного запроса | Один сохранённый ответ | Один сохранённый ответ |

Параметры восстановлены по текущему `lab1/runner.py`: манифест не содержит полного снимка конфигурации или версии кода исходного запуска. Значение `LAB_MAX_TOKENS` из общего конфига в этом runner не определяет бюджет запросов: для заданий передаются конкретные значения. Несмотря на запрос отключения thinking, у Kimi сохранена ненулевая длина поля reasoning; нельзя считать доказанным, что сервер полностью отключил внутренние рассуждения.

Бюджеты токенов различаются, поэтому полнота и время ответа зависят не только от модели. Для строгого сравнения потребовались бы достаточные сопоставимые бюджеты, несколько повторов и сохранение фактического расхода токенов. В этом отчёте оценивается имеющийся запуск, без приписывания ему дополнительных экспериментов.

## 4. Исходный текст для экспериментов

Использован учебный текст **Retrieval-Augmented Generation in Production Systems** из `lab1/source_text.py`. Он включает механизм RAG, этапы конвейера, ограничения, оценку и безопасность. В нём есть ответ на прямой вопрос о мере сходства и материал для смыслового вывода, но отсутствуют автор и дата появления RAG.

Текст содержит **215 слов при разбиении по пробелам**. Это короткий материал, который может не соответствовать требуемым 1–2 страницам при обычном оформлении. В отчёте приведён именно исходный текст фактического эксперимента; его расширение задним числом сделало бы описание результатов недостоверным. Промпты и ответы сохранены на английском, аналитическая часть отчёта написана на русском.

### Полный исходный текст

Retrieval-augmented generation (RAG) combines a language model with an external collection of documents. Before answering, a retriever searches that collection for passages related to the user's question. The selected passages are inserted into the prompt as evidence. This reduces dependence on the model's parametric memory and makes an answer easier to inspect.

A typical RAG pipeline includes document loading, chunking, indexing, retrieval, and generation. Chunking divides long documents into smaller fragments, often with overlap. An index stores a representation of each fragment. A keyword index is transparent and easy to debug, while a vector index compares embeddings by a similarity measure such as cosine similarity. A retriever returns the top-k fragments, where k is a configurable number.

RAG does not guarantee truth. Retrieval may return irrelevant passages, the context may be incomplete, and the model may misinterpret the evidence. Applications should ask the model to separate evidence from assumptions, cite the supplied passages, and state when the context is insufficient. Evaluation should measure both answer quality and adherence to the retrieved context.

Production teams monitor latency, retrieval precision, token usage, and failure rates. Caching repeated queries can reduce latency. Access controls are needed when a corpus contains private information. Retrieved documents are untrusted data: prompt injection inside a document must not override the system policy.

## 5. Ход выполнения работы

### 5.1. Подготовка среды и подключение

Для установки зависимостей и запуска предусмотрены команды:

```powershell
python -m pip install -r requirements.txt
python -m lab1.runner
```

Следующий фрагмент использует реальные функции проекта и показывает получение списка и тестовый запрос к обеим моделям:

```python
from labs.common import load_config, make_client, list_models
from lab1.runner import call

config = load_config()
client = make_client(config)
available_models = list_models(client)
print(available_models)

for model in config.models:
    result = call(
        client, model, "task_1", "connection_check",
        "Reply with exactly: connection verified.",
        max_tokens=256, temperature=0.0,
    )
    print(model, repr(result.output), result.latency_seconds)
```

Внутри `call()` используется `client.chat.completions.create()` с одним сообщением роли `user`. Время измеряется как разность `time.time()` до и после запроса. В CSV записываются промпт, ответ, время, причина завершения, ошибка и текстовые метрики. Это полное клиентское время ожидания, а не время до первого токена и не чистое время вычислений модели.

| Модель | Сохранённый ответ (`repr`) | Время, с | Завершение |
| --- | --- | --- | --- |
| Kimi | `' connection verified.'` | 0,779 | `stop` |
| Qwen | `'connection verified.'` | 0,260 | `stop` |

Оба запроса подтвердили подключение. При посимвольной проверке Qwen выполнила инструкцию точнее: у Kimi есть начальный пробел.

### 5.2. Первый одинаковый запрос

> Explain the concept of retrieval-augmented generation to a second-year software engineering student in 120 words or fewer. Include one practical example.

Kimi дала определение RAG и пример студенческого чат-бота, получающего актуальные сроки из учебного календаря. Ответ понятен, содержит 87 единиц словесного счётчика и укладывается в лимит. Недостаток — слишком оптимистичное описание получения точного ответа: наличие поиска само по себе точность не гарантирует.

Qwen дополнила определение схемой из четырёх шагов и примером Stripe. Объяснение механизма полнее, но длиннее: 134 единицы счётчика при лимите 120. При простом разбиении по пробелам получается 122 элемента, включая обозначения шагов; точный подсчёт естественных слов зависит от правила. Числовой пример Stripe требует оговорок и внешней проверки, которой в самом ответе нет.

Для заданного краткого учебного объяснения предпочтительнее ответ Kimi: он компактнее и не вводит конкретный внешний лимит API. Полные ответы обеих моделей приведены в приложении Б.

### 5.3. Пять формулировок суммаризации

К каждой инструкции добавлялись `Use only the source below.` и полный текст раздела 4.

| Вариант | Инструкция | Kimi, слов | Qwen, слов | Сравнение |
| --- | --- | --- | --- | --- |
| summary | Summarize the source in no more than 80 words. | 75 | 100 | Kimi укладывается в 80 слов и сохраняет главное; Qwen сохраняет больше деталей, но превышает лимит. |
| main_points | Extract the five main points from the source. | 203 | 168 | Обе дают пять пунктов. Kimi подробнее, Qwen компактнее; у Qwen перекрытие фрагментов описано без often. |
| short_recap | Briefly retell the source for a busy engineer. | 158 | 126 | Kimi выбирает пять тематических блоков; Qwen — абзац для инженера. Обе сохраняют риски, оценку и эксплуатацию. |
| outline | Create a concise hierarchical outline of the source. | 195 | 141 | Kimi даёт полный план из пяти разделов; Qwen обрывается на начале третьего раздела из-за лимита токенов. |
| takeaways | List the most useful practical takeaways from the source. | 190 | 181 | Обе дают практические списки. Kimi местами усиливает исходные рекомендации; Qwen добавляет объяснение пользы chunking и достигает лимита. |

Числовое ограничение `no more than 80 words` дало самый короткий результат у обеих моделей: 75 и 100 слов соответственно. Для Kimi это наиболее удачная формулировка краткого резюме. Если важнее охват содержания и удобство сравнения, лучше работает `Extract the five main points`: обе модели дали пять законченных смысловых блоков.

`Briefly` и `concise` без числовой границы не обеспечили одинаковую краткость. `Hierarchical outline` привёл к вложенной структуре, которая у Qwen потребовала больше доступного бюджета. `Practical takeaways` сместил ответ от описания к рекомендациям: например, осторожное указание на возможное перекрытие превратилось у Kimi в заголовок `Chunk with overlap`.

Сравнение не изолирует влияние одного слова: промпты одновременно меняют объём, структуру и аудиторию. Поэтому вывод относится к полным формулировкам, а не к причинному эффекту отдельного глагола.

### 5.4. Вопросы по ограниченному контексту

После каждого вопроса добавлялась общая инструкция:

> Answer only from the source. If the source does not contain the answer, say exactly that the information is unavailable.

Далее передавался полный исходный текст.

| Тип | Вопрос | Kimi | Qwen |
| --- | --- | --- | --- |
| Прямой | According to the source, which similarity measure can a vector index use? | `cosine similarity` | `cosine similarity` |
| Смысловой | Why can RAG improve inspectability while not guaranteeing truth? | Указаны свидетельства в промпте и три причины ошибок: нерелевантный поиск, неполный контекст, неверная интерпретация. | Основной смысл тот же; добавлена фраза о reasoning, скрытом в весах, которой нет в исходном тексте. |
| Отсутствующий ответ | According to the source, who invented RAG and in what year? | `The information is unavailable.` | `The information is unavailable.` |

Обе модели корректно удержали границу знания в третьем вопросе: даже наличие возможных внешних знаний об авторах не привело к ответу вне контекста. На смысловом вопросе Kimi точнее придерживалась формулировок источника. Один успешный отказ не доказывает, что модель всегда будет признавать нехватку информации.

### 5.5. Форматы ответа

К каждой инструкции также добавлялись `Use only the source below.` и исходный текст.

| Формат | Инструкция | Наблюдение |
| --- | --- | --- |
| Обычный текст | Explain the main purpose of RAG in one paragraph. | Обе модели дали один абзац. У Qwen он состоит из длинной фразы и содержит дополнительные обобщения. |
| Список | Explain the main purpose of RAG as exactly four bullet points. | Обе дали ровно четыре пункта; Qwen включила также оценку и безопасность. |
| JSON | Return valid JSON only with exactly two keys: "purpose" (string) and "limitations" (array of strings). | Оба ответа успешно разбираются `json.loads`; ровно два требуемых ключа и правильные типы, внешнего текста и Markdown-ограждений нет. |

Начальный пробел в JSON Kimi не мешает разбору. Kimi перечислила четыре ограничения, Qwen — пять, включив prompt injection. Основной смысл назначения сохранён в обоих JSON. По соблюдению трёх форматов результат равный; JSON Qwen дополнительно удобен для чтения из-за отступов. Список удобнее для быстрого просмотра, JSON — для программного анализа.

Форматы сравниваются не при полностью одинаковом содержании: JSON явно запрашивает ещё и ограничения, тогда как абзац и список — назначение RAG. Разницу длины нельзя приписывать только синтаксису формата.

### 5.6. Запрос с большим числом проверяемых фактов

> Write a fact-heavy technical answer about RAG. Include at least three dates, numbers, technology names, author names, document titles, and URLs. Clearly label each claim as either supported by the supplied source or not supported by it. The supplied source is:

После этой инструкции передавался исходный текст. В отличие от заданий 3–5 здесь разрешено добавлять сведения вне источника при явной маркировке. Поэтому сама метка `Not supported by the supplied source` не означает ложность: утверждение может подтверждаться внешней публикацией.

Kimi дала завершённый ответ объёмом 533 слова с тремя URL, отделяя исходный текст от внешних сведений. Qwen дала 291 слово и один URL; ответ оборвался в пятом пункте. Вступительное обещание Qwen включить нужное число фактов не является свидетельством выполнения инструкции. Проверка выбранных утверждений приведена в разделе 8.

### 5.7. Оценка качества

Каждый из 26 основных ответов оценён по шести критериям: точность, полнота, ясность, следование инструкции, структура и проверяемость. Это аналитическая оценка сохранённого текста, а не автоматический результат модели и не независимый экспертный бенчмарк.

Шкала: **5** — критерий выполнен без существенных замечаний; **4** — небольшая неточность, лишнее обобщение или неудобство; **3** — заметная проблема, но ответ полезен; **2** — существенная часть задачи не выполнена; **1** — ответ непригоден по критерию. Для полноты учитывается объём, запрошенный конкретным промптом: короткий правильный отказ может получить 5. При обрыве оцениваются отдельно корректность сохранившихся фактов и неполнота ответа.

## 6. Таблица результатов

Обозначения промптов соответствуют разделу 5 и коду runner. Длина в словах рассчитана регулярным выражением `\b\w+\b`, длина в символах — `len(output)`, включая пробелы и переводы строк. Полные ответы приведены в приложении Б; CSV содержит полные промпты вместе с исходным текстом.

| Модель | Задание / промпт | Время, с | Символов | Слов | Завершение |
| --- | --- | --- | --- | --- | --- |
| Kimi | task_2 / identical_explanation | 7.949 | 606 | 87 | stop |
| Qwen | task_2 / identical_explanation | 2.0 | 859 | 134 | stop |
| Kimi | task_3 / summary | 10.509 | 560 | 75 | stop |
| Kimi | task_3 / main_points | 10.544 | 1457 | 203 | stop |
| Kimi | task_3 / short_recap | 8.917 | 1158 | 158 | stop |
| Kimi | task_3 / outline | 11.648 | 1604 | 195 | stop |
| Kimi | task_3 / takeaways | 9.614 | 1396 | 190 | stop |
| Qwen | task_3 / summary | 1.397 | 752 | 100 | stop |
| Qwen | task_3 / main_points | 2.227 | 1277 | 168 | stop |
| Qwen | task_3 / short_recap | 1.797 | 898 | 126 | stop |
| Qwen | task_3 / outline | 2.464 | 1091 | 141 | length |
| Qwen | task_3 / takeaways | 2.73 | 1382 | 181 | length |
| Kimi | task_4 / direct | 2.341 | 18 | 2 | stop |
| Kimi | task_4 / inference | 3.092 | 341 | 51 | stop |
| Kimi | task_4 / unavailable | 1.575 | 32 | 4 | stop |
| Qwen | task_4 / direct | 0.38 | 17 | 2 | stop |
| Qwen | task_4 / inference | 1.002 | 440 | 64 | stop |
| Qwen | task_4 / unavailable | 0.4 | 31 | 4 | stop |
| Kimi | task_5 / plain_text | 4.729 | 409 | 67 | stop |
| Kimi | task_5 / list | 24.4 | 308 | 47 | stop |
| Kimi | task_5 / json | 13.943 | 542 | 77 | stop |
| Qwen | task_5 / plain_text | 1.029 | 519 | 73 | stop |
| Qwen | task_5 / list | 0.958 | 474 | 64 | stop |
| Qwen | task_5 / json | 1.193 | 542 | 72 | stop |
| Kimi | task_6 / fact_probe | 77.897 | 3752 | 533 | stop |
| Qwen | task_6 / fact_probe | 4.596 | 2093 | 291 | length |

### Сводные показатели

| Модель | Ответов | Среднее время, с | Медиана, с | Средняя длина, слов | Завершение length |
| --- | --- | --- | --- | --- | --- |
| Kimi | 13 | 14.397 | 9.614 | 129.9 | 0 |
| Qwen | 13 | 1.706 | 1.397 | 109.2 | 3 |

Qwen была быстрее на всех 13 парных основных запросах. Среднее время Kimi заметно увеличивает запрос с фактами (77,897 с); поэтому приведена также медиана. Ошибок API в 26 основных строках нет, но `finish_reason=length` встречается у Qwen в `outline`, `takeaways` и `fact_probe`. У `takeaways` последний пункт выглядит законченным; нельзя утверждать, что текст обязательно обрывается посреди фразы. У `outline` и `fact_probe` обрыв виден непосредственно.

### Дополнительные метрики

| Модель | Промпт | Числовых совпадений | Годов | URL | Маркеров осторожности | Маркеров уверенности |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi | task_2 / identical_explanation | 0 | 0 | 0 | 0 | 0 |
| Qwen | task_2 / identical_explanation | 9 | 0 | 0 | 0 | 0 |
| Kimi | task_4 / unavailable | 0 | 0 | 0 | 0 | 0 |
| Qwen | task_4 / unavailable | 0 | 0 | 0 | 0 | 0 |
| Kimi | task_6 / fact_probe | 11 | 5 | 3 | 0 | 0 |
| Qwen | task_6 / fact_probe | 15 | 6 | 1 | 0 | 0 |

Во всех 26 ответах оба счётчика языковых маркеров равны нулю. Это ограничение словаря, а не отсутствие осторожности: правильная фраза `The information is unavailable.` в словарь не включена. Аналогично, номера пунктов и фрагменты URL увеличивают счётчик чисел, а счётчик годов отражает вхождения, не число уникальных дат. Метрики длины, ссылок и маркеров сами по себе не доказывают качество ответа.

## 7. Анализ качества ответов

В таблице: Т — точность, П — полнота, Я — ясность, И — следование инструкции, С — структура, В — проверяемость. Точность здесь относится к проверенному содержанию; для фактически насыщенных ответов не заявляется проверка каждого предложения.

| Модель | Промпт | Т | П | Я | И | С | В | Комментарий |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi | task_2 / identical_explanation | 4 | 5 | 5 | 5 | 5 | 4 | Понятное объяснение и учебный пример; точность ответа RAG описана несколько оптимистично. |
| Qwen | task_2 / identical_explanation | 3 | 5 | 4 | 3 | 4 | 3 | Полезная схема; 134 единицы счётчика при лимите 120; конкретный лимит Stripe дан без условий и источника. |
| Kimi | task_3 / summary | 5 | 4 | 5 | 5 | 5 | 5 | 75 слов при лимите 80; сохранены механизм, этапы, ограничения и безопасность; опущена часть рекомендаций по оценке. |
| Kimi | task_3 / main_points | 5 | 5 | 5 | 5 | 5 | 5 | Ровно пять пунктов; охвачены все основные блоки исходного текста. |
| Kimi | task_3 / short_recap | 5 | 5 | 5 | 4 | 5 | 5 | Корректный структурированный пересказ; 158 слов для busy engineer всё ещё довольно много. |
| Kimi | task_3 / outline | 5 | 5 | 5 | 4 | 5 | 5 | Полная иерархия, но 195 слов слабо соответствуют требованию concise. |
| Kimi | task_3 / takeaways | 4 | 5 | 5 | 4 | 5 | 4 | Практический список; часто используемое перекрытие превращено в директиву, а возможный эффект кеша — в безусловный. |
| Qwen | task_3 / summary | 5 | 5 | 5 | 3 | 5 | 5 | Смысл сохранён, но 100 слов превышают ограничение 80. |
| Qwen | task_3 / main_points | 4 | 5 | 5 | 5 | 5 | 5 | Пять содержательных пунктов; перекрытие фрагментов представлено без оговорки often. |
| Qwen | task_3 / short_recap | 5 | 5 | 5 | 5 | 5 | 5 | Компактный пересказ с ограничениями и эксплуатационными требованиями. |
| Qwen | task_3 / outline | 5 | 2 | 3 | 2 | 2 | 5 | finish_reason=length; ответ обрывается на разделе III, отсутствуют ограничения и эксплуатация. |
| Qwen | task_3 / takeaways | 4 | 5 | 5 | 4 | 5 | 4 | Основные блоки сохранены; добавлено объяснение пользы chunking; достигнут лимит, хотя последний пункт выглядит законченным. |
| Kimi | task_4 / direct | 5 | 5 | 5 | 5 | 5 | 5 | Краткий прямой ответ cosine similarity совпадает с исходным текстом. |
| Kimi | task_4 / inference | 5 | 5 | 5 | 5 | 5 | 5 | Объяснены проверяемость и все три причины возможной ошибки. |
| Kimi | task_4 / unavailable | 5 | 5 | 5 | 5 | 5 | 5 | Корректно сообщено об отсутствии информации; автор и год не выдуманы. |
| Qwen | task_4 / direct | 5 | 5 | 5 | 5 | 5 | 5 | Точный прямой ответ по тексту. |
| Qwen | task_4 / inference | 4 | 5 | 5 | 4 | 5 | 4 | Основной вывод верен; формулировка reasoning is hidden in weights отсутствует в источнике и упрощает понятие рассуждения. |
| Qwen | task_4 / unavailable | 5 | 5 | 5 | 5 | 5 | 5 | Корректный отказ отвечать на основании недостаточного контекста. |
| Kimi | task_5 / plain_text | 5 | 5 | 5 | 5 | 5 | 5 | Один абзац, основное назначение передано без внешних фактов. |
| Kimi | task_5 / list | 5 | 5 | 5 | 5 | 5 | 5 | Ровно четыре пункта, точно описывающие назначение и механизм. |
| Kimi | task_5 / json | 5 | 5 | 5 | 5 | 5 | 5 | Валидный JSON, два требуемых ключа и правильные типы; четыре ограничения. |
| Qwen | task_5 / plain_text | 4 | 5 | 4 | 4 | 5 | 4 | Один абзац; тяжёлая длинная фраза, расширение о reliability и accountability сверх прямой формулировки источника. |
| Qwen | task_5 / list | 5 | 5 | 5 | 5 | 5 | 5 | Ровно четыре пункта; назначение дополнено требованиями оценки и безопасности из текста. |
| Qwen | task_5 / json | 5 | 5 | 5 | 5 | 5 | 5 | Валидный JSON, нужные ключи и типы; ограничения дополнены риском prompt injection. |
| Kimi | task_6 / fact_probe | 4 | 5 | 4 | 5 | 4 | 4 | Завершённый ответ с маркировкой происхождения; проверенные публикации существуют, но типичность k=5 не обоснована. |
| Qwen | task_6 / fact_probe | 3 | 2 | 3 | 2 | 2 | 3 | Ответ обрезан в пункте 5; обещанное разнообразие фактов не достигнуто; типичность 150/50 токенов не подтверждена. |

### Итоговое сопоставление

**Точность и работа с контекстом.** В прямом вопросе и признании отсутствующей информации модели равны. В смысловом вопросе Kimi ближе к исходному тексту; Qwen добавляет собственную формулировку о весах модели. В обеих моделях встречаются усиления исходных утверждений, поэтому безоговорочного победителя по фактической истинности нет.

**Полнота.** При данных настройках Kimi полнее выполняет иерархический план и запрос с фактами. Существенную часть преимущества объясняет больший доступный бюджет. В коротком резюме Qwen охватывает больше рекомендаций, но нарушает ограничение длины.

**Следование инструкции.** Kimi лучше соблюдает числовое ограничение суммаризации и даёт завершённый ответ в задании 6. Qwen точнее выполняет посимвольный тест подключения. Вопрос с отсутствующим ответом, четыре пункта и JSON обе модели выполняют успешно.

**Формат.** Явного победителя в задании 5 нет: все шесть ответов соблюдают запрошенную структуру. JSON Qwen легче читать, JSON Kimi компактнее представлен.

**Практическое применение.** Для полного ответа по источнику в этом запуске предпочтительнее Kimi. Для быстрых коротких ответов Qwen показала хороший результат, но её бюджет и соблюдение длины требуют контроля. Это оценка конкретного запуска, а не универсальный рейтинг моделей.

## 8. Поиск галлюцинаций и проверка источников

Проверка выполнена 30.09.2026 путём сопоставления выбранных утверждений с открытыми первичными источниками. Ниже — пять утверждений Kimi из задания 6, четыре утверждения Qwen из задания 6 и дополнительный пример Qwen из задания 2. Формулировки в таблице передают проверяемый смысл; исходные ответы полностью сохранены в приложении Б.

| Модель | Утверждение | Где проверялось | Результат | Комментарий |
| --- | --- | --- | --- | --- |
| Kimi | Статья Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks связана с Patrick Lewis и NeurIPS 2020. | [Lewis et al., arXiv](https://arxiv.org/abs/2005.11401) | Подтверждено | Карточка статьи подтверждает авторов и принятие на NeurIPS 2020. Это подтверждение конкретной работы, а не доказательство первенства всей идеи поиска перед генерацией. |
| Kimi | В исходной работе индексировано около 21 000 000 документов Wikipedia. | [Lewis et al., раздел 3](https://arxiv.org/html/2005.11401v4) | Подтверждено с уточнением | В разделе 3 указаны 21 млн неперекрывающихся фрагментов по 100 слов из снимка Wikipedia за декабрь 2018 года. Их нельзя понимать как 21 млн полных статей. |
| Kimi | REALM: Retrieval-Augmented Language Model Pre-Training — работа Kelvin Guu и соавторов 2020 года. | [Guu et al., arXiv](https://arxiv.org/abs/2002.08909) | Подтверждено | Указаны Kelvin Guu и соавторы; первая версия размещена 10.02.2020. |
| Kimi | Обзор Retrieval-Augmented Generation for Large Language Models: A Survey опубликован Yunfan Gao и соавторами в декабре 2023 года. | [Gao et al., arXiv](https://arxiv.org/abs/2312.10997) | Подтверждено | Первая версия препринта датирована 18.12.2023; ссылка ведёт на нужную работу. Это дата препринта. |
| Kimi | Инженеры часто выбирают k=5 при поиске фрагментов. | [Lewis et al., раздел 3](https://arxiv.org/html/2005.11401v4) | Не подтверждена типичность | В статье исследованы k=5 и k=10 при обучении. Это подтверждает использование k=5 в эксперименте, но не частоту такого выбора в производственных системах. |
| Qwen | Работа о RAG 2020 года написана Patrick Lewis, Ethan Perez и соавторами. | [Lewis et al., arXiv](https://arxiv.org/abs/2005.11401) | Подтверждено | Имена и год совпадают с карточкой статьи; arXiv:2005.11401 существует. |
| Qwen | Препринт работы о RAG представлен в мае 2020 года. | [Lewis et al., arXiv](https://arxiv.org/abs/2005.11401) | Подтверждено | Дата первой версии — 22.05.2020. Отдельное утверждение модели о декабре как дате публикации здесь не оценивается. |
| Qwen | Векторный поиск может использовать embeddings и cosine similarity. | [Документация FAISS](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances) | Подтверждено с оговоркой | FAISS описывает поиск по косинусному сходству через нормализацию векторов и скалярное произведение. Косинусное сходство — один из вариантов, не обязательная метрика любого индекса. |
| Qwen | Фрагменты по 150 токенов с перекрытием 50 токенов распространены на практике. | [Документация LangChain](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter) | Не подтверждено | В исходном тексте чисел нет. Документация описывает настраиваемые размер и перекрытие, но не подтверждает распространённость пары 150/50. Это не доказательство невозможности такой настройки. |
| Qwen | В учебном примере Stripe обеспечивает 100 запросов/с на аккаунт «as of v2023-10-16». | [Документация Stripe](https://docs.stripe.com/rate-limits) | Частично подтверждено; привязка к версии не подтверждена | Дополнительная проверка task_2: текущая документация даёт глобальный live-лимит 100 запросов/с, но также отдельные лимиты endpoint и sandbox. Историческая привязка к версии 2023-10-16 этой страницей не подтверждается. |

### Характер обнаруженных проблем

В проверенной выборке не обнаружено вымышленной статьи или несуществующего arXiv-идентификатора. Число 21 млн у Kimi имеет основание, но требует уточнения единицы: речь о фрагментах, которые статья называет документами. Это терминологическая неоднозначность, а не доказанная выдумка.

У Kimi не подтверждена заявленная частота использования `k=5` в производственных системах. У Qwen не подтверждена распространённость параметров `150/50` токенов; дополнительный пример Stripe смешивает реальный глобальный лимит с неподтверждённой исторической привязкой и не оговаривает другие ограничения. Такие формулировки создают риск галлюцинации или ложной точности, но неподтверждённость не равна доказанной ложности.

В рассмотренных примерах Qwen содержит больше проблем с необоснованной конкретикой, особенно с учётом задания 2. Однако малая и неслучайная выборка утверждений, разная длина ответов и обрезка Qwen не позволяют вычислять частоту галлюцинаций модели в целом.

### Как изменить промпт

Для задачи строго по тексту более надёжной постановкой была бы:

> Use only the supplied text. Do not add dates, names, URLs, or numerical settings absent from it. For each factual claim, quote the supporting sentence. If the text does not contain the requested information, return "The information is unavailable." Do not describe examples as standard or common settings without evidence.

Если нужны внешние факты, следует отдельно разрешить внешние источники, потребовать ссылку для каждого конкретного числа и даты и указать, что непроверенные сведения должны быть помечены. Требование выдать заранее заданное количество фактов даже при нехватке материала лучше заменить требованием перечислить только подтверждённые. Эти изменения предложены по результатам анализа и в сохранённом запуске отдельно не проверялись.

## 9. Выводы

1. **Различия между моделями.** Kimi дала более развёрнутые и завершённые ответы в сложных заданиях; Qwen была быстрее на всех парных запросах. Сравнение полноты ограничено разными бюджетами токенов.
2. **Влияние формулировки.** Лимит 80 слов дал самые короткие резюме, пять главных пунктов — сопоставимые законченные списки, иерархический план — подробную структуру, а практические выводы — рекомендации вместо простого пересказа.
3. **Полезные инструкции.** `Use only the source`, явное указание признать отсутствие сведений, `exactly four bullet points` и требование двух конкретных ключей JSON помогли получить проверяемый результат. При этом числовой лимит слов Qwen соблюла не во всех случаях.
4. **Добавление собственных сведений.** Оно наблюдалось в примере Stripe, смысловом объяснении Qwen, практических рекомендациях и особенно в задании 6, которое прямо запрашивало внешнюю конкретику с маркировкой.
5. **Необходимость проверки.** Уверенный стиль, точное число или существующая ссылка не гарантируют, что источник подтверждает именно это утверждение. Нужно проверять смысл, единицы измерения, условия применимости и даты, а также отделять ошибку содержания от обрыва по лимиту.
6. **Надёжность в данном эксперименте.** Kimi предпочтительнее по завершённости и соблюдению краткого резюме при использованных настройках. На отсутствии ответа в контексте и на JSON обе модели справились. Для общего вывода о превосходстве одной модели этих данных недостаточно.

Практическая цель подключения, сохранения и анализа ответов достигнута. Полное соответствие формальным требованиям ограничено коротким исходным текстом и неполным фактически насыщенным ответом Qwen. Для устранения этих ограничений нужен отдельный повторный запуск с текстом требуемого объёма и достаточным бюджетом; текущие результаты таким запуском не подменяются.

### Файлы работы и воспроизводимость

| Файл | Назначение |
| --- | --- |
| `lab1/runner.py` | Отправка запросов, замеры, метрики, сохранение результатов |
| `lab1/source_text.py` | Точный исходный материал |
| `labs/common.py` | Конфигурация, подключение и запись CSV |
| `results/lab1/manifest.json` | Дата, список моделей, проверки и число ответов исходного запуска |
| `results/lab1/connection_checks.csv` | Два теста подключения |
| `results/lab1/lab1_results.csv` | 26 полных промптов и ответов с метриками |
| `results/lab1/lab1_results_with_metrics.csv` | В текущей реализации копия той же таблицы с метриками |
| `results/lab1/quality_scores.csv` | Заполненные оценки 26 ответов |
| `results/lab1/hallucination_verification.csv` | Проверенные утверждения и источники |

При подготовке отчёта новые обращения к моделям не выполнялись. Исходные CSV с ответами и манифест сохранены. Флаг `manual_verification_required=true` в манифесте относится к первоначальному созданию заготовок; заполненная проверка хранится в отдельном CSV. Повторный запуск runner перезаписывает результаты и создаёт пустые таблицы оценок и проверки, поэтому перед ним следует сохранить текущие артефакты отдельно.

## Приложение А. Доступные модели по сохранённому ответу API

Снимок от 26.09.2026, 95 идентификаторов. Список воспроизведён из `results/lab1/manifest.json`.

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

## Приложение Б. Полные ответы моделей

Ниже приведены все 26 основных ответов без исправления фактов, обрывов и форматирования внутри сохранённого текста. Кодовые блоки отделяют исходные ответы от аналитической части. Базовые инструкции воспроизведены точно; для заданий 3–6 к ним добавлялся полный текст раздела 4. Полные сообщения вместе с контекстом находятся в CSV.

### Б.1. Kimi — task_2 / identical_explanation

**Промпт:**

```text
Explain the concept of retrieval-augmented generation to a second-year software engineering student in 120 words or fewer. Include one practical example.
```

**Ответ:** 7.949 с; 606 символов; 87 слов; завершение `stop`.

```text
 Retrieval-augmented generation (RAG) grounds large language models by fetching relevant external data before generating a response. Instead of relying solely on training memory, the system queries a vector database or API to retrieve documents, then injects them into the prompt as context. This reduces hallucinations and keeps answers current without retraining the model.

**Example:** A student support chatbot indexes the latest academic calendar. When asked about add/drop deadlines, it retrieves this semester’s entry and generates an accurate, cited reply rather than hallucinating outdated dates.
```

### Б.2. Qwen — task_2 / identical_explanation

**Промпт:**

```text
Explain the concept of retrieval-augmented generation to a second-year software engineering student in 120 words or fewer. Include one practical example.
```

**Ответ:** 2.0 с; 859 символов; 134 слов; завершение `stop`.

```text
Retrieval-Augmented Generation (RAG) enhances large language models (LLMs) by dynamically fetching relevant, up-to-date information from an external knowledge source (e.g., a database or document store) *before* generating a response. Instead of relying solely on pre-trained knowledge (which can be outdated or incomplete), the LLM uses the retrieved context to produce more accurate, fact-based answers.  

**How it works**: 1) User query → 2) Retrieve top-k relevant documents → 3) Inject retrieved context into the LLM prompt → 4) Generate response grounded in that context.  

**Example**: A developer asks, *“What’s the latest API rate limit for Stripe’s v2023-10-16?”* RAG fetches Stripe’s official API docs (retrieved from a vector database), then the LLM synthesizes the answer: *“As of v2023-10-16, Stripe enforces 100 requests/second per account.”*
```

### Б.3. Kimi — task_3 / summary

**Промпт:**

```text
Summarize the source in no more than 80 words.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 10.509 с; 560 символов; 75 слов; завершение `stop`.

```text
 Retrieval-augmented generation (RAG) enhances language models by retrieving relevant passages from external documents to ground answers, reducing reliance on internal memory. A pipeline involves document loading, chunking, indexing (keyword or vector), and retrieval of top-k fragments for generation. However, RAG does not ensure truth, as retrieval can fail or evidence may be misinterpreted. Production requires monitoring latency, precision, and token usage, plus caching, access controls, and safeguards against prompt injection from untrusted documents.
```

### Б.4. Kimi — task_3 / main_points

**Промпт:**

```text
Extract the five main points from the source.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 10.544 с; 1457 символов; 203 слов; завершение `stop`.

```text
 1. **Core mechanism and purpose:** Retrieval-augmented generation combines a language model with an external document collection, using a retriever to find relevant passages that are inserted into the prompt as evidence. This reduces reliance on the model’s parametric memory and makes answers easier to inspect.

2. **Typical pipeline components:** A standard RAG pipeline includes document loading, chunking (often with overlap), indexing, retrieval, and generation. Indexes can be keyword-based (transparent, easy to debug) or vector-based (using similarity measures like cosine similarity), and retrievers return a configurable top-k set of fragments.

3. **Reliability limitations:** RAG does not guarantee truth. Retrieval can return irrelevant passages, the provided context may be incomplete, and the model may still misinterpret the evidence.

4. **Safeguards and evaluation:** Applications should instruct the model to separate evidence from assumptions, cite the supplied passages, and state when context is insufficient. Evaluation should measure both answer quality and adherence to the retrieved context.

5. **Production and security considerations:** Production teams must monitor latency, retrieval precision, token usage, and failure rates; use caching to reduce latency; enforce access controls for private corpora; and treat retrieved documents as untrusted data so that prompt injection within a document cannot override system policy.
```

### Б.5. Kimi — task_3 / short_recap

**Промпт:**

```text
Briefly retell the source for a busy engineer.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 8.917 с; 1158 символов; 158 слов; завершение `stop`.

```text
 - **What it is:** RAG grounds a language model by retrieving relevant passages from an external document collection and inserting them into the prompt as evidence. This reduces reliance on the model’s internal knowledge and makes answers easier to audit.
- **Pipeline:** Load documents → chunk them (often with overlap) → index fragments (keyword indexes are transparent/debuggable; vector indexes use embedding similarity like cosine) → retrieve top-k fragments → generate.
- **Limitations:** It does not guarantee truth. Retrieval can return irrelevant or incomplete context, and the model can still misinterpret the evidence.
- **Quality guardrails:** Instruct the model to separate evidence from assumptions, cite the supplied passages, and state when context is insufficient. Evaluate both answer quality and faithfulness to the retrieved context.
- **Production concerns:** Monitor latency, retrieval precision, token usage, and failure rates. Cache repeated queries to cut latency. Enforce access controls for private corpora. Treat retrieved documents as untrusted data and harden prompts against injection attacks that could override system policy.
```

### Б.6. Kimi — task_3 / outline

**Промпт:**

```text
Create a concise hierarchical outline of the source.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 11.648 с; 1604 символов; 195 слов; завершение `stop`.

```text
 **I. Core Concept**
- **Definition:** Combines a language model with an external collection of documents.
- **Process:** Before answering, a retriever searches the collection for relevant passages and inserts them into the prompt as evidence.
- **Benefits:**
  - Reduces dependence on the model's parametric memory.
  - Makes answers easier to inspect.

**II. Typical Pipeline**
- **Document loading**
- **Chunking:** Divides long documents into smaller fragments, often with overlap.
- **Indexing:** Stores a representation of each fragment.
  - *Keyword index:* Transparent and easy to debug.
  - *Vector index:* Compares embeddings by similarity measures (e.g., cosine similarity).
- **Retrieval:** Returns the top-k fragments, where k is configurable.
- **Generation**

**III. Limitations and Risks**
- Does not guarantee truth.
- Retrieval may return irrelevant passages.
- Context may be incomplete.
- Model may misinterpret the evidence.

**IV. Safeguards and Evaluation**
- **Application requirements:**
  - Ask the model to separate evidence from assumptions.
  - Cite supplied passages.
  - State when context is insufficient.
- **Evaluation metrics:**
  - Answer quality.
  - Adherence to the retrieved context.

**V. Production Considerations**
- **Monitoring:** Latency, retrieval precision, token usage, and failure rates.
- **Performance:** Cache repeated queries to reduce latency.
- **Privacy:** Access controls needed for corpora containing private information.
- **Security:** Retrieved documents are untrusted data; prompt injection inside a document must not override system policy.
```

### Б.7. Kimi — task_3 / takeaways

**Промпт:**

```text
List the most useful practical takeaways from the source.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 9.614 с; 1396 символов; 190 слов; завершение `stop`.

```text
 Here are the most useful practical takeaways from the source:

- **Implement the full pipeline.** A typical RAG system requires document loading, chunking, indexing, retrieval, and generation stages.
- **Chunk with overlap.** Divide long documents into smaller fragments, often with overlap between chunks.
- **Match the index to your operational needs.** Use a keyword index when you want transparency and easier debugging; use a vector index (comparing embeddings via cosine similarity or similar measures) for semantic retrieval.
- **Make retrieval configurable.** The retriever returns a top-k set of fragments, and k should be treated as a configurable parameter.
- **Instruct the model to be explicit about evidence.** Prompt the model to separate evidence from assumptions, cite the supplied passages, and state when the context is insufficient.
- **Evaluate two things at once.** Measure both final answer quality and adherence to the retrieved context.
- **Monitor production metrics.** Track latency, retrieval precision, token usage, and failure rates.
- **Cache repeated queries.** This directly reduces latency.
- **Apply access controls for private corpora.** If the document collection contains private information, restrict access appropriately.
- **Treat retrieved documents as untrusted.** Prevent prompt injection inside a retrieved document from overriding the system policy.
```

### Б.8. Qwen — task_3 / summary

**Промпт:**

```text
Summarize the source in no more than 80 words.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 1.397 с; 752 символов; 100 слов; завершение `stop`.

```text
RAG combines a language model with an external document collection: a retriever finds relevant passages, which are added to the prompt as evidence, reducing reliance on the model’s internal memory and improving inspectability. The pipeline involves loading, chunking (often with overlap), indexing (keyword or vector), retrieval, and generation. However, RAG does not guarantee truth—retrieval may be irrelevant or incomplete, and models may misinterpret evidence. Best practices include requiring evidence citation, stating context limitations, and evaluating both answer quality and context adherence. Production considerations include latency (mitigated by caching), access controls, and safeguarding against prompt injection in retrieved documents.
```

### Б.9. Qwen — task_3 / main_points

**Промпт:**

```text
Extract the five main points from the source.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 2.227 с; 1277 символов; 168 слов; завершение `stop`.

```text
1. **RAG combines a language model with an external document collection**: A retriever searches the collection for relevant passages before answering, inserts them into the prompt as evidence, reducing reliance on the model’s parametric memory and improving answer interpretability.

2. **A typical RAG pipeline includes five stages**: document loading, chunking (dividing documents into overlapping fragments), indexing (storing fragment representations—e.g., keyword or vector-based), retrieval (fetching top-*k* relevant fragments), and generation (producing the final answer).

3. **RAG does not guarantee truth**: Risks include irrelevant or incomplete retrieved passages and model misinterpretation; applications should require the model to cite evidence, separate facts from assumptions, and acknowledge insufficient context.

4. **Evaluation must assess both answer quality and adherence to retrieved context**: Success is not only about correctness but also faithfulness to the provided evidence.

5. **Production considerations include performance, security, and reliability**: Teams monitor latency, retrieval precision, token usage, and failure rates; caching, access controls, and safeguards against prompt injection (e.g., from untrusted documents) are essential.
```

### Б.10. Qwen — task_3 / short_recap

**Промпт:**

```text
Briefly retell the source for a busy engineer.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 1.797 с; 898 символов; 126 слов; завершение `stop`.

```text
**RAG in One Paragraph for Busy Engineers:**  
RAG augments a language model with an external document corpus: a *retriever* first fetches top-*k* relevant text fragments (via keyword or vector/semantic search), inserts them into the prompt as evidence, and the *generator* answers using that context. A standard pipeline includes loading, chunking (often with overlap), indexing, retrieval, and generation. **Key caveats:** RAG doesn’t guarantee truth—retrieval can be noisy or incomplete, and models may hallucinate. Mitigate by prompting the model to cite evidence, flag assumptions, and declare insufficient context; evaluate both answer quality and faithfulness to retrieved passages. In production, monitor latency (cache repeated queries), retrieval precision, token usage, and failure rates; enforce strict access controls and prompt-injection safeguards since retrieved docs are untrusted.
```

### Б.11. Qwen — task_3 / outline

**Промпт:**

```text
Create a concise hierarchical outline of the source.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 2.464 с; 1091 символов; 141 слов; завершение `length`.

```text
**Hierarchical Outline of the Source on Retrieval-Augmented Generation (RAG)**

I. **Core Concept of RAG**  
   A. Combines a language model with an external document collection  
   B. Retrieval step: searches collection for passages relevant to user question  
   C. Evidence insertion: selected passages added to prompt as context  
   D. Benefits:  
      1. Reduces reliance on model’s parametric memory  
      2. Enables easier inspection of answers  

II. **Typical RAG Pipeline**  
   A. Document loading  
   B. Chunking  
      1. Splits long documents into smaller fragments  
      2. Often includes overlap between chunks  
   C. Indexing  
      1. Stores representation of each fragment  
      2. Types of indexes:  
         a. Keyword index: transparent and easy to debug  
         b. Vector index: compares embeddings using similarity (e.g., cosine similarity)  
   D. Retrieval  
      1. Returns top-*k* fragments (*k* is configurable)  
   E. Generation  
      1. Uses retrieved passages as evidence to generate answer  

III. **Limitations and Mitigations**  
   A.
```

### Б.12. Qwen — task_3 / takeaways

**Промпт:**

```text
List the most useful practical takeaways from the source.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 2.73 с; 1382 символов; 181 слов; завершение `length`.

```text
- RAG combines a language model with an external document collection to reduce reliance on the model’s parametric memory and improve answer traceability.  
- A typical RAG pipeline consists of five stages: document loading, chunking (often with overlap), indexing, retrieval, and generation.  
- Chunking divides long documents into smaller fragments to improve retrieval relevance and manageability.  
- Indexing can use keyword-based (transparent and debug-friendly) or vector-based (using embeddings and similarity measures like cosine similarity) methods.  
- Retrieval returns the top-*k* most relevant fragments, where *k* is a configurable parameter.  
- RAG does **not** guarantee truth: retrieved passages may be irrelevant, incomplete, or misinterpreted by the model.  
- Applications should require the model to: separate evidence from assumptions, cite supplied passages, and explicitly state when context is insufficient.  
- Evaluation must assess both answer quality and adherence to the retrieved context.  
- Production monitoring should track latency, retrieval precision, token usage, and failure rates.  
- Caching repeated queries can reduce latency.  
- Access controls are essential when the document corpus contains private information.  
- Retrieved documents are untrusted data: prompt injection attempts inside documents must not override system policies.
```

### Б.13. Kimi — task_4 / direct

**Промпт:**

```text
According to the source, which similarity measure can a vector index use?
Answer only from the source. If the source does not contain the answer, say exactly that the information is unavailable.

[Полный исходный текст из раздела 4]
```

**Ответ:** 2.341 с; 18 символов; 2 слов; завершение `stop`.

```text
 cosine similarity
```

### Б.14. Kimi — task_4 / inference

**Промпт:**

```text
Why can RAG improve inspectability while not guaranteeing truth?
Answer only from the source. If the source does not contain the answer, say exactly that the information is unavailable.

[Полный исходный текст из раздела 4]
```

**Ответ:** 3.092 с; 341 символов; 51 слов; завершение `stop`.

```text
 RAG improves inspectability because it inserts selected passages into the prompt as evidence, reducing dependence on the model's parametric memory and making an answer easier to inspect. It does not guarantee truth because retrieval may return irrelevant passages, the context may be incomplete, and the model may misinterpret the evidence.
```

### Б.15. Kimi — task_4 / unavailable

**Промпт:**

```text
According to the source, who invented RAG and in what year?
Answer only from the source. If the source does not contain the answer, say exactly that the information is unavailable.

[Полный исходный текст из раздела 4]
```

**Ответ:** 1.575 с; 32 символов; 4 слов; завершение `stop`.

```text
 The information is unavailable.
```

### Б.16. Qwen — task_4 / direct

**Промпт:**

```text
According to the source, which similarity measure can a vector index use?
Answer only from the source. If the source does not contain the answer, say exactly that the information is unavailable.

[Полный исходный текст из раздела 4]
```

**Ответ:** 0.38 с; 17 символов; 2 слов; завершение `stop`.

```text
cosine similarity
```

### Б.17. Qwen — task_4 / inference

**Промпт:**

```text
Why can RAG improve inspectability while not guaranteeing truth?
Answer only from the source. If the source does not contain the answer, say exactly that the information is unavailable.

[Полный исходный текст из раздела 4]
```

**Ответ:** 1.002 с; 440 символов; 64 слов; завершение `stop`.

```text
RAG improves inspectability because the retrieved passages are inserted into the prompt as evidence, making the basis for the answer transparent and traceable—unlike purely parametric models where the reasoning is hidden in weights. However, it does not guarantee truth because retrieval may return irrelevant or incomplete passages, and the model may misinterpret the evidence, leading to incorrect answers despite the presence of context.
```

### Б.18. Qwen — task_4 / unavailable

**Промпт:**

```text
According to the source, who invented RAG and in what year?
Answer only from the source. If the source does not contain the answer, say exactly that the information is unavailable.

[Полный исходный текст из раздела 4]
```

**Ответ:** 0.4 с; 31 символов; 4 слов; завершение `stop`.

```text
The information is unavailable.
```

### Б.19. Kimi — task_5 / plain_text

**Промпт:**

```text
Explain the main purpose of RAG in one paragraph.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 4.729 с; 409 символов; 67 слов; завершение `stop`.

```text
 The main purpose of retrieval-augmented generation (RAG) is to combine a language model with an external collection of documents so that, before answering, a retriever can search that collection for passages related to the user's question and insert the selected passages into the prompt as evidence. By doing so, RAG reduces dependence on the model's parametric memory and makes an answer easier to inspect.
```

### Б.20. Kimi — task_5 / list

**Промпт:**

```text
Explain the main purpose of RAG as exactly four bullet points.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 24.4 с; 308 символов; 47 слов; завершение `stop`.

```text
 - Combine a language model with an external collection of documents.
- Before answering, search that collection for passages related to the user's question.
- Insert the selected passages into the prompt as evidence.
- Reduce dependence on the model's parametric memory and make an answer easier to inspect.
```

### Б.21. Kimi — task_5 / json

**Промпт:**

```text
Return valid JSON only with exactly two keys: "purpose" (string) and "limitations" (array of strings).
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 13.943 с; 542 символов; 77 слов; завершение `stop`.

```text
 {"purpose":"Retrieval-augmented generation (RAG) combines a language model with an external collection of documents; before answering, a retriever searches that collection for passages related to the user's question and inserts the selected passages into the prompt as evidence, reducing dependence on the model's parametric memory and making an answer easier to inspect.","limitations":["RAG does not guarantee truth.","Retrieval may return irrelevant passages.","The context may be incomplete.","The model may misinterpret the evidence."]}
```

### Б.22. Qwen — task_5 / plain_text

**Промпт:**

```text
Explain the main purpose of RAG in one paragraph.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 1.029 с; 519 символов; 73 слов; завершение `stop`.

```text
The main purpose of RAG is to enhance the accuracy, reliability, and traceability of language model outputs by augmenting them with relevant, externally retrieved evidence from a document collection before generating a response—this reduces reliance on the model’s internal parametric memory, allows answers to be inspected against cited passages, and supports better accountability, though it does not guarantee factual correctness and requires careful handling of retrieval quality, context sufficiency, and security.
```

### Б.23. Qwen — task_5 / list

**Промпт:**

```text
Explain the main purpose of RAG as exactly four bullet points.
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 0.958 с; 474 символов; 64 слов; завершение `stop`.

```text
- Combines a language model with an external document collection to enhance responses using retrieved evidence.  
- Reduces reliance on the model’s parametric memory by inserting relevant passages into the prompt as context.  
- Enables more inspectable answers by grounding outputs in explicitly provided source material.  
- Requires careful evaluation and monitoring to ensure answers adhere to retrieved context and mitigate risks like hallucination or prompt injection.
```

### Б.24. Qwen — task_5 / json

**Промпт:**

```text
Return valid JSON only with exactly two keys: "purpose" (string) and "limitations" (array of strings).
Use only the source below.

[Полный исходный текст из раздела 4]
```

**Ответ:** 1.193 с; 542 символов; 72 слов; завершение `stop`.

```text
{
  "purpose": "To reduce dependence on the model's parametric memory and make answers easier to inspect by retrieving relevant passages from an external document collection and inserting them into the prompt as evidence.",
  "limitations": [
    "RAG does not guarantee truth.",
    "Retrieval may return irrelevant passages.",
    "The context may be incomplete.",
    "The model may misinterpret the evidence.",
    "Retrieved documents are untrusted data, and prompt injection inside a document must not override the system policy."
  ]
}
```

### Б.25. Kimi — task_6 / fact_probe

**Промпт:**

```text
Write a fact-heavy technical answer about RAG. Include at least three dates, numbers, technology names, author names, document titles, and URLs. Clearly label each claim as either supported by the supplied source or not supported by it. The supplied source is:

[Полный исходный текст из раздела 4]
```

**Ответ:** 77.897 с; 3752 символов; 533 слов; завершение `stop`.

```text
 Retrieval-augmented generation (RAG) combines a language model with an external collection of documents. **[Supported by the supplied source]** Before answering, a retriever searches that collection for passages related to the user's question. **[Supported by the supplied source]** The selected passages are inserted into the prompt as evidence. **[Supported by the supplied source]** This reduces dependence on the model's parametric memory and makes an answer easier to inspect. **[Supported by the supplied source]**

A typical RAG pipeline includes document loading, chunking, indexing, retrieval, and generation. **[Supported by the supplied source]** Chunking divides long documents into smaller fragments, often with overlap. **[Supported by the supplied source]** An index stores a representation of each fragment. **[Supported by the supplied source]** A keyword index is transparent and easy to debug, while a vector index compares embeddings by a similarity measure such as cosine similarity. **[Supported by the supplied source]** A retriever returns the top-k fragments, where k is a configurable number. **[Supported by the supplied source]**

RAG does not guarantee truth. **[Supported by the supplied source]** Retrieval may return irrelevant passages, the context may be incomplete, and the model may misinterpret the evidence. **[Supported by the supplied source]** Applications should ask the model to separate evidence from assumptions, cite the supplied passages, and state when the context is insufficient. **[Supported by the supplied source]** Evaluation should measure both answer quality and adherence to the retrieved context. **[Supported by the supplied source]**

Production teams monitor latency, retrieval precision, token usage, and failure rates. **[Supported by the supplied source]** Caching repeated queries can reduce latency. **[Supported by the supplied source]** Access controls are needed when a corpus contains private information. **[Supported by the supplied source]** Retrieved documents are untrusted data: prompt injection inside a document must not override the system policy. **[Supported by the supplied source]**

The foundational RAG architecture was introduced in the 2020 NeurIPS paper *“Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks”* by lead author Patrick Lewis and colleagues. **[Not supported by the supplied source]** That work indexed roughly 21,000,000 Wikipedia documents and is available at https://arxiv.org/abs/2005.11401. **[Not supported by the supplied source]** A precursor model, *“REALM: Retrieval-Augmented Language Model Pre-Training,”* was introduced by Kelvin Guu and colleagues in 2020. **[Not supported by the supplied source]**

Modern production stacks frequently rely on technologies such as LangChain, initially released in October 2022, and LlamaIndex to orchestrate pipelines. **[Not supported by the supplied source]** Vector indexes are commonly implemented with FAISS (Facebook AI Similarity Search) or Pinecone, storing embeddings from models like OpenAI's text-embedding-ada-002, which outputs 1,536-dimensional vectors. **[Not supported by the supplied source]** In practice, engineers often configure the retriever to return top-k results with k=5. **[Not supported by the supplied source]**

In December 2023, Yunfan Gao and co-authors published the survey *“Retrieval-Augmented Generation for Large Language Models: A Survey,”* available at https://arxiv.org/abs/2312.10997, which systematizes advances in retrieval strategies and evaluation. **[Not supported by the supplied source]** Another key resource for vector search is the FAISS repository at https://github.com/facebookresearch/faiss. **[Not supported by the supplied source]**
```

### Б.26. Qwen — task_6 / fact_probe

**Промпт:**

```text
Write a fact-heavy technical answer about RAG. Include at least three dates, numbers, technology names, author names, document titles, and URLs. Clearly label each claim as either supported by the supplied source or not supported by it. The supplied source is:

[Полный исходный текст из раздела 4]
```

**Ответ:** 4.596 с; 2093 символов; 291 слов; завершение `length`.

```text
Below is a fact-heavy technical answer about Retrieval-Augmented Generation (RAG), with each claim explicitly labeled as **supported by the supplied source** or **not supported by it**. The answer includes at least three dates, numbers, technology names, author names, document titles, and URLs—where such information appears in the supplied source or is verifiably established in the broader literature (and clearly distinguished as such).

---

1. **RAG was introduced in 2020 by Lewis et al. in the paper “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks”**  
   ✅ **Supported by external knowledge** (not the supplied source).  
   The technique was first proposed in the NeurIPS 2020 paper:  
   **Authors**: Patrick Lewis, Ethan Perez, et al.  
   **Title**: *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*  
   **URL**: https://arxiv.org/abs/2005.11401  
   **Date**: Submitted May 2020; published December 2020 (NeurIPS 2020).  
   *(Note: The supplied source does not mention authors, titles, or dates.)*

2. **A typical RAG pipeline includes five stages: document loading, chunking, indexing, retrieval, and generation**  
   ✅ **Supported by the supplied source**.  
   The source states: *“A typical RAG pipeline includes document loading, chunking, indexing, retrieval, and generation.”*

3. **Chunking often uses overlapping fragments (e.g., 150-token chunks with 50-token overlap)**  
   ❌ **Not supported by the supplied source**.  
   The source mentions: *“Chunking divides long documents into smaller fragments, often with overlap.”*  
   However, it does **not** specify concrete numbers (e.g., 150/50 tokens). Those values are common in practice (e.g., in FAISS + Sentence Transformers pipelines) but are not in the supplied text.

4. **Vector indexing uses embeddings and cosine similarity for similarity search**  
   ✅ **Supported by the supplied source**.  
   The source states: *“a vector index compares embeddings by a similarity measure such as cosine similarity.”*

5. **The retriever returns the top-*k* fragments, where *k* is
```
