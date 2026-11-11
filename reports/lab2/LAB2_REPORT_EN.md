# Lab 2 Report on Prompt Engineering and Few Shot Prompting


## 1. Cover page

**ITMO University / Университет ИТМО**  
**Course:** Prompt Engineering  
**Student:** ____________________  
**Group:** ____________________  
**Experiment time:** 2026-10-28T20:32:24.058164  
**Run folder:** `results\lab2_claude_haiku_llama_20261028_202806`  
**Models:** A `anthropic/claude-haiku-4.5`; B `meta-llama/llama-3.3-70b-instruct`.


## 2. Objective and method

The objective was to design and compare a simple prompt, a structured prompt (V1), a one-shot prompt (V2), and a few-shot prompt (V3), then test edge cases and obtain an independent review. Model A produced the baseline and final essay; identical V1, V2, and V3 prompt strings were sent to both models. Model B reviewed Model A’s V3 answer in a separate request. Prompts and model answers are preserved verbatim in their original English.

Measured word counts use whitespace-separated tokens in the saved answer. The script’s automatic counts for links, years, numbers, and caution/confidence markers are indicators only; they do not establish factual accuracy. The run used one request per planned cell, except the final answer can have at most two attempts; this run required one attempt.


## 3. Models and run conditions

| Parameter | Value |
| --- | --- |
| Model A | anthropic/claude-haiku-4.5 |
| Model B | meta-llama/llama-3.3-70b-instruct |
| API profile | cloudru |
| Endpoint | https://foundation-models.api.cloud.ru/v1 |
| Temperature | 0.3 |
| Max output tokens | 4096 |
| Timeout | 180.0 s |
| Requests | 12 successful, 1 error, 0 truncated |

Generation-time runner SHA-256: `17f102573eea7ef847479a4431098393441ad46e8130d9f952c4a3070c119e80`. The report parser was subsequently improved to recover the JSON object from the reviewer’s fenced response; the original model response remains unchanged in `lab2_results.json`. The manifest source-text hash is `13ef01169bfade1627006d0819cfeb2c659c4e2ad65a5e61c65a3b96877836e3`. No API key is stored in the run.


## 4. Task 1: Topic and task definition

| Question | Answer |
| --- | --- |
| What topic was selected? | Why AI answers need verification |
| What should the model do? | Write a mini-essay for 9th–10th grade students explaining why AI answers need verification, give two concrete examples, and reach a cautious conclusion. |
| Who is the text for? | Students in grades 9–10 (ages 14–16) |
| Where could this text be used? | In a computer science or digital literacy class as learning material about checking AI-generated information. |
| What should a good result look like? | A 180–220-word mini-essay with a clear structure, two explained examples, factual care, and a cautious conclusion. |
| Which model errors are especially undesirable here? | Fabricated sources or facts; unsupported dates or numbers; overconfidence; missing required structure; language unsuitable for the audience. |


## 5. Task 2: Quality criteria and rubric

The first table reproduces the six core criteria and descriptions from the assignment. Scores are a draft assessment of Model A’s final V3 answer for the student to confirm. The second table adds operational checks used in this experiment.

| Criterion | How to tell it is met | Score 0–2 |
| --- | --- | --- |
| Topic relevance | The answer stays on the selected topic. | 2 |
| Audience clarity | The text is understandable to the intended audience. | 2 |
| Structure | The text has an opening, development, and conclusion. | 2 |
| Specificity | The answer includes examples, not only general discussion. | 1 |
| Factual care | There are no fabricated facts, dates, quotations, or sources. | 2 |
| Style | The tone fits the task. | 2 |

Scale: 0 = not met; 1 = partly met; 2 = met. Draft scores must be reviewed by the student.

Supplementary operational rubric

| Criterion | How checked | Draft self-score 0–2 |
| --- | --- | --- |
| Topic relevance | Directly answers the assigned task | 2 |
| Audience clarity | Language level fits the intended audience | 2 |
| Logical structure | Introduction, thesis, examples, explanations, and conclusion | 2 |
| At least two concrete examples | Two distinguishable examples | 1 |
| Factual care | No unsupported specific facts or citations | 2 |
| Appropriate and cautious style | Calm tone and cautious wording | 2 |
| 180–220 word length | Whitespace-separated word count: 180–220 | 2 |
| Conclusion adds no new arguments | No new argument in the conclusion | 2 |
| Usable after minor editing | Requires only minor editing | 1 |

Scale: 0 = not met; 1 = partly met; 2 = met. The draft scores are justified again in the self-review section.


## 6. Task 3: Simple prompt and first result

**Prompt:**

```text
Write a short essay about why ai answers need verification for students.
```

**Model A answer:** (269 words)

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

Draft assessment: the answer is 269 words, which is over the 180–220 target; the prompt does not specify audience, structure, examples, or cautious style. Three observed shortcomings are: (1) length above target; (2) no requirement for two explained examples; (3) no target age or format. These observations motivate V1.


## 7. Task 4: Structured prompt design

| Prompt part | What was added | Why it is needed |
| --- | --- | --- |
| Role | Educational content writer specializing in teen digital literacy | Sets expected expertise and register |
| Task | Explain why AI answers need verification | Defines the central question |
| Audience | Grades 9–10, ages 14–16 | Guides vocabulary and explanation |
| Context | Teen digital literacy is implicit in the role; classroom setting is not named explicitly | Could be made more explicit in a future revision |
| Content and structure | Short introduction, central point, two explained failures, cautious conclusion | Makes expected parts observable |
| Constraints | 180–220 words; no fabricated facts, dates, sources, or statistics; avoid absolutes | Limits scope and unsupported precision |
| Format | Plain-text paragraphs | Makes the output easy to reuse |
| Quality criteria | Embedded as content requirements; not a separate numbered checklist in V1 | Supports review; a future version could include an explicit checklist |


## 8. Task 5: V1 prompt and cross-model comparison

**V1 verbatim:**

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



**anthropic/claude-haiku-4.5 — ok, 95 words, 4.346 s:**

```text
# Why You Should Verify AI Answers

You've probably used AI chatbots to help with homework or answer quick questions. They're fast and often helpful, but here's something important to understand: AI doesn't actually "know" things the way you do. Instead, it predicts what words should come next based on patterns in its training data.

This matters because AI can sound confident while being completely wrong. When an AI generates text, it's essentially making educated guesses about what's probable, not checking facts against reliable sources. This can lead to problems.

One common issue is "Overloaded
```



**meta-llama/llama-3.3-70b-instruct — ok, 166 words, 30.385 s:**

```text
As we increasingly rely on artificial intelligence (AI) for information, it's essential to understand its limitations. AI can generate human-like text, but this doesn't mean the information is accurate or up-to-date. It's crucial to verify AI answers to ensure we're getting reliable information.

AI generates probable text based on patterns and associations, not verified facts. This can lead to errors, such as hallucination, where AI provides information that isn't based on any actual data. For example, AI might describe a fictional event as if it were real. Another issue is outdated knowledge, where AI provides information that was once true but is no longer accurate.

For instance, AI might confidently state that a certain company is still in business, even if it has gone bankrupt. In both cases, AI's errors can be misleading and potentially harmful. It's essential to fact-check AI answers to separate fact from fiction. By being cautious and verifying information, we can use AI as a helpful tool while avoiding its potential pitfalls.
```



**Required simple-prompt versus V1 comparison:**

| Criterion | Simple prompt | Prompt V1 | Comment |
| --- | --- | --- | --- |
| Topic relevance | Addresses verification of AI answers. | Same central topic is stated explicitly. | Both stay on topic. |
| Audience clarity | Students are mentioned, but age and grade are unspecified. | Grades 9–10 (ages 14–16) are specified. | V1 gives the model a usable audience definition. |
| Structure | The answer has headings and a closing paragraph, but no requested outline. | A five-part outline is required; the returned answer is incomplete and stops mid-sentence. | V1 is clearer, but this output is incomplete. |
| Specificity | Discusses failure modes generally; two examples are not required. | Two examples are required, but the captured answer stops before providing them. | The V1 requirement was not fulfilled in this response. |
| Style | Formal educational tone; audience is not tailored. | Calm, plain language for teenagers is requested. | V1 states the style more precisely. |
| Factual care | No sources are cited; factual claims were not independently verified. | Fabrication is prohibited; the incomplete answer contains no citations. | Prompt constraints do not replace fact-checking. |


Claude Haiku’s V1 response is substantially under the target at 95 words and ends mid-sentence at “One common issue is Overloaded,” despite finish_reason=stop. Llama’s is also short at 166 words. Neither response meets the range; specifying a range did not guarantee compliance.


## 9. Task 6: Good and bad few-shot examples

| Example type | Example text | Why it is good or weak |
| --- | --- | --- |
| Weak | AI is useful for everyone because it makes life easier and helps with many tasks. | Too general, no concrete situation, no conditional phrasing, reads like a slogan |
| Stronger | AI can help a student understand a difficult concept if used as an explanation assistant rather than a way to just get the answer. For example, asking 'Can you explain how photosynthesis works step by step?' is more useful than asking 'What is the answer to question 5?' | Specific situation (student learning), conditional phrasing ('if used as...'), contrasts good vs bad usage, appropriate caution |

The stronger example concerns using AI to learn a difficult concept; it is related to education but does not repeat the essay’s exact verification task.


## 10. Task 7: V2 one-shot prompt

**V2 verbatim:**

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



**anthropic/claude-haiku-4.5 — ok, 203 words, 5.304 s:**

```text
# Why You Should Check AI Answers

You've probably used AI to help with homework or answer questions. It's fast and often sounds confident. But here's something important: AI doesn't actually know things the way you do. It generates text based on patterns it learned, which means it can sound right while being wrong.

**AI generates probable text, not verified facts.** Think of it like this: AI predicts what words should come next based on what it's seen before. It's really good at this, but prediction isn't the same as knowing. Sometimes AI confidently gives you information that sounds completely real but isn't.

For example, AI might invent details about historical events or create fake names of scientists who don't exist. It does this without hesitation because it's just following patterns, not checking facts. Another common problem is outdated information. If AI was trained on older data, it might give you information that's no longer current, like outdated scientific understanding or old statistics.

**The takeaway:** AI is a useful tool, but treat it like a starting point, not a final answer. Cross-check important information with reliable sources like textbooks, educational websites, or your teacher. Using AI thoughtfully—combined with verification—makes you a smarter learner.
```



**meta-llama/llama-3.3-70b-instruct — error, 0 words, 77.191 s:**

The request failed and returned no answer.



Model A’s V2 output is 203 words, inside the requested range, compared with its 95-word V1 output. It adds more concrete formulations, including invented historical details and fake scientist names as hypothetical examples. Model B’s V2 request returned HTTP 502 (“Request failed”) after 77.191 seconds; there is no B answer to compare for this cell. The one-shot example may have helped Model A reach the length target, but one run cannot establish causation.


**Required V1/V2 comparison:**

| Question | Answer |
| --- | --- |
| What changed after adding the example? | V2 includes one example about asking AI to explain a difficult topic step by step. |
| Did the answer become more specific? | Partly: Model A moved from a general V1 discussion to two named failure types in V2; the examples remain hypothetical. |
| Did the style move closer to the target? | Yes: the V2 answer is plain and student-facing and has 203 words, within the target. |
| Did the model copy the example? | No literal copying was identified; the answer uses its own examples. |
| Should the example remain in the prompt? | Keep the teaching pattern, but use a neutral hypothetical example and avoid fake names or citations. |


## 11. Task 8: V3 few-shot prompt and comparison

**V3 verbatim:**

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



**anthropic/claude-haiku-4.5 — ok, 214 words, 4.651 s; caution markers 1, confident markers 1:**

```text
# Why You Should Verify AI Answers

You've probably used AI to help with homework or answer questions. It's fast and often helpful. But here's something important: AI doesn't actually "know" facts the way you do. Instead, it predicts the next word based on patterns it learned during training, which means it can sound confident while being completely wrong.

AI sometimes invents information that sounds plausible but doesn't exist. For example, an AI might describe a historical event with specific details—names, dates, locations—that seem real but are actually made up. A student might copy these details into an essay, only to have a teacher point out that the event never happened. The AI wasn't trying to lie; it was just following patterns without checking reality.

Another common problem is outdated knowledge. If an AI was trained on information from several years ago, it might give you answers about current events, recent discoveries, or new technology that are no longer accurate. You could end up with information that was true once but isn't anymore.

The solution isn't to avoid AI—it's to be thoughtful. For important facts, dates, or claims, cross-check what AI tells you with reliable sources like your library database, textbooks, or established websites. This habit protects your work and builds stronger research skills.
```



**meta-llama/llama-3.3-70b-instruct — ok, 163 words, 12.511 s; caution markers 0, confident markers 0:**

```text
As we increasingly rely on artificial intelligence (AI) for information and answers, it's essential to understand the importance of verifying AI-generated content. AI systems can process vast amounts of data and generate text quickly, but this doesn't mean the information is always accurate. In fact, AI often produces probable text based on patterns and associations, rather than verified facts.

For instance, an AI might invent a fake citation or claim that a certain event occurred on a specific date, even if it didn't. Another example is when AI provides outdated knowledge, such as recommending a treatment for a medical condition that has since been discredited. This matters because students might use such information in their research or reports, only to find that it's incorrect or outdated.

So it's wise to check important claims from AI against reliable sources, especially for facts, dates, and references. By doing so, we can ensure the accuracy and credibility of the information we use and avoid spreading misinformation.
```



**Required version comparison (Model A; draft scores 0–2):**

| Criterion | V1 without examples | V2 with one example | V3 with several examples | Comment |
| --- | --- | --- | --- | --- |
| Topic relevance | 2 | 2 | 2 | All three address verification of AI answers. |
| Audience clarity | 2 | 2 | 2 | All name grades 9–10; V1 is incomplete. |
| Structure | 1 | 2 | 2 | V1 ends mid-sentence; V2 and V3 contain the requested parts. |
| Specificity | 1 | 1 | 1 | V2 and V3 name failure types, but neither gives a detailed verifiable case. |
| Style | 2 | 2 | 2 | All use an educational tone; audience fit is clearer in the structured prompts. |
| Cautious wording | 1 | 2 | 2 | V2 and V3 explicitly advise checking important claims. |
| No copying from examples | Not applicable | 2 | 2 | No literal copying detected; the invented-citation example remains a priming risk. |

These are draft human judgments, not scores emitted by the API. Model B’s V2 cell is unavailable because its request failed with HTTP 502.


Model A’s V3 answer has 214 words and meets the target. It uses two explained failure types (plausible invented details and stale information), a cautious conclusion, and does not repeat the named example citation from the few-shot block. Model B’s V3 answer has 163 words, below target, although it contains a fake-citation example and a stale-knowledge example. On this run, V3 is the strongest answer from Model A against the word and structure requirements; it is not proof that V3 or Model A is universally best. The prompt contains three short teaching examples, but the intentionally fake citation could prime imitation and should be removed or explicitly labeled as a non-reusable placeholder in future work.


## 12. Task 9: Analysis of few-shot effects

| Version / model | Words | Latency (s) | Caution / confident | Outcome |
| --- | --- | --- | --- | --- |
| V1 | anthropic/claude-haiku-4.5 | 95 | 4.346 | 1 / 0 | ok |
| V1 | meta-llama/llama-3.3-70b-instruct | 166 | 30.385 | 0 / 0 | ok |
| V2 | anthropic/claude-haiku-4.5 | 203 | 5.304 | 1 / 0 | ok |
| V2 | meta-llama/llama-3.3-70b-instruct | 0 | 77.191 | 0 / 0 | error |
| V3 | anthropic/claude-haiku-4.5 | 214 | 4.651 | 1 / 1 | ok |
| V3 | meta-llama/llama-3.3-70b-instruct | 163 | 12.511 | 0 / 0 | ok |


1. V2 used the student-learning example; V3 used examples for specificity, explaining relevance, and a cautious conclusion.
2. They target concrete writing skills rather than copy the final topic.
3. The examples were intended to teach specificity, explanation, and calibrated conclusions.
4. Model A’s output grew from 95 words (V1) to 203 (V2); Model B’s V2 call failed.
5. Model A’s V3 answer reached 214 words and included two explained risk types; Model B’s answer was 163 words.
6. Yes. The fabricated citation in V3 is a priming risk; neither V3 answer copied its title verbatim.
7. Compare word count, structure, concrete examples, overlap with example wording, and both model outputs.
8. The example that links an example to why it matters is likely most useful, but this is an analytical judgment, not a measured causal effect.
9. The citation example could be removed because it conflicts with the no-fabrication constraint and may prime invented citations.
10. Use neutral, clearly hypothetical examples and add a checklist for the nine quality criteria.



Assignment example analysis table

| Example | What it should show | Helped / did not help | Why |
| --- | --- | --- | --- |
| Example 1: concrete argument | Turn a vague claim into a specific illustration. | Partly helped | The V3 essay describes invented event details, but does not give a verifiable concrete case; the fake-citation example also risks priming. |
| Example 2: explain relevance | Connect the example to why it matters to a student. | Helped | Model A explains that a student could copy false details into an essay and be corrected by a teacher. |
| Example 3: cautious conclusion | Avoid an absolute conclusion and recommend proportionate checking. | Helped | The V3 answer recommends checking important claims against reliable sources instead of rejecting AI entirely. |


## 13. Task 10: Edge-case tests

Five edge checks were run with Model A. Each prompt and output is saved in the run JSON. The audience-change request included the preceding Model A V3 essay, so the follow-up had its necessary context.



| Check | What was changed | What the model did | Problem that appeared | How to improve the prompt |
| --- | --- | --- | --- | --- |
| too_general_topic | Too general topic - model may give generic response | ok: The answer becomes a broad overview of AI applications instead of a focused mini-essay about verification. | It follows the deliberately broad request but does not preserve the lab's narrower task; name the reader and intended format. | Add the intended audience, genre, central question, and two required examples. |
| hallucination_risk | Risk of fabricated facts - ask for specific citations | ok: The response returned three references. Two had incorrect author/year attributions: DOI 10.1145/3571730 is Ji et al. (2023), not Rawte et al.; arXiv:2005.00661 is Maynez et al. (2020), not Zhang et al. (2023). A third Ji et al. citation repeated the first DOI. | The answer produced plausible-looking citations, including incorrect author/year metadata. The two records were checked against the [ACM DOI record](https://doi.org/10.1145/3571730) and the [official arXiv record](https://arxiv.org/abs/2005.00661). | Check every title, author list, year, and DOI against the publisher or repository record; do not infer verification from a valid-looking DOI. |
| audience_change | Change audience - adapt for parents instead of students | ok: The answer is rewritten for parents using the supplied preceding essay as context. | The context is now explicit and the model can adapt it; inspect whether tone and examples actually change for parents. | Name the parents' needs and request one concrete parent-facing example. |
| conflicting_requirements | Conflicting requirements - detailed but very short | ok: The model has to balance a request for detail with a two-sentence maximum. | The output is concise; the length constraint necessarily limits the number of explanations. | Prioritize the sentence limit and ask for one compact example, or remove the conflicting demand for detail. |
| strict_json_format | Strict JSON format requirement | ok: The parser confirms valid JSON and all five required keys. | Valid JSON does not establish factual accuracy. | Parse the JSON, then check its claims separately. |


Manual citation check: The hallucination-risk response included two mismatched author/year attributions; one DOI correctly identifies Ji et al. (2023), while the other identifies Maynez et al. (2020). The cited records are linked in the edge-case table.

Strict JSON result: valid JSON with all five required keys. The parser strips the code fence before validation. The request failure in Model B’s V2 cell is retained and excluded from quality comparisons.


## 14. Task 11: Independent review by Model B

Model B received the original task, audience and context, all nine criteria, the full V3 prompt, and Model A’s final V3 answer in a separate request. The response contained a fenced JSON object and extra prose. The report parser recovered the first valid JSON object; the full raw reviewer response is retained in the result record. The reviewer assigned 2/2 to every criterion, found no hallucinations, and said the conclusion could explain cross-checking in more detail. This review is advisory and is not independent fact verification.




**Assignment reviewer table:**

| Criterion | Second model score 0–2 | Second model comment | Agree / disagree | My comment |
| --- | --- | --- | --- | --- |
| Task relevance | 2 | The response directly addresses the topic of why AI answers need verification. | Draft: partly agree | The essay stays on topic; student to confirm. |
| Audience clarity | 2 | The language used is clear and understandable for 9-10th grade students. | Draft: agree | The language is accessible; student to confirm. |
| Structure | 2 | The response has a logical structure, including an introduction, main point, examples, explanations, and conclusion. | Draft: agree | The answer has an opening, examples, and conclusion. |
| Specificity | 2 | The response includes two concrete examples of AI failures: inventing information and outdated knowledge. | Draft: partly disagree | The 2/2 seems generous: the examples describe types of failure but remain broad. |
| Use of few-shot examples | — | No separate numeric score was returned. | Draft: not enough evidence | The reviewer returned a separate copying field, not a score for example usefulness. |
| No copying from examples | — | few_shot_copying: none | Draft: partly agree | No literal copying was identified, but the invented-citation example could prime imitation. |
| Factual care | 2 | No fabricated facts, quotes, sources, or dates are present in the response. | Draft: partly agree | No citations or dates appear in the final essay; this does not verify every general claim. |
| Style | 2 | The tone is calm, educational, and appropriately cautious throughout the response. | Draft: agree | The tone is calm and suitable for the stated audience. |
| Overall usability | 2 | The text is usable after minor manual editing, with no major revisions needed. | Draft: partly agree | It meets the word range but still needs human fact and audience review. |

Scores and agreement statements above are a proposed draft for the student to review. A dash means the model did not return a numeric score for that criterion; no score was inferred.


**Expanded reviewer scores from the saved review response:**

| Criterion | Model B | Reviewer comment | Draft self-score | Agreement |
| --- | --- | --- | --- | --- |
| Topic relevance | 2 | The response directly addresses the topic of why AI answers need verification. | 2 | Student to confirm |
| Audience clarity | 2 | The language used is clear and understandable for 9-10th grade students. | 2 | Student to confirm |
| Logical structure | 2 | The response has a logical structure, including an introduction, main point, examples, explanations, and conclusion. | 2 | Student to confirm |
| At least two concrete examples | 2 | The response includes two concrete examples of AI failures: inventing information and outdated knowledge. | 1 | Student to confirm |
| Factual care | 2 | No fabricated facts, quotes, sources, or dates are present in the response. | 2 | Student to confirm |
| Appropriate and cautious style | 2 | The tone is calm, educational, and appropriately cautious throughout the response. | 2 | Student to confirm |
| 180–220 word length | 2 | The response is within the 180-220 word limit. | 2 | Student to confirm |
| Conclusion adds no new arguments | 2 | The conclusion does not introduce new arguments and is cautious in its wording. | 2 | Student to confirm |
| Usable after minor editing | 2 | The text is usable after minor manual editing, with no major revisions needed. | 1 | Student to confirm |


**Draft reflection for the student to confirm:** I agree that the essay is clear and appropriately cautious, and that the final paragraph could say more about how to cross-check claims. I would not accept the reviewer’s blanket 2/2 without qualification: the examples are concrete in type but not especially specific, and the result still needs a human check for factual accuracy and audience fit. These statements are proposed wording, not a record of the student’s personal view.


## 15. Task 12: Final Prompt Card

| Field | Content |
| --- | --- |
| Prompt name | Evidence-aware student essay about checking AI answers |
| Task the prompt is used for | Write a mini-essay for 9-10th grade students explaining why AI answers need verification, with two concrete examples and a cautious conclusion |
| Target audience | 9-10th grade students (ages 14-16) |
| Recommended model | anthropic/claude-haiku-4.5 for this measured run; not a universal recommendation. |
| Input | Task and optional source material to verify |
| Expected result | 180–220 word mini-essay with introduction, thesis, two explained examples and cautious conclusion |
| Model role | Educational writer for teen digital literacy |
| Core requirements | Plain language, two failure examples, explain relevance, distinguish prediction from verified fact |
| Restrictions | No invented facts, quotations, sources, dates, statistics, or categorical claims |
| Output format | Plain-text paragraphs |
| Few-shot examples | One non-topic-specific learning example plus three short style/argument patterns |
| What the few-shot examples demonstrate | Specificity, explanation of relevance, and a cautious conclusion |
| Quality criteria | Topic relevance; Audience clarity; Logical structure; At least two concrete examples; Factual care; Appropriate and cautious style; 180–220 word length; Conclusion adds no new arguments; Usable after minor editing |
| Potential model errors | Fabricated citations or references; Invented statistics or precise numbers without basis; Overconfident claims without qualification; Condescending or overly complex language for the audience; Missing required structural elements; Exceeding or significantly under word count |
| How to check the result | Count words, score the criteria, and verify factual claims and citations manually |
| When not to use the prompt | The task requires current facts or real citations that cannot be independently verified |

**Final prompt:**

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


## 16. Task 13: Final text and edit disclosure

The text below is Model A’s raw V3 answer, reproduced without editorial changes. Its measured length is 214 words. Its position is that AI should be used thoughtfully and important claims should be checked; it has an introduction, a main point, two explained examples, and a conclusion.

```text
# Why You Should Verify AI Answers

You've probably used AI to help with homework or answer questions. It's fast and often helpful. But here's something important: AI doesn't actually "know" facts the way you do. Instead, it predicts the next word based on patterns it learned during training, which means it can sound confident while being completely wrong.

AI sometimes invents information that sounds plausible but doesn't exist. For example, an AI might describe a historical event with specific details—names, dates, locations—that seem real but are actually made up. A student might copy these details into an essay, only to have a teacher point out that the event never happened. The AI wasn't trying to lie; it was just following patterns without checking reality.

Another common problem is outdated knowledge. If an AI was trained on information from several years ago, it might give you answers about current events, recent discoveries, or new technology that are no longer accurate. You could end up with information that was true once but isn't anymore.

The solution isn't to avoid AI—it's to be thoughtful. For important facts, dates, or claims, cross-check what AI tells you with reliable sources like your library database, textbooks, or established websites. This habit protects your work and builds stronger research skills.
```

| Manual change | Reason |
| --- | --- |
| None | The report reproduces the stored model answer; translation is not presented as model output. |


## 17. Task 14: Conclusions

1. The simple prompt only names the topic; V3 specifies role, audience, structure, constraints, output format and examples.
2. The most useful elements in this run were the audience, explicit structure, word range, and prohibition on invented sources.
3. The educational-writer role framed the voice, but its separate effect was not isolated.
4. The audience instruction makes the intended reader explicit; it cannot guarantee perfect age-level fit.
5. Model A’s V2 output met the word target while V1 did not; the B V2 request failed.
6. Model A’s V3 answer also met the word target; Model B’s was shorter. One run is not enough for a general model ranking.
7. A fabricated citation in the examples could distract or prime copying; no literal copying was found in V3.
8. Copying was checked by comparing distinctive example wording with the generated answers; this is a qualitative check.
9. Claude Haiku performed better on the word-count target in this run; Llama’s V2 call failed and its V1/V3 answers were short.
10. Good few-shot examples teach one transferable skill, stay short, avoid conflicting with the constraints, and are checked for copying.

Interpretation limit: These findings describe one small run at one endpoint and setting; they do not establish general model superiority or causal few-shot effects.


## Appendix A: Run summary

| Request | Model | Status | Words | Latency s | Finish |
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



All full prompts and raw responses, including the failed request and reviewer response, are preserved in the run folder.
