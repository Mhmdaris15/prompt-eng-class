"""Lab 4: a bounded plan-tool-answer agent using a local calculator and search."""

from __future__ import annotations

import ast
import operator
from pathlib import Path

from labs.common import OUTPUT_DIR, complete, load_config, make_client, write_csv


CORPUS_DIR = Path(__file__).resolve().parent
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def calculate(expression: str) -> float:
    """Safely evaluate arithmetic expressions supported by the lab."""
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError("Only numeric arithmetic is allowed.")

    return visit(ast.parse(expression, mode="eval"))


def local_search(term: str) -> list[str]:
    matches = []
    for path in CORPUS_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if term.lower() in text.lower():
            matches.append(str(path.name))
    return matches


def run() -> None:
    config = load_config()
    client = make_client(config)
    model = config.models[0]
    tasks = [
        ("calculator", "Calculate 18 * 7 + 5 and explain the result."),
        ("file_search", "Find local lab files containing the word 'RAG'."),
        ("planning", "Give a three-step plan for evaluating a summarization prompt."),
    ]
    rows = []
    for task_type, task in tasks:
        plan = f"1. Understand task. 2. Select {task_type} tool. 3. Produce final answer."
        if task_type == "calculator":
            tool_result = str(calculate("18 * 7 + 5"))
        elif task_type == "file_search":
            tool_result = ", ".join(local_search("RAG")) or "No matching files."
        else:
            tool_result = "No external tool required."
        final_prompt = (
            f"Task: {task}\nPlan: {plan}\nTool result: {tool_result}\n"
            "Return a concise final answer and mention the tool result."
        )
        result = complete(client, model, final_prompt, max_tokens=300)
        rows.append(
            {
                "task_type": task_type,
                "task": task,
                "plan": plan,
                "tool_action": tool_result,
                "final_answer": result.output,
                "latency_seconds": result.latency_seconds,
                "response_length_chars": len(result.output),
                "error": result.error,
            }
        )
    write_csv(OUTPUT_DIR / "lab4_agent_results.csv", rows)
    print(f"Wrote {len(rows)} agent rows to {OUTPUT_DIR}")


if __name__ == "__main__":
    run()
