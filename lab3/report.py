"""Bilingual reports follow the twelve assignment tasks and use saved evidence."""
from pathlib import Path
import csv
from .pipeline import ROOT, read, save
from .config import QUESTIONS, MY_RAG_INSTRUCTION, CORRECTION_ADDITION

FIELD_DEFINITIONS={
 'article_id':('Строковый ID ArXiv; ведущие нули сохранены','String ArXiv ID; leading zeros retained'),
 'authors':('Авторы публикации','Publication authors'),
 'title':('Название публикации','Publication title'),
 'categories':('Тематические категории','Subject categories'),
 'main_category':('Основная научная категория','Main scientific category'),
 'other_categories':('Дополнительные категории','Additional categories'),
 'abstract':('Аннотация, а не полный текст статьи','Abstract, not full paper'),
 'year':('Год публикации','Publication year'),
 'embedding_bge_m3':('Готовый 1024-мерный вектор BGE-M3','Precomputed 1024-dimensional BGE-M3 vector'),
}

def table(headers, rows):
    def cell(x): return str(x).replace('|','\\|').replace('\n','<br>')
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(cell(x) for x in row)+' |' for row in rows])

def csv_rows(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def build_reports(run_dir):
    run_dir=Path(run_dir); m=read(run_dir/'manifest.json')
    calls=read(run_dir/'calls.json') if (run_dir/'calls.json').exists() else {}
    corpus=read(run_dir/'corpus.json')
    retrieval=csv_rows(run_dir/'retrieval_review.csv'); claims=csv_rows(run_dir/'claims_review_template.csv')
    analysis=read(run_dir/'analysis.json') if (run_dir/'analysis.json').exists() else {}
    required_calls={f'q{i}_{mode}' for i in range(1,6) for mode in ['plain','rag']} | {'q1_simple','q2_simple','q1_k1','q1_k5','q1_manual','review','q1_corrected'}
    analysis_keys={f'{kind}_{lang}' for kind in ['prompts','comparison','k','review','correction','conclusions'] for lang in ['ru','en']}
    ready=required_calls.issubset(calls) and all(c['status']=='ok' for c in calls.values()) and len(retrieval)==15 and all(r['relevance_0_1_2'] in ['0','1','2'] and r['reason'] for r in retrieval) and len(claims)>=3 and all(r['claim'] and r['evidence_from_abstract'] and r['verdict'] in ['подтверждается','частично','не подтверждается','противоречит источнику'] and r['reason'] for r in claims) and all(analysis.get(k) for k in analysis_keys)
    m['report_ready']=ready
    if ready: m['status']='complete_pending_student_confirmation'
    save(run_dir/'manifest.json',m)
    out=ROOT/'reports/lab3'; out.mkdir(parents=True,exist_ok=True)
    for lang in ['ru','en']:
        L=lambda ru,en: ru if lang=='ru' else en
        pending=L('Не выполнено / ожидает проверки','Not performed / awaiting review')
        def answer(name): return calls.get(name,{}).get('answer') or pending
        def focus(name):
            paragraphs=answer(name).split('\n\n')
            return next((p for p in paragraphs if 'previously reported values' in p or 'compared to prior experimental measurements' in p),answer(name)[:900])
        sections=[L('# Отчёт по лабораторной работе 3 Исследование RAG по научным публикациям','# Lab 3 Report Researching RAG for Scientific Publications'),
                  L('**Статус:** '+('эксперименты и проверки записаны; самооценку нужно подтвердить.' if ready else 'ЧЕРНОВИК. Отсутствующие эксперименты или ручные проверки перечислены ниже. Сдавать как завершённую работу нельзя.'),'**Status:** '+('experiments and reviews recorded; student confirmation remains necessary.' if ready else 'DRAFT. Missing experiments or manual reviews are identified below. This is not a completed submission.')),
                  L('Работа выполнена по заданию из `docs/assignments/Лабораторная работа 3.md`. Исходный ноутбук преподавателя сохранён в lab3. Тема — квантовая запутанность.','The report follows docs/assignments/Лабораторная работа 3.md. The teacher notebook is retained in lab3. Topic: quantum entanglement.')]
        sections += [table([L('Параметр','Parameter'),L('Значение','Value')],[[L('Основная модель','Primary model'),m['primary_model']],[L('Рецензент','Reviewer'),m['review_model']],['temperature',m['temperature']],['max_tokens',m['max_tokens']],['recorded chat calls',len(calls)],['statuses',m.get('by_status',{})]]),
            L('Первые 15 chat-запросов вернули HTTP 400 без префикса cloud/ и сохранены в calls_unprefixed_400.json. Две успешные короткие пробы подтвердили маршрутизацию. Основные результаты получены после исправления. Дополнительный q3_corrected — разведочная проверка; задание 12 использует q1_corrected.','The first 15 chat requests returned HTTP 400 without cloud/ and remain in calls_unprefixed_400.json. Two successful short probes confirmed routing. Main results use the corrected route. The extra q3_corrected record is exploratory; Task 12 uses q1_corrected.')]
        sections += [L('## Задание 1 Подключение и эмбеддинги','## Task 1 Connection and embeddings'),
            'Embedding: `cloud-bge/BAAI/bge-m3`; POST `/v1/embeddings`; header `x-bf-vk`. Chat: Bearer authentication; wire model IDs use `cloud/` + model name.',
            L('Прогноз до API-запросов: предложения 1 и 2 наиболее близки; оба посвящены обработке информации с помощью ИИ. Сходство смысла не означает одинаковость или истинность утверждений.','Prediction recorded before API requests: sentences 1 and 2 should be closest because both discuss AI-based information processing. Semantic similarity implies neither factual identity nor truth.')]
        if (run_dir/'sentence_experiment.json').exists():
            sent=read(run_dir/'sentence_experiment.json'); sections += [table([L('Пара','Pair'),'cosine'],[[f'{i+1}–{j+1}',round(sent['cosine_matrix'][i][j],5)] for i in range(3) for j in range(i+1,3)])]
            best=max(((i,j) for i in range(3) for j in range(i+1,3)),key=lambda ij:sent['cosine_matrix'][ij[0]][ij[1]])
            sections += [L(f'Максимальная близость у пары {best[0]+1}–{best[1]+1}. Прогноз о сходстве предложений об ИИ и обработке информации подтвердился; предложение о прогулке относится к другой теме. Даже близкие предложения не утверждают полностью одно и то же.',f'The highest similarity is for pair {best[0]+1}–{best[1]+1}. The prediction about the AI and information-processing sentences is supported; the walk sentence concerns another topic. Even the similar sentences do not make identical claims.')]
        else: sections += [pending]
        sections += [L('## Задание 2 Датасет','## Task 2 Dataset'),table([L('Поле','Field'),L('Назначение','Purpose')],[[x, L(*FIELD_DEFINITIONS[x])] for x in m['fields']]),
            L('Самые частые категории среди всех 10000 просмотренных записей','Most frequent categories among all 10,000 scanned records'),
            table([L('Категория','Category'),L('Число записей','Records')],sorted(m['categories'].items(),key=lambda item:-item[1])[:6]),
            L('Примеры аннотаций из выборки','Sample abstracts from the subset')]
        for p in corpus[:3]: sections += [f"**{p['article_id']} — {p['title']}**\n\n{p['abstract']}"]
        sections += [table(['ArXiv',L('Какие сведения доступны','Information available'),L('Каких подробностей не хватает','Missing details')],[
            ['0704.0140',L('Применение AdS/CFT к энтропии чёрной дыры и заявленные ведущий и субведущий члены.','Use of AdS/CFT for black-hole entropy and the reported leading and subleading terms.'),L('Полный вывод формулы и проверка её предпосылок.','Full derivation and verification of assumptions.')],
            ['0704.0172',L('Система Shastry–Sutherland, аналитическая модель тетрамера и точная диагонализация.','Shastry–Sutherland system, analytical tetramer model, and exact diagonalization.'),L('Полные расчётные настройки, графики и подробности сопоставления моделей.','Full computational settings, plots, and detailed model comparisons.')],
            ['0704.0179',L('Получение и томография световых состояний, тесты неклассичности и оценка создаваемой запутанности.','Light-state preparation and tomography, nonclassicality tests, and generated-entanglement assessment.'),L('Подробная схема установки, числовые результаты и погрешности измерений.','Detailed apparatus, numerical results, and measurement uncertainties.')],
        ])]
        sections += [L('Аннотации позволяют определить метод, объект и заявленный авторами результат. В них могут отсутствовать экспериментальные параметры, доказательства, ошибки измерений и стоимость практического внедрения.','Abstracts identify methods, study systems, and results reported by authors. They may omit experimental settings, proofs, measurement errors, and deployment costs.'),
            L('## Задание 3 Тема и отбор','## Task 3 Topic and selection'),table([L('Показатель','Measure'),L('Значение','Value')],[[k,m[k]] for k in ['keyword','scanned','matches','selected']]+[[L('Годы в подмножестве','Years in subset'),', '.join(sorted({p['year'] for p in corpus}))]]),
            L('Отбор регистронезависимый по названию, аннотации и категориям. Выбраны первые 100 совпадений в порядке CSV, а не случайная репрезентативная выборка. Поиск ограничен этим подмножеством; отсутствующий источник система найти не может.','Case-insensitive matching searches title, abstract, and categories. The first 100 matches in CSV order form a convenience subset, not a random representative sample. Retrieval cannot return a source outside that subset.'),
            L('## Задание 4 Готовые векторы','## Task 4 Precomputed vectors'),f"Matrix: `{m['matrix_shape']}`; source model: `{m['embedding_model']}`.",
            L('Строки разбираются JSON-парсером в float32. Проверяются размерность, конечность и ненулевая норма. Документы и вопрос нормализуются: cosine(x,q) = (x·q)/(||x|| ||q||). Векторы статей не пересчитываются; API нужен только для вопросов и трёх тестовых предложений.','JSON strings become float32 vectors. Shape, finiteness, and nonzero norm are checked. Documents and queries are normalized: cosine(x,q) = (x·q)/(||x|| ||q||). Article vectors are reused; only questions and the three test sentences require embedding calls.'),
            L('## Задание 5 Пять вопросов и поиск','## Task 5 Five questions and retrieval'),table(['ID',L('Вопрос','Question')],list(enumerate(QUESTIONS,1))),
            table(['Q','ArXiv','cosine',L('Оценка 0–2','Relevance 0–2'),L('Обоснование','Reason')],[[r['question_id'],r['article_id'],r['similarity'],r['relevance_0_1_2'] or pending,(r.get('reason_ru',r['reason']) if lang=='ru' else r['reason']) or pending] for r in retrieval]) if retrieval else pending,
            L('Высокая близость может отражать общие термины, хотя статья не содержит нужного результата или изучает другую систему. Все 15 оценок требуют чтения аннотаций, а не порога cosine.','High similarity may reflect shared vocabulary while the article addresses a different system or does not contain the requested result. All 15 grades require reading the abstracts rather than thresholding cosine.'),
            L('## Задание 6 Ответ без документов','## Task 6 Answer without documents'),answer('q1_plain'),
            L('## Задание 7 Две версии промпта','## Task 7 Two prompt versions'),
            L('Простой: Answer the question using these article abstracts. Затем вопрос и тот же контекст.','Simple: Answer the question using these article abstracts. Follow with the question and identical context.'),
            '```text\n'+MY_RAG_INSTRUCTION+'\n```',
            table(['Q',L('Простой ответ фрагмент','Simple answer excerpt'),L('Улучшенный ответ фрагмент','Improved answer excerpt')],[[i,answer(f'q{i}_simple')[:700],answer(f'q{i}_rag')[:700]] for i in [1,2]]),analysis.get('prompts_'+lang,pending),
            L('Улучшение задаёт структуру, локальные ссылки и отказ при недостатке данных. Само наличие инструкции не доказывает, что ответ верен; наблюдения требуется сверить с источниками.','The improved instruction specifies structure, local citations, and abstention when evidence is missing. Adding an instruction does not establish correctness; observed changes need source checking.'),
            L('## Задание 8 RAG и обычные ответы','## Task 8 RAG versus ordinary answers'),
            table(['Q',L('Без RAG статус','Plain status'),L('RAG статус','RAG status')],[[i,calls.get(f'q{i}_plain',{}).get('status',pending),calls.get(f'q{i}_rag',{}).get('status',pending)] for i in range(1,6)]),
            analysis.get('comparison_'+lang,pending),
            L('## Задание 9 Количество и ручной отбор','## Task 9 Context size and manual selection'),
            table(['k',L('Отбор','Selection'),L('Ответ фрагмент','Answer excerpt')],[[r['k'],r['selection'],r['answer'][:350]] for r in csv_rows(run_dir/'k_experiment.csv')]) if (run_dir/'k_experiment.csv').exists() else pending,
            analysis.get('k_'+lang,pending),
            L('## Задание 10 Проверка утверждений','## Task 10 Claim verification'),
            L('Проверяется q1_rag: S1 = 0705.1308; S2 = 0704.0251; S3 = 0704.1506. Цитаты сопоставлены с полными аннотациями после нормализации пробелов.','Checked response: q1_rag. S1 = 0705.1308; S2 = 0704.0251; S3 = 0704.1506. Evidence fragments were matched to the full abstracts after whitespace normalization.'),
            table([L('Утверждение','Claim'),L('Источник','Source'),L('Фрагмент аннотации','Abstract evidence'),L('Вердикт','Verdict'),L('Обоснование','Reason')],[[r['claim'] or pending,r['source_id'],r['evidence_from_abstract'],r['verdict'] if lang=='ru' else {'подтверждается':'supported','частично':'partly supported','не подтверждается':'unsupported','противоречит источнику':'contradicted'}.get(r['verdict'],r['verdict']),r.get('reason_ru',r['reason']) if lang=='ru' else r['reason']] for r in claims]) if claims else pending,
            L('## Задание 11 Рецензия второй модели','## Task 11 Second-model review'),answer('review')[:1000],analysis.get('review_'+lang,pending),
            L('## Задание 12 Исправление одной ошибки','## Task 12 One error correction'),
            L('Изменён только промпт для вопроса 1. Модель и три найденных источника сохранены. Добавлена одна инструкция:','Only the prompt for question 1 is changed. The model and the three sources remain the same. Added instruction:'),
            CORRECTION_ADDITION,table([L('До фрагмент','Before excerpt'),L('После фрагмент','After excerpt')],[[focus('q1_rag'),focus('q1_corrected')]]),analysis.get('correction_'+lang,pending),
            L('## Выводы и ограничения','## Conclusions and limitations'),analysis.get('conclusions_'+lang,L('Эксперимент пока не завершён. Нельзя делать выводы об улучшении качества до выполнения API-запросов и проверки утверждений.','The experiment is incomplete. Quality improvements cannot be concluded before API execution and claim verification.')),
            L('Все полные промпты, ответы, статусы и привязки источников находятся в `results/lab3_entanglement/`. Самостоятельные оценки являются предложением для проверки студентом.','Full prompts, responses, statuses, and source mappings are in results/lab3_entanglement/. Proposed manual judgments require student confirmation.')]
        path=out/('LAB3_REPORT.md' if lang=='ru' else 'LAB3_REPORT_EN.md')
        path.write_text('\n\n'.join(sections)+'\n',encoding='utf-8'); print(path)
