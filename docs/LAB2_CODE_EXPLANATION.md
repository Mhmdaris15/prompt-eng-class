# Lab 2: Prompt Engineering Fundamentals — Code Explanation

## Overview

This document provides a comprehensive explanation of the Lab 2 implementation for the Prompt Engineering course at ITMO University. The code implements all 11 tasks from the laboratory specification, focusing on systematic prompt engineering techniques, quality evaluation, and comparative model analysis.

---

## Architecture

```
lab2/
├── __init__.py              # Package initialization
├── source_text.py           # Controlled technical text + experiment definitions
├── common.py                # Shared utilities: config, client, metrics, export
└── runner.py                # Main orchestrator implementing all 11 tasks
```

### Design Principles

1. **Separation of Concerns**: Source text, configuration, client logic, and experiment orchestration are in separate modules
2. **Reproducibility**: Every experiment is tracked with timestamps, model names, prompt versions, and full metrics
3. **Batch-Preserving Error Handling**: Failures are recorded as result rows with error status, not exceptions that halt execution
4. **Model-Aware Token Management**: Special handling for Kimi models that consume reasoning tokens internally
5. **Comprehensive Metrics**: Automated extraction of linguistic and structural features for quantitative analysis

---

## Module: `source_text.py`

### Purpose
Provides the controlled experimental input — a technical text about AI verification — along with all experiment definitions (topic, task, audience, quality criteria, undesirable errors).

### Key Components

#### `SOURCE_TEXT` (str)
A ~1,200-word technical article covering:
- How LLMs actually work (probabilistic text generation)
- Common failure modes (hallucination, knowledge cutoff, context limits, sycophancy)
- Verification strategies (source grounding, cross-reference, uncertainty markers, RAG, decomposition, calibration)
- Practical guidelines for students

**Why this text?** It's self-referential (about AI verification), contains verifiable and unverifiable claims, and is the right length (1-2 pages) for summarization and Q&A tasks.

#### Experiment Definitions

| Constant | Purpose |
|----------|---------|
| `TOPIC` | "Why AI answers need verification" |
| `TASK` | "Write a mini-essay for 9-10th grade students explaining why AI answers need verification, with two concrete examples and a cautious conclusion" |
| `AUDIENCE` | "9-10th grade students (ages 14-16)" |
| `CONTEXT` | "Educational content for a computer science or digital literacy class" |
| `GOOD_RESULT_CRITERIA` | 9 criteria for quality evaluation |
| `UNDESIRABLE_ERRORS` | 6 error types to detect |

---

## Module: `common.py`

### Purpose
Shared infrastructure: configuration, Cloud.ru API client, metrics computation, and data export.

### Class: `Lab2Config`

Configuration dataclass with environment-based initialization.

```python
@dataclass
class Lab2Config:
    api_key: str                          # From API_KEY env var
    base_url: str = "https://foundation-models.api.cloud.ru/v1"
    primary_model: str = "moonshotai/Kimi-K2.6"
    secondary_model: str = "google/gemini-3.1-pro-preview"
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 120
    output_dir: str = "results/lab2"
    
    @classmethod
    def from_env(cls) -> "Lab2Config":
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY not found in environment. Check .env file.")
        return cls(api_key=api_key)
```

**Key Design Decision**: Uses `from_env()` classmethod for clean dependency injection and testability.

### Class: `CompletionResult`

Dataclass capturing everything about a single model response.

```python
@dataclass
class CompletionResult:
    # Identification
    model: str
    prompt_name: str
    prompt: str
    answer: str
    status: str              # "ok", "error", "truncated"
    error: str = ""
    
    # Performance
    latency_sec: float = 0.0
    answer_length: int = 0
    finish_reason: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Automated Metrics
    links_count: int = 0
    years_count: int = 0
    numbers_count: int = 0
    caution_markers_count: int = 0
    confident_markers_count: int = 0
```

**Status Values**:
- `"ok"` — Normal completion
- `"truncated"` — `finish_reason == "length"` (hit token limit)
- `"error"` — API exception occurred

### Class: `Lab2Client`

OpenAI-compatible client wrapper with model-aware token budget handling.

#### `complete()` — Core Completion Logic

```python
def complete(
    self,
    model: str,
    prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None
) -> CompletionResult:
```

**Kimi-Specific Handling** (lines 105-130):
```python
# Model-aware token budget: Kimi uses reasoning tokens internally
effective_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
if "kimi" in model.lower() or "moonshotai" in model.lower():
    effective_max_tokens = max(effective_max_tokens, 4096)

# Try with thinking disabled for Kimi models
extra_params = {}
if "kimi" in model.lower() or "moonshotai" in model.lower():
    extra_params["extra_body"] = {"thinking": {"type": "disabled"}}
```

**Why this matters**: Cloud.ru's Kimi deployment includes internal reasoning tokens in the completion budget. Without `thinking: {"type": "disabled"}`, the model spends tokens on hidden reasoning, leaving fewer for visible output → `finish_reason: "length"` with truncated/empty responses.

**Fallback Strategy** (lines 135-185): If the `extra_body` parameter fails (API doesn't support it), retry without it. This ensures compatibility across different API versions.

#### `complete_with_metrics()` — Instrumented Completion

```python
def complete_with_metrics(
    self,
    model: str,
    prompt_name: str,
    prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None
) -> CompletionResult:
```

Calls `complete()`, then computes all automated metrics on the response.

### Metrics Functions

| Function | Pattern | Purpose |
|----------|---------|---------|
| `count_links()` | `https?://\S+` | Detect fabricated URLs |
| `count_years()` | `\b(19\|20)\d{2}\b` | Detect fabricated dates |
| `count_numbers()` | `\b\d+[\d.,]*\b` | Detect fabricated statistics |
| `count_caution_markers()` | 25 Russian/English markers | Measure appropriate uncertainty |
| `count_confident_markers()` | 16 Russian/English markers | Measure overconfidence |

**Caution Markers** (Russian): `возможно`, `вероятно`, `нужно проверить`, `недостаточно данных`, `зависит от`, `требуется проверка`, `может быть`, `предположительно`, `примерно`, `ориентировочно`, `не уверен`, `не гарантирую`, `может отличаться`

**Caution Markers** (English): `possibly`, `probably`, `need to verify`, `need to check`, `insufficient data`, `depends on`, `verification required`, `may be`, `approximately`, `roughly`, `not certain`, `cannot guarantee`, `might differ`

**Confident Markers** (Russian): `точно`, `однозначно`, `безусловно`, `гарантирую`, `фактически`, `доказано`, `установлено`, `известно`

**Confident Markers** (English): `definitely`, `certainly`, `absolutely`, `guaranteed`, `factually`, `proven`, `established`, `known for certain`

### Export Functions

| Function | Output | Encoding |
|----------|--------|----------|
| `save_results_csv()` | `lab2_results.csv` | `utf-8-sig` (Excel-compatible) |
| `save_results_json()` | `lab2_results.json` | UTF-8 |
| `create_manifest()` | `manifest.json` | UTF-8 |
| `compute_file_hash()` | SHA-256 | — |

**Manifest Contents**:
- Experiment metadata (timestamp, config)
- Source text hash (reproducibility)
- Runner script hash (code version)
- Summary statistics
- Models and prompts tested

---

## Module: `runner.py`

### Class: `Lab2Runner`

Main orchestrator implementing all 11 laboratory tasks.

```python
class Lab2Runner:
    def __init__(self, config: Lab2Config):
        self.config = config
        self.client = Lab2Client(config)
        self.results: List[CompletionResult] = []
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Experiment tracking
        self.prompts: Dict[str, str] = {}
        self.prompt_versions: Dict[str, Dict[str, Any]] = {}
        self.evaluation_results: List[Dict[str, Any]] = []
```

### Task Implementations

#### Task 1: Topic Selection & Quality Criteria (`_task1_topic_selection`)

Documents the experimental setup in `task1_topic_criteria.json`:
- Topic, task, audience, context
- 9 quality criteria
- 6 undesirable errors

**No API calls** — pure documentation.

#### Task 2: Simple Prompt Baseline (`_task2_simple_prompt`)

```python
simple_prompt = f"Write a short essay about {TOPIC.lower()} for students."
```

Tests both models with minimal prompt. Establishes baseline for comparison.

#### Task 3: V1 Improved Prompt (`_task3_v1_prompt`)

Full structured prompt with:
- **Role**: "educational content writer specializing in digital literacy for teenagers"
- **Task**: Write mini-essay for 9-10th graders
- **Structure**: 5 required sections (intro, main point, 2 examples + explanations, conclusion)
- **Constraints**: Tone, length (180-220 words), no fabrication, no categorical language
- **Format**: Plain text paragraphs

**Prompt Version Tracking**: Records components in `prompt_versions["v1"]`.

#### Task 4: Few-Shot Examples Design (`_task4_few_shot_examples`)

Creates and saves contrasting examples:

**Bad Example** (saved as `bad_example`):
> "AI is useful for everyone because it makes life easier and helps with many tasks."

**Why weak**: Too general, no concrete situation, no conditional phrasing, reads like a slogan.

**Good Example** (saved as `good_example`):
> "AI can help a student understand a difficult concept if used as an explanation assistant rather than a way to just get the answer. For example, asking 'Can you explain how photosynthesis works step by step?' is more useful than asking 'What is the answer to question 5?'"

**Why strong**: Specific situation, conditional phrasing ("if used as..."), contrasts good vs bad usage, appropriate caution.

Saved to `task4_few_shot_examples.json`.

#### Task 5: V2 One-Shot Prompt (`_task5_v2_one_shot`)

V1 + one good few-shot example showing desired specificity level.

```python
v2_prompt = f"""...V1 prompt...

Aim for this level of specificity:

Weak formulation:
AI helps people learn.

Better formulation:
{good_example}

Format: Plain text paragraphs."""
```

#### Task 6: V3 Few-Shot Prompt (`_task6_v3_few_shot`)

V1 + three few-shot examples targeting specific skills:

```python
few_shot_examples = """Examples of desired style:

Example 1 - Concrete argument:
Weak: AI can make mistakes.
Better: An AI might invent a fake citation like "Smith et al. 2023, 'Quantum Computing Breakthrough'" — a paper that doesn't exist but looks real.

Example 2 - Explaining an example:
Weak: This is bad because it's wrong.
Better: This matters because a student might use that fake citation in a report, and the teacher would find no such paper.

Example 3 - Cautious conclusion:
Weak: So never trust AI.
Better: So it's wise to check important claims from AI against reliable sources, especially for facts, dates, and references."""
```

Each example teaches a specific skill: concreteness, explanation, cautious conclusion.

#### Task 7: Few-Shot Analysis (`_task7_few_shot_analysis`)

Compares V1, V2, V3 quantitatively across both models:

```python
analysis["comparison"][version][model] = {
    "length": r.answer_length,
    "latency_sec": r.latency_sec,
    "caution_markers": r.caution_markers_count,
    "confident_markers": r.confident_markers_count,
    "links": r.links_count,
    "years": r.years_count,
    "numbers": r.numbers_count,
    "finish_reason": r.finish_reason
}
```

Saved to `task7_few_shot_analysis.json`.

#### Task 8: Edge Case Testing (`_task8_edge_cases`)

Five stress tests:

| Case | Description | Check |
|------|-------------|-------|
| `too_general_topic` | "Write about artificial intelligence." | Generic response |
| `hallucination_risk` | Ask for 3 specific papers with DOIs | Fabricated citations |
| `audience_change` | Rewrite for parents instead of students | Audience adaptation |
| `conflicting_requirements` | Detailed but ≤2 sentences | Conflict resolution |
| `strict_json_format` | Exact JSON structure required | JSON validity |

Each tested on both models. Results in `task8_edge_cases.json`.

#### Task 9: Second Model Evaluation (`_task9_second_model_evaluation`)

Cross-model evaluation: each model evaluates the other's V3 output.

**Evaluation Prompt Structure**:
1. Original task + criteria
2. Final prompt used
3. Model response
4. Request: Score 8 criteria (0-2), check few-shot copying, hallucinations, strongest/weakest aspects

**Bidirectional**: Primary evaluates secondary, secondary evaluates primary.

**Temperature**: 0.1 for consistent evaluation.

Saved to `task9_evaluations.json`.

#### Results Saving (`_save_all_results`)

Generates all output files:

| File | Purpose |
|------|---------|
| `lab2_results.csv` | Main results table |
| `lab2_results_with_metrics.csv` | Same with metrics (for analysis) |
| `lab2_results.json` | Full structured data |
| `prompts_used.json` | All prompts by name |
| `prompt_versions.json` | Prompt evolution tracking |
| `manifest.json` | Experiment metadata + hashes |
| `task1_topic_criteria.json` | Task 1 documentation |
| `task4_few_shot_examples.json` | Few-shot examples |
| `task7_few_shot_analysis.json` | Quantitative comparison |
| `task8_edge_cases.json` | Edge case results |
| `task9_evaluations.json` | Cross-model evaluations |

---

## Execution Flow

```
main()
  └── Lab2Runner(config).run_all()
        ├── _task1_topic_selection()          → task1_topic_criteria.json
        ├── _task2_simple_prompt()            → 2 API calls
        ├── _task3_v1_prompt()                → 2 API calls
        ├── _task4_few_shot_examples()        → task4_few_shot_examples.json
        ├── _task5_v2_one_shot()              → 2 API calls
        ├── _task6_v3_few_shot()              → 2 API calls
        ├── _task7_few_shot_analysis()        → task7_few_shot_analysis.json
        ├── _task8_edge_cases()               → 10 API calls (5 cases × 2 models)
        ├── _task9_second_model_evaluation()  → 2-4 API calls
        └── _save_all_results()               → All CSV/JSON outputs
```

**Total API Calls**: ~18-22 per full run (depending on evaluation success)

---

## Key Technical Decisions

### 1. Kimi Reasoning Token Handling

**Problem**: Cloud.ru's Kimi-K2.6 includes hidden reasoning tokens in `completion_tokens`. With default 2000 token limit, reasoning consumes budget → truncated output.

**Solution**: 
- Detect Kimi models by name (`"kimi"` or `"moonshotai"`)
- Increase `max_tokens` to minimum 4096
- Send `extra_body={"thinking": {"type": "disabled"}}` to disable reasoning
- Fallback gracefully if API rejects the parameter

### 2. Batch-Preserving Error Handling

```python
try:
    response = self.client.chat.completions.create(...)
except Exception as e:
    # Return CompletionResult with status="error", not raise
    return CompletionResult(status="error", error=str(e), ...)
```

**Why**: A single failed request shouldn't lose all other results. Failed requests appear in CSV with error details for post-hoc analysis.

### 3. Dual CSV Output

- `lab2_results.csv` — Standard results
- `lab2_results_with_metrics.csv` — Identical but named for analysis pipeline clarity

### 4. Manifest with Hashes

```python
source_hash = hashlib.sha256(SOURCE_TEXT.encode()).hexdigest()
runner_hash = compute_file_hash(__file__)
```

Enables exact reproduction verification: if source text or runner code changes, hashes differ.

### 5. Structured Evaluation (Task 9)

Uses JSON output format for machine-parseable evaluation:
```json
{
  "scores": {"topic_adherence": 2, "audience_clarity": 2, ...},
  "few_shot_copying": "none|partial|heavy",
  "hallucinations_found": [],
  "strongest_aspect": "...",
  "weakest_aspect": "...",
  "overall_assessment": "..."
}
```

---

## Configuration

### Environment Variables (`.env`)

```bash
API_KEY=your_cloud_ru_api_key
LAB_MODEL_A=moonshotai/Kimi-K2.6
LAB_MODEL_B=Qwen/Qwen3-Coder-Next
```

### Command-Line Arguments

```bash
python -m lab2.runner \
    --primary-model moonshotai/Kimi-K2.6 \
    --secondary-model Qwen/Qwen3-Coder-Next \
    --temperature 0.3 \
    --max-tokens 2000 \
    --output-dir results/lab2
```

---

## Output Data Schema

### `lab2_results.csv` Columns

| Column | Type | Description |
|--------|------|-------------|
| model | string | Model identifier |
| prompt_name | string | Task identifier (simple, v1, v2, v3, edge_*, evaluation) |
| prompt | string | Full prompt text |
| answer | string | Model response |
| status | string | ok / error / truncated |
| error | string | Error message if status=error |
| latency_sec | float | Request latency |
| answer_length | int | Character count |
| finish_reason | string | stop / length / error |
| prompt_tokens | int | Input tokens |
| completion_tokens | int | Output tokens |
| total_tokens | int | Total tokens |
| timestamp | ISO8601 | Request timestamp |
| links_count | int | HTTP/HTTPS URLs detected |
| years_count | int | Years (19xx, 20xx) detected |
| numbers_count | int | Numeric values detected |
| caution_markers_count | int | Uncertainty markers |
| confident_markers_count | int | Certainty markers |

---

## Extending the Framework

### Adding a New Prompt Version

1. Add method `_taskN_new_version()` in `Lab2Runner`
2. Define prompt in method
3. Register in `self.prompts` and `self.prompt_versions`
4. Call `self.client.complete_with_metrics()` for each model
5. Append to `self.results`
6. Add to `_save_all_results()` if new output files needed

### Adding a New Metric

1. Add function in `common.py` (e.g., `count_questions(text)`)
2. Add field to `CompletionResult` dataclass
3. Compute in `complete_with_metrics()`
4. Automatically included in CSV/JSON export

### Adding a New Model

1. Update `Lab2Config` defaults or pass via CLI
2. If model has special token handling, extend `complete()` logic
3. No other changes needed — framework is model-agnostic

---

## Troubleshooting

### Kimi Returns Empty/Truncated Responses

**Symptoms**: `status="truncated"`, `finish_reason="length"`, `answer_length=0` or very small

**Causes & Fixes**:
1. Reasoning tokens consuming budget → Ensure `thinking: {"type": "disabled"}` is sent
2. Token limit too low → Increase `max_tokens` to 4096+
3. API doesn't support `extra_body` → Fallback handles this automatically

### JSON Parse Errors in Evaluation

**Symptom**: `parse_error: true` in `task9_evaluations.json`

**Cause**: Evaluator model didn't return valid JSON

**Fix**: Lower temperature (0.1), add "Return ONLY valid JSON" instruction, or implement retry with repair.

### Rate Limiting / Timeouts

**Symptom**: `status="error"` with connection/timeout errors

**Fix**: Increase `timeout` in config, add retry logic with exponential backoff.

---

## Relationship to Lab 1

| Aspect | Lab 1 | Lab 2 |
|--------|-------|-------|
| Focus | Summarization, Q&A, format compliance, hallucination detection | Prompt engineering progression, few-shot, evaluation |
| Models | 2 models, 7 experiments × 2 = 14 runs | 2 models, ~18-22 runs |
| Metrics | Length, latency, numbers, years, links, caution/confident | Same + finish_reason, token usage |
| Output | `results.csv`, `results_with_metrics.csv` | `lab2_results.csv`, `lab2_results_with_metrics.csv` |
| Report | `reports/lab1/LAB1_REPORT.md` | `reports/lab2/LAB2_REPORT.md` (to be generated) |
| Defense | `DEFENSE_GUIDE_LAB1.md` + EN | `DEFENSE_GUIDE_LAB2.md` + EN (to be generated) |

---

## Next Steps

After successful execution:
1. Run `python -m lab2.runner` to generate all outputs
2. Review `lab2_results.csv` for quality patterns
3. Generate `reports/lab2/LAB2_REPORT.md` with findings
4. Create `DEFENSE_GUIDE_LAB2.md` (RU + EN)
5. Prepare manual evaluation files:
   - `hallucination_verification.csv` — fact-check each output
   - `quality_scores.csv` — human scores on 9 criteria

---

*Generated as part of ITMO University Prompt Engineering Laboratory Work 2*