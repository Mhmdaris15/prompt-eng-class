"""
Lab 2 Runner
============
Main execution script for Lab 2: Prompt Engineering Fundamentals and Quality Analysis.

Implements all 11 tasks from the lab specification:
1. Topic selection and quality criteria
2. Simple prompt baseline
3. V1: Improved prompt with role, task, audience, constraints
4. Few-shot examples (bad and good)
5. V2: One-shot prompt
6. V3: Few-shot prompt with multiple examples
7. Few-shot analysis
8. Edge case testing
9. Second model evaluation
10. Results export and report generation
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lab2.common import (
    Lab2Config, Lab2Client, CompletionResult,
    save_results_csv, save_results_json, create_manifest, save_manifest,
    compute_file_hash
)
from lab2.source_text import (
    SOURCE_TEXT, TOPIC, TASK, AUDIENCE, CONTEXT,
    GOOD_RESULT_CRITERIA, UNDESIRABLE_ERRORS
)


def parse_evaluation_response(text: str) -> Dict[str, Any]:
    """Extract the first valid JSON object from a reviewer response."""
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise json.JSONDecodeError("No JSON object found in reviewer response", text, 0)


class Lab2Runner:
    """Orchestrates all Lab 2 experiments."""
    
    def __init__(self, config: Lab2Config):
        self.config = config
        self.output_dir = Path(config.output_dir)
        if self.output_dir.exists():
            raise FileExistsError(f"Output directory already exists: {self.output_dir}")
        self.client = Lab2Client(config)
        self.output_dir.mkdir(parents=True, exist_ok=False)
        self.results: List[CompletionResult] = []
        
        # Experiment tracking
        self.prompts: Dict[str, str] = {}
        self.prompt_versions: Dict[str, Dict[str, Any]] = {}
        self.evaluation_results: List[Dict[str, Any]] = []
    
    def run_all(self) -> List[CompletionResult]:
        """Run all Lab 2 tasks."""
        self._validate_selected_models()
        print("=" * 60)
        print("LAB 2: Prompt Engineering Fundamentals")
        print("=" * 60)
        
        # Task 1: Topic and criteria (documented in source_text.py)
        self._task1_topic_selection()
        
        # Task 2: Simple prompt baseline
        self._task2_simple_prompt()
        
        # Task 3: V1 improved prompt
        self._task3_v1_prompt()
        
        # Task 4: Few-shot examples
        self._task4_few_shot_examples()
        
        # Task 5: V2 one-shot prompt
        self._task5_v2_one_shot()
        
        # Task 6: V3 few-shot prompt
        self._task6_v3_few_shot()
        
        # Task 7: Few-shot analysis
        self._task7_few_shot_analysis()
        
        # Task 8: Edge case testing
        self._task8_edge_cases()
        
        # Task 9: Second model evaluation
        self._task9_second_model_evaluation()
        
        # Save all results
        self._save_all_results()
        
        return self.results

    def _validate_selected_models(self) -> None:
        available = set(self.client.list_models())
        requested = [self.config.primary_model, self.config.secondary_model]
        missing = [model for model in requested if model not in available]
        if missing:
            raise ValueError("Selected model(s) unavailable at the configured endpoint: " + ", ".join(missing))
    
    def _task1_topic_selection(self):
        """Task 1: Document topic selection and quality criteria."""
        print("\n[Task 1] Topic Selection & Quality Criteria")
        print(f"  Topic: {TOPIC}")
        print(f"  Task: {TASK}")
        print(f"  Audience: {AUDIENCE}")
        print(f"  Context: {CONTEXT}")
        print(f"  Quality Criteria ({len(GOOD_RESULT_CRITERIA)}):")
        for i, criterion in enumerate(GOOD_RESULT_CRITERIA, 1):
            print(f"    {i}. {criterion}")
        print(f"  Undesirable Errors ({len(UNDESIRABLE_ERRORS)}):")
        for i, error in enumerate(UNDESIRABLE_ERRORS, 1):
            print(f"    {i}. {error}")
        
        # Save topic info
        topic_info = {
            "topic": TOPIC,
            "task": TASK,
            "audience": AUDIENCE,
            "context": CONTEXT,
            "quality_criteria": GOOD_RESULT_CRITERIA,
            "undesirable_errors": UNDESIRABLE_ERRORS
        }
        with open(self.output_dir / "task1_topic_criteria.json", "w", encoding="utf-8") as f:
            json.dump(topic_info, f, ensure_ascii=False, indent=2)
    
    def _task2_simple_prompt(self):
        """Task 2: Simple prompt baseline."""
        print("\n[Task 2] Simple Prompt Baseline")
        
        simple_prompt = f"Write a short essay about {TOPIC.lower()} for students."
        self.prompts["simple"] = simple_prompt
        
        model = self.config.primary_model
        print(f"  Testing {model}...")
        result = self.client.complete_with_metrics(model=model, prompt_name="simple", prompt=simple_prompt)
        self.results.append(result)
        print(f"    Status: {result.status}, Length: {result.answer_length}, Latency: {result.latency_sec}s")
    
    def _task3_v1_prompt(self):
        """Task 3: V1 improved prompt with role, task, audience, constraints."""
        print("\n[Task 3] V1 Improved Prompt")
        
        v1_prompt = """You are an educational content writer specializing in digital literacy for teenagers.

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

Format: Plain text paragraphs."""
        
        self.prompts["v1"] = v1_prompt
        self.prompt_versions["v1"] = {
            "name": "V1 Improved",
            "description": "Role + task + audience + structure + constraints + format",
            "components": ["role", "task", "audience", "structure", "constraints", "format"]
        }
        
        for model in [self.config.primary_model, self.config.secondary_model]:
            print(f"  Testing {model}...")
            result = self.client.complete_with_metrics(
                model=model,
                prompt_name="v1",
                prompt=v1_prompt
            )
            self.results.append(result)
            print(f"    Status: {result.status}, Length: {result.answer_length}, Latency: {result.latency_sec}s")
    
    def _task4_few_shot_examples(self):
        """Task 4: Create bad and good few-shot examples."""
        print("\n[Task 4] Few-Shot Examples Design")
        
        # Bad example - too generic, no specificity
        bad_example = """AI is useful for everyone because it makes life easier and helps with many tasks."""
        
        # Good example - specific situation, conditional phrasing, appropriate caution
        good_example = """AI can help a student understand a difficult concept if used as an explanation assistant rather than a way to just get the answer. For example, asking 'Can you explain how photosynthesis works step by step?' is more useful than asking 'What is the answer to question 5?'"""
        
        self.prompt_versions["examples"] = {
            "bad_example": {
                "text": bad_example,
                "why_weak": "Too general, no concrete situation, no conditional phrasing, reads like a slogan"
            },
            "good_example": {
                "text": good_example,
                "why_strong": "Specific situation (student learning), conditional phrasing ('if used as...'), contrasts good vs bad usage, appropriate caution"
            }
        }
        
        # Save examples
        with open(self.output_dir / "task4_few_shot_examples.json", "w", encoding="utf-8") as f:
            json.dump(self.prompt_versions["examples"], f, ensure_ascii=False, indent=2)
        
        print(f"  Bad example: {bad_example[:80]}...")
        print(f"  Good example: {good_example[:80]}...")
    
    def _task5_v2_one_shot(self):
        """Task 5: V2 one-shot prompt with one good example."""
        print("\n[Task 5] V2 One-Shot Prompt")
        
        good_example = self.prompt_versions["examples"]["good_example"]["text"]
        
        v2_prompt = f"""You are an educational content writer specializing in digital literacy for teenagers.

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
{good_example}

Format: Plain text paragraphs."""
        
        self.prompts["v2"] = v2_prompt
        self.prompt_versions["v2"] = {
            "name": "V2 One-Shot",
            "description": "V1 + one good few-shot example",
            "components": ["role", "task", "audience", "structure", "constraints", "format", "one_shot_example"]
        }
        
        for model in [self.config.primary_model, self.config.secondary_model]:
            print(f"  Testing {model}...")
            result = self.client.complete_with_metrics(
                model=model,
                prompt_name="v2",
                prompt=v2_prompt
            )
            self.results.append(result)
            print(f"    Status: {result.status}, Length: {result.answer_length}, Latency: {result.latency_sec}s")
    
    def _task6_v3_few_shot(self):
        """Task 6: V3 few-shot prompt with multiple examples."""
        print("\n[Task 6] V3 Few-Shot Prompt")
        
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
        
        v3_prompt = f"""You are an educational content writer specializing in digital literacy for teenagers.

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

{few_shot_examples}

Format: Plain text paragraphs."""
        
        self.prompts["v3"] = v3_prompt
        self.prompt_versions["v3"] = {
            "name": "V3 Few-Shot",
            "description": "V1 + three few-shot examples (concrete argument, explanation, cautious conclusion)",
            "components": ["role", "task", "audience", "structure", "constraints", "format", "few_shot_examples"]
        }
        
        for model in [self.config.primary_model, self.config.secondary_model]:
            print(f"  Testing {model}...")
            attempts = 2 if model == self.config.primary_model else 1
            for attempt in range(1, attempts + 1):
                result = self.client.complete_with_metrics(model=model, prompt_name="v3", prompt=v3_prompt)
                result.attempt = attempt
                result.word_count = len(result.answer.split())
                self.results.append(result)
                print(f"    Attempt {attempt}: {result.status}, words={result.word_count}, latency={result.latency_sec}s")
                if model != self.config.primary_model or (result.status == "ok" and 180 <= result.word_count <= 220):
                    break
    
    def _task7_few_shot_analysis(self):
        """Task 7: Analyze few-shot impact."""
        print("\n[Task 7] Few-Shot Analysis")
        
        # Compare V1, V2, V3 results
        analysis = {
            "examples_used": [
                {
                    "example": "Concrete argument (fake citation)",
                    "purpose": "Show how to write specific, verifiable examples instead of vague statements",
                    "version": "v3"
                },
                {
                    "example": "Explaining the example",
                    "purpose": "Show how to explain WHY an example matters, not just state it",
                    "version": "v3"
                },
                {
                    "example": "Cautious conclusion",
                    "purpose": "Show how to conclude without overstatement",
                    "version": "v3"
                },
                {
                    "example": "One-shot good example (student learning)",
                    "purpose": "Show conditional phrasing and specific situation",
                    "version": "v2"
                }
            ],
            "comparison": {}
        }
        
        # Collect metrics per version per model
        for version in ["v1", "v2", "v3"]:
            analysis["comparison"][version] = {}
            for model in [self.config.primary_model, self.config.secondary_model]:
                results = [r for r in self.results if r.prompt_name == version and r.model == model]
                if results:
                    r = results[0]
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
        
        with open(self.output_dir / "task7_few_shot_analysis.json", "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print("  Analysis saved to task7_few_shot_analysis.json")
    
    def _task8_edge_cases(self):
        """Task 8: Edge case testing (3+ checks)."""
        print("\n[Task 8] Edge Case Testing")
        
        edge_cases = [
            {
                "name": "too_general_topic",
                "description": "Too general topic - model may give generic response",
                "prompt": "Write about artificial intelligence.",
                "check": "generic_response"
            },
            {
                "name": "hallucination_risk",
                "description": "Risk of fabricated facts - ask for specific citations",
                "prompt": "Write a mini-essay for students on why AI needs verification. Include 3 specific research papers with authors, years, and DOIs that prove AI hallucinates.",
                "check": "fabricated_citations"
            },
            {
                "name": "audience_change",
                "description": "Change audience - adapt for parents instead of students",
                "prompt": "Rewrite the previous essay for parents of teenagers instead of the teenagers themselves. Keep the same core message but adjust tone and examples.",
                "check": "audience_adaptation"
            },
            {
                "name": "conflicting_requirements",
                "description": "Conflicting requirements - detailed but very short",
                "prompt": "Explain in detail why AI answers need verification with multiple examples, but use no more than 2 sentences total.",
                "check": "conflict_resolution"
            },
            {
                "name": "strict_json_format",
                "description": "Strict JSON format requirement",
                "prompt": """Write a mini-essay for 9-10th grade students on why AI answers need verification.
Return ONLY valid JSON with this exact structure:
{
  "introduction": "string",
  "main_point": "string",
  "example_1": {"claim": "string", "explanation": "string"},
  "example_2": {"claim": "string", "explanation": "string"},
  "conclusion": "string"
}
No extra text, no markdown, just the JSON.""",
                "check": "json_validity"
            }
        ]
        
        edge_results = []
        previous_essay = next((r.answer for r in reversed(self.results)
                               if r.prompt_name == "v3" and r.model == self.config.primary_model
                               and r.status == "ok"), "")
        for case in edge_cases:
            if case["name"] == "audience_change":
                essay = previous_essay or "[No successful V3 essay was available.]"
                case["prompt"] += f"\n\nPREVIOUS ESSAY TO REWRITE:\n{essay}"
        
        for case in edge_cases:
            print(f"  Testing: {case['name']} - {case['description']}")
            for model in [self.config.primary_model]:
                result = self.client.complete_with_metrics(
                    model=model,
                    prompt_name=f"edge_{case['name']}",
                    prompt=case["prompt"]
                )
                self.results.append(result)
                edge_results.append({
                    "case": case["name"],
                    "description": case["description"],
                    "model": model,
                    "result": result.to_dict()
                })
                print(f"    {model}: {result.status}, len={result.answer_length}, finish={result.finish_reason}")
        
        with open(self.output_dir / "task8_edge_cases.json", "w", encoding="utf-8") as f:
            json.dump(edge_results, f, ensure_ascii=False, indent=2)
    
    def _task9_second_model_evaluation(self):
        """Task 9: Second model evaluates first model's output."""
        print("\n[Task 9] Second Model Evaluation")
        
        # Get the best result from primary model (V3)
        primary_v3_results = [r for r in self.results 
                              if r.prompt_name == "v3" and r.model == self.config.primary_model and r.status == "ok"]
        
        if not primary_v3_results:
            print("  No successful V3 result from primary model, skipping evaluation")
            return
        
        best_result = primary_v3_results[0]
        final_text = best_result.answer
        final_prompt = best_result.prompt
        
        # Evaluation prompt for secondary model
        eval_prompt = f"""You are a strict but constructive reviewer of educational texts.

I developed a prompt for a language model. Below I provide:
1. The original task
2. Quality criteria
3. The final prompt used
4. The model's response

Your task: Evaluate both the response AND how well the prompt worked.

ORIGINAL TASK:
{TASK}
Audience: {AUDIENCE}
Context: {CONTEXT}

QUALITY CRITERIA:
{chr(10).join(f"- {c}" for c in GOOD_RESULT_CRITERIA)}

FINAL PROMPT USED:
{final_prompt}

MODEL RESPONSE:
{final_text}

Score each of the nine stated quality criteria from 0 to 2, in the same order. Use 0 = not met, 1 = partly met, 2 = met. Explain briefly when a score is 0 or 1.

Also check:
- Did the model copy few-shot examples too literally?
- Are there any hallucinated facts?
- What are the strongest and weakest aspects?

Return your evaluation as JSON:
{{
  "scores": {{"criterion_1": 0, "criterion_2": 0, "criterion_3": 0, "criterion_4": 0, "criterion_5": 0, "criterion_6": 0, "criterion_7": 0, "criterion_8": 0, "criterion_9": 0}},
  "score_explanations": {{"criterion_1": "string", "criterion_2": "string", "criterion_3": "string", "criterion_4": "string", "criterion_5": "string", "criterion_6": "string", "criterion_7": "string", "criterion_8": "string", "criterion_9": "string"}},
  "few_shot_copying": "none|partial|heavy",
  "hallucinations_found": [],
  "strongest_aspect": "string",
  "weakest_aspect": "string",
  "overall_assessment": "string"
}}"""
        
        print(f"  Evaluating with {self.config.secondary_model}...")
        eval_result = self.client.complete_with_metrics(
            model=self.config.secondary_model,
            prompt_name="evaluation",
            prompt=eval_prompt,
            temperature=0.1  # Lower temperature for more consistent evaluation
        )
        self.results.append(eval_result)
        
        # Parse evaluation
        try:
            eval_data = parse_evaluation_response(eval_result.answer)
            self.evaluation_results.append({
                "evaluator_model": self.config.secondary_model,
                "evaluated_model": self.config.primary_model,
                "evaluated_prompt": "v3",
                "status": eval_result.status,
                "parse_error": False,
                "raw_response": eval_result.answer,
                "evaluation": eval_data
            })
            print(f"  Evaluation complete: {eval_data.get('overall_assessment', 'N/A')[:80]}...")
        except json.JSONDecodeError:
            print("  Warning: Could not parse evaluation JSON")
            self.evaluation_results.append({
                "evaluator_model": self.config.secondary_model,
                "evaluated_model": self.config.primary_model,
                "evaluated_prompt": "v3",
                "status": eval_result.status,
                "parse_error": True,
                "raw_response": eval_result.answer,
                "evaluation": {"raw_response": eval_result.answer, "parse_error": True}
            })
        
        # Save evaluations
        with open(self.output_dir / "task9_evaluations.json", "w", encoding="utf-8") as f:
            json.dump(self.evaluation_results, f, ensure_ascii=False, indent=2)
    
    def _save_all_results(self):
        """Save all results to CSV and JSON."""
        print("\n[Saving Results]")
        
        # Main results CSV
        save_results_csv(self.results, str(self.output_dir / "lab2_results.csv"))
        save_results_json(self.results, str(self.output_dir / "lab2_results.json"))
        
        # Results with metrics (same as main for now, but could be extended)
        save_results_csv(self.results, str(self.output_dir / "lab2_results_with_metrics.csv"))
        
        # Prompts used
        with open(self.output_dir / "prompts_used.json", "w", encoding="utf-8") as f:
            json.dump(self.prompts, f, ensure_ascii=False, indent=2)
        
        # Prompt versions info
        with open(self.output_dir / "prompt_versions.json", "w", encoding="utf-8") as f:
            json.dump(self.prompt_versions, f, ensure_ascii=False, indent=2)
        
        # Manifest
        source_hash = hashlib.sha256(SOURCE_TEXT.encode()).hexdigest()
        runner_hash = compute_file_hash(__file__)
        manifest = create_manifest(self.config, self.results, source_hash, runner_hash)
        save_manifest(manifest, str(self.output_dir / "manifest.json"))
        
        print(f"\nAll results saved to {self.output_dir}/")
        print(f"  - lab2_results.csv")
        print(f"  - lab2_results_with_metrics.csv")
        print(f"  - lab2_results.json")
        print(f"  - prompts_used.json")
        print(f"  - prompt_versions.json")
        print(f"  - manifest.json")
        print(f"  - task1_topic_criteria.json")
        print(f"  - task4_few_shot_examples.json")
        print(f"  - task7_few_shot_analysis.json")
        print(f"  - task8_edge_cases.json")
        print(f"  - task9_evaluations.json")


def main():
    parser = argparse.ArgumentParser(description="Lab 2: Prompt Engineering Fundamentals")
    parser.add_argument("--primary-model", help="Primary model name")
    parser.add_argument("--secondary-model", help="Secondary model name")
    parser.add_argument("--temperature", type=float, default=0.3, help="Temperature")
    parser.add_argument("--max-tokens", type=int, default=2000, help="Max tokens")
    parser.add_argument("--output-dir", default="results/lab2", help="Output directory")
    args = parser.parse_args()
    
    # Load config
    config = Lab2Config.from_env()
    if args.primary_model:
        config.primary_model = args.primary_model
    if args.secondary_model:
        config.secondary_model = args.secondary_model
    config.temperature = args.temperature
    config.max_tokens = args.max_tokens
    config.output_dir = args.output_dir
    
    print(f"Primary model: {config.primary_model}")
    print(f"Secondary model: {config.secondary_model}")
    print(f"Temperature: {config.temperature}")
    print(f"Max tokens: {config.max_tokens}")
    print(f"Output dir: {config.output_dir}")
    
    # Run experiments
    runner = Lab2Runner(config)
    results = runner.run_all()
    
    # Summary
    successful = [r for r in results if r.status == "ok"]
    print(f"\n{'='*60}")
    print(f"LAB 2 COMPLETE")
    print(f"{'='*60}")
    print(f"Total requests: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(results) - len(successful)}")
    if successful:
        avg_latency = sum(r.latency_sec for r in successful) / len(successful)
        avg_length = sum(r.answer_length for r in successful) / len(successful)
        print(f"Avg latency: {avg_latency:.2f}s")
        print(f"Avg length: {avg_length:.0f} chars")


if __name__ == "__main__":
    main()
