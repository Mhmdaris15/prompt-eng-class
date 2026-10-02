"""Record the manual, run-specific review and checked fact claims."""
import csv
import json
import statistics
from pathlib import Path
from labs.common import write_csv

RUN = Path('results/lab1_final')
MODELS = {'Kimi':'moonshotai/Kimi-K2.6', 'Qwen':'Qwen/Qwen3-Coder-Next'}
scores = {
('Kimi','task_2','identical_explanation'):((4,5,5,5,5,4),'Clear explanation and practical example; says RAG cuts hallucinations, which could imply too much certainty.'),
('Qwen','task_2','identical_explanation'):((4,5,5,5,5,4),'Within the word limit and gives a clear example; “ensuring” policy accuracy overstates what retrieval guarantees.'),
('Qwen','task_3','summary'):((5,5,5,2,5,5),'Good summary, but 104 words exceeds the requested 80-word maximum.'),
('Kimi','task_3','summary'):((5,5,5,5,5,5),'Exactly 80 words under the recorded word counter; retains purpose, stages, limitations, and safeguards.'),
('Kimi','task_3','main_points'):((5,5,5,5,5,5),'Exactly five detailed points cover the main sections of the source.'),
('Qwen','task_3','main_points'):((5,5,5,5,5,5),'Exactly five concise points retain the same principal ideas.'),
('Qwen','task_3','short_recap'):((5,5,5,5,5,5),'Readable recap for an engineer; includes the source’s versioning, index, and evidence guidance.'),
('Kimi','task_3','short_recap'):((5,5,5,5,5,5),'Readable recap that preserves the reliability and production themes.'),
('Kimi','task_3','outline'):((5,5,5,5,5,5),'Complete hierarchical outline; its 547 words are reasonable for a detailed outline.'),
('Qwen','task_3','outline'):((5,5,5,5,5,5),'Complete, clearly nested outline, shorter than Kimi’s at 470 words.'),
('Qwen','task_3','takeaways'):((5,5,5,5,5,5),'Actionable points cover chunking, metadata, index maintenance, security, and evaluation.'),
('Kimi','task_3','takeaways'):((5,5,5,5,5,5),'Detailed practical advice follows the expanded source closely.'),
('Kimi','task_4','direct'):((5,5,5,5,5,5),'Exact direct answer from the source.'),
('Qwen','task_4','direct'):((5,5,5,5,5,5),'Exact direct answer from the source.'),
('Qwen','task_4','inference'):((5,5,5,5,5,5),'Connects inspectability to explicit evidence and discusses outdated or conflicting passages from the source.'),
('Kimi','task_4','inference'):((5,5,5,5,5,5),'Concise explanation supported by the supplied text.'),
('Kimi','task_4','unavailable'):((5,5,5,5,5,5),'Returns the exact requested unavailable-information response.'),
('Qwen','task_4','unavailable'):((5,5,5,5,5,5),'Returns the exact requested unavailable-information response.'),
('Qwen','task_5','plain_text'):((5,5,5,5,5,5),'One paragraph covers the four requested aspects.'),
('Kimi','task_5','plain_text'):((5,5,5,5,5,5),'One coherent paragraph covers purpose, retrieval, limitations, and security.'),
('Kimi','task_5','list'):((5,5,4,5,4,5),'Exactly four correct points; each point is long, but the categories remain clear.'),
('Qwen','task_5','list'):((5,5,5,5,5,5),'Four concise points in the requested order.'),
('Qwen','task_5','json'):((5,5,5,5,5,5),'Valid JSON, exact four keys and string values, with no surrounding text.'),
('Kimi','task_5','json'):((5,5,4,5,5,5),'Valid JSON with the exact schema; 478 words makes the values less convenient to scan.'),
('Kimi','task_6','fact_probe'):((4,5,5,5,5,5),'The three checked paper references exist. “Introduced RAG” is broader than the paper’s claim to introduce its particular RAG models.'),
('Qwen','task_6','fact_probe'):((2,4,4,3,3,3),'The Ragas authors are misattributed and the cited Hugging Face path returns 404; other selected claims are supported.'),
}

score_comments_ru = {
('Kimi','task_2','identical_explanation'):'Объяснение понятное, пример практический; фраза о том, что RAG сокращает галлюцинации, может прозвучать как гарантия.',
('Qwen','task_2','identical_explanation'):'Ответ укладывается в лимит и содержит ясный пример; слово «обеспечивает» преувеличивает гарантии актуальности.',
('Qwen','task_3','summary'):'Хорошее резюме, но 104 слова превышают заданный максимум 80.',
('Kimi','task_3','summary'):'80 слов по использованному счётчику; сохранены назначение, этапы, ограничения и меры защиты.',
('Kimi','task_3','main_points'):'Ровно пять подробных пунктов охватывают основные разделы источника.',
('Qwen','task_3','main_points'):'Ровно пять более кратких пунктов сохраняют те же основные идеи.',
('Qwen','task_3','short_recap'):'Связный пересказ для инженера; учитывает версии, индекс и работу со свидетельствами.',
('Kimi','task_3','short_recap'):'Понятный пересказ с основными ограничениями и эксплуатационными аспектами.',
('Kimi','task_3','outline'):'Полный иерархический план; 547 слов оправданы подробной структурой.',
('Qwen','task_3','outline'):'Полный и хорошо вложенный план; 470 слов — короче ответа Kimi.',
('Qwen','task_3','takeaways'):'Практические пункты охватывают фрагментацию, метаданные, индекс, безопасность и оценку.',
('Kimi','task_3','takeaways'):'Подробные рекомендации близко следуют расширенному исходному тексту.',
('Kimi','task_4','direct'):'Точный прямой ответ по исходному тексту.',
('Qwen','task_4','direct'):'Точный прямой ответ по исходному тексту.',
('Qwen','task_4','inference'):'Связывает проверяемость с явными свидетельствами и использует обсуждённые в тексте устаревшие и конфликтующие фрагменты.',
('Kimi','task_4','inference'):'Краткое и точное объяснение, подтверждаемое исходным текстом.',
('Kimi','task_4','unavailable'):'Выдана запрошенная фраза об отсутствии информации.',
('Qwen','task_4','unavailable'):'Выдана запрошенная фраза об отсутствии информации.',
('Qwen','task_5','plain_text'):'Один абзац охватывает все четыре требуемых аспекта.',
('Kimi','task_5','plain_text'):'Связный абзац описывает назначение, поиск, ограничения и безопасность.',
('Kimi','task_5','list'):'Ровно четыре корректных пункта; пункты длинные, но смысловые категории различимы.',
('Qwen','task_5','list'):'Четыре кратких пункта в заданном порядке.',
('Qwen','task_5','json'):'Валидный JSON с точными четырьмя ключами и строковыми значениями; дополнительного текста нет.',
('Kimi','task_5','json'):'Валидный JSON с требуемой схемой; 478 слов затрудняют быстрое чтение значений.',
('Kimi','task_6','fact_probe'):'Три проверенные ссылки ведут на реальные публикации. Формулировка «ввели RAG» шире, чем утверждение статьи о предложенных в ней моделях RAG.',
('Qwen','task_6','fact_probe'):'Авторы статьи Ragas указаны неверно, а ссылка на репозиторий Hugging Face возвращает 404; остальные выбранные факты подтверждаются.',
}
scores = {key: (value[0], score_comments_ru[key]) for key, value in scores.items()}

sources = [
('Kimi',1,'Lewis et al. introduced retrieval-augmented generation in the 2020 NeurIPS paper Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.','https://arxiv.org/abs/2005.11401','Подтверждено с уточнением','The title, authors, 2020 preprint date, and NeurIPS acceptance are supported. More precisely, the paper introduces particular RAG models; it does not establish that all retrieval-augmented generation began there.'),
('Kimi',2,'Gao et al. published the survey Retrieval-Augmented Generation for Large Language Models: A Survey in 2023.','https://arxiv.org/abs/2312.10997','Подтверждено','The first arXiv version was submitted on 18 December 2023; title and lead author match.'),
('Kimi',3,'Asai et al. proposed Self-RAG in the 2023 paper Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection.','https://arxiv.org/abs/2310.11511','Подтверждено','The arXiv record confirms title, Akari Asai as lead author, and first-version date 17 October 2023.'),
('Qwen',1,'The paper by Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks, is from 2020.','https://arxiv.org/abs/2005.11401','Подтверждено с уточнением','Title, Patrick Lewis, coauthors, and first-version date 22 May 2020 are supported. “Introduced RAG” needs qualification: the paper presents particular RAG models.'),
('Qwen',2,'The URL https://github.com/huggingface/transformers/tree/main/examples/research_projects/rag contains the RAG implementation and its Apache 2.0 license.','https://github.com/huggingface/transformers/tree/main/examples/research_projects/rag','Ссылка не работает; лицензия не подтверждена','The cited path returns 404 on 2 October 2026. A related project is in the separate transformers-research-projects/rag repository; the cited URL does not verify the implementation or its license.'),
('Qwen',3,'Ragas: Automated Evaluation of Retrieval Augmented Generation was written by Pawar et al. in 2023, arXiv:2309.15217.','https://arxiv.org/abs/2309.15217','Ошибка в авторах; статья и год подтверждены','The identifier and 2023 date are real, but the arXiv authors are Shahul Es, Jithin James, Luis Espinosa-Anke, and Steven Schockaert, not Pawar et al.'),
('Qwen',4,'RAG fragment metadata may include title, version, owner, access policy, and update time.','source_text.txt','Подтверждено исходным текстом','The supplied source explicitly lists these metadata fields and explains their use for filtering and citations.'),
]
source_comments_ru = [
'Название, авторы, дата препринта 2020 года и принятие на NeurIPS подтверждаются. Точнее: в статье представлены определённые модели RAG; она не доказывает первенство всей идеи retrieval augmentation.',
'Первая версия arXiv подана 18 декабря 2023 года; название и первый автор совпадают.',
'Запись arXiv подтверждает название, Akari Asai как первого автора и дату первой версии — 17 октября 2023 года.',
'Название, Patrick Lewis, соавторы и дата первой версии — 22 мая 2020 года — подтверждаются. Фразу «ввели RAG» следует уточнить: статья представляет конкретные модели RAG.',
'При проверке 2 октября 2026 года указанный путь возвращает 404. Похожий проект есть в отдельном репозитории transformers-research-projects/rag; приведённый URL не подтверждает ни реализацию, ни её лицензию.',
'Идентификатор и дата публикации 2023 года реальны, но авторы — Shahul Es, Jithin James, Luis Espinosa-Anke и Steven Schockaert, а не Pawar et al.',
'В исходном тексте прямо перечислены эти поля метаданных и описано их использование для фильтрации и цитирования.',
]
sources = [(*row[:5], source_comments_ru[index]) for index, row in enumerate(sources)]

def main():
    with (RUN/'lab1_results.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=26: raise ValueError('Expected all 26 completed answers')
    rubric=[]
    fields=('accuracy_1_5','completeness_1_5','clarity_1_5','instruction_following_1_5','structure_1_5','verifiability_1_5')
    for row in rows:
        values,comment=scores[(('Kimi' if row['model']==MODELS['Kimi'] else 'Qwen'),row['task'],row['variant'])]
        rubric.append({'model':row['model'],'task':row['task'],'variant':row['variant'],**dict(zip(fields,values)),'comment':comment})
    write_csv(RUN/'quality_scores.csv',rubric)
    facts=[]
    for model,num,claim,url,status,comment in sources:
        facts.append({'model':MODELS[model],'claim_number':num,'candidate_claim':claim,'source_or_url_checked':url,'status':status,'comment':comment,'raw_output_file':'lab1_results.csv','verification_date':'2026-10-02'})
    write_csv(RUN/'hallucination_verification.csv',facts)
    latency={}
    for model in MODELS.values():
        values=[float(r['latency_seconds']) for r in rows if r['model']==model]
        latency['Kimi' if model==MODELS['Kimi'] else 'Qwen']={'mean':round(statistics.mean(values),3),'median':round(statistics.median(values),3)}
    notes={
    'first_query':'Обе модели выполнили лимит 120 слов: Kimi — 103, Qwen — 109. Kimi объяснила retrieval и привела пример компании. Обе фразы о снижении галлюцинаций не означают гарантию; примеры придуманы для объяснения и не являются подтверждёнными случаями.',
    'summaries':{'summary':'Kimi уложилась в 80 слов; Qwen сохранила содержание, но превысила лимит (104 слова).','main_points':'Обе выдали ровно пять пунктов; Kimi подробнее, Qwen компактнее.','short_recap':'Оба пересказа учитывают аудиторию инженера; числового ограничения длины не было.','outline':'Обе иерархические структуры закончены; Kimi — 547 слов, Qwen — 470.','takeaways':'Оба списка извлекают конкретные действия; Qwen короче: 275 против 529 слов.'},
    'summary_conclusion':'Для краткого резюме лучше всего сработал явный предел: Kimi уложилась в 80 слов, Qwen превысила его. Пять главных пунктов дали одинаково удобную структуру у обеих моделей. У краткого пересказа и плана не было числовой границы, поэтому ответы получились объёмными. Практические выводы полезны для действий, но это уже рекомендации, а не простой пересказ. Промпты меняют несколько условий сразу, поэтому вывод относится к целым формулировкам.',
    'questions':'Обе модели ответили cosine similarity на прямой вопрос и вернули точную фразу “The information is unavailable.” на вопрос об авторе и годе. На смысловой вопрос обе объяснили прозрачность свидетельств и отсутствие гарантии истины; Qwen подробнее использовала примеры версий и конфликтующих фрагментов из расширенного текста. В этой выборке соблюдение границы контекста одинаково; один пример не гарантирует такое поведение всегда.',
    'formats':'Автоматическая проверка прошла для всех шести ответов: оба абзаца остались одним абзацем, оба списка имеют ровно четыре пункта, оба JSON разбираются и содержат точные четыре строковых ключа. Содержание одинаково охватывает назначение, retrieval, ограничения и безопасность. JSON Kimi длиннее (478 слов против 155), JSON Qwen быстрее просматривать. Список удобен для человека, JSON — для программы. По соблюдению структуры результат равный.',
    'fact_probe':'Три выбранные ссылки Kimi ведут на реальные первичные публикации с совпадающими заглавиями, датами и первыми авторами; формулировка «introduced RAG» нуждается в уточнении. В ответе Qwen верна ссылка на Lewis et al., но Ragas приписана неправильным авторам, а ссылка на Hugging Face возвращает 404. Это конкретные находки в небольшом наборе, не оценка общей частоты ошибок модели.',
    'latency':f"Qwen была быстрее во всех 13 парных запросах. Среднее/медианное клиентское время: Kimi — {latency['Kimi']['mean']}/{latency['Kimi']['median']} с; Qwen — {latency['Qwen']['mean']}/{latency['Qwen']['median']} с. Это один запуск для этих моделей и этой сервисной инфраструктуры; цифры не являются универсальной скоростью моделей. Ошибок API и ответов, ограниченных бюджетом токенов, нет.",
    'quality_conclusion':'В этом запуске Kimi точно выполнила ограничение суммаризации и дала более краткий список фактов. Qwen отвечала быстрее и кратко соблюдала структурированные форматы. Обе правильно обработали отсутствующий ответ и прошли автоматические проверки формата. В выбранной ручной проверке внешних фактов у Qwen выявлены ошибка авторства Ragas и неработающий URL. Выборка и один повтор не позволяют присвоить моделям общий рейтинг.',
    'verification_conclusion':'Проверка выявила две конкретные проблемы у Qwen: неверная атрибуция авторов статьи Ragas и неработающий путь GitHub. Остальные выбранные утверждения подтверждены с оговоркой об авторстве и области источника. У Kimi не установлено ложных сведений в трёх выбранных ссылках, но заявление, что статья Lewis et al. ввела всю идею RAG, шире подтверждаемого факта о конкретных RAG-моделях. URL нужно открыть и сверить с точным утверждением.',
    'conclusions':'1. **Различия моделей.** Qwen была быстрее во всех 13 запросах; медианы — '+str(latency['Qwen']['median'])+' с у Qwen и '+str(latency['Kimi']['median'])+' с у Kimi. Все 26 ответов закончены без API-ошибок и обрезки.\n2. **Влияние промпта.** Числовой предел 80 слов дал краткое резюме Kimi; запрос пяти пунктов облегчает сравнение; свободный план и пересказ длиннее.\n3. **Полезные инструкции.** «Только по этому тексту», точная фраза для отсутствующих данных, одинаковая область четырёх смысловых аспектов и строгая схема JSON повысили проверяемость.\n4. **Внешние утверждения.** Запрос фактов разрешал внешний контекст. Проверка выявила у Qwen неверного автора и неработающую ссылку, несмотря на внешне точный ответ.\n5. **Необходимость проверки.** Реальный URL не гарантирует правильную атрибуцию или поддержку тезиса; проверять нужно содержание страницы, автора, название, дату и точное утверждение.\n6. **Надёжность в рамках эксперимента.** В трёх выбранных внешних утверждениях Kimi было меньше установленных ошибок; Qwen существенно быстрее. Малая выборка не поддерживает универсальный рейтинг.'}
    (RUN/'review_notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Added {len(rubric)} rubric reviews, {len(facts)} checked claims, and report analysis notes.')

if __name__=='__main__': main()
