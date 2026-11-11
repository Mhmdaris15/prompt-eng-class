"""
Lab 2 Source Text
=================
Technical text about AI verification and trustworthiness for prompt engineering experiments.
"""

SOURCE_TEXT = """# Why AI Answers Need Verification: A Guide for Students

## Introduction

Large Language Models (LLMs) like GPT, Claude, and open-source alternatives have become ubiquitous tools for students, researchers, and professionals. They can write code, summarize papers, explain concepts, and even generate creative content. However, a fundamental property of these models is often overlooked: **they are probabilistic text generators, not knowledge databases.**

When an LLM produces an answer, it predicts the most likely next tokens based on its training data and the input prompt. It does not "know" facts in the human sense—it generates text that statistically resembles correct answers. This distinction is critical for anyone relying on AI outputs.

## How LLMs Actually Work

LLMs are trained on massive text corpora from the internet, books, code repositories, and other sources. During training, they learn statistical patterns: which words tend to follow which other words, how concepts relate linguistically, and how to structure coherent responses. The model stores these patterns as weights in a neural network with billions of parameters.

At inference time, given a prompt, the model computes a probability distribution over its vocabulary for the next token. It samples from this distribution (often with temperature controlling randomness) and repeats until reaching a stop condition. The result is a plausible continuation—not a retrieved fact.

## Common Failure Modes

### Hallucination

The most cited failure mode is hallucination: the model generates plausible-sounding but false information. This includes:
- **Fabricated citations**: Inventing paper titles, authors, DOIs, and URLs that don't exist
- **False specifics**: Stating precise numbers, dates, or version numbers that are incorrect
- **Confident falsehoods**: Presenting speculation as established fact with high confidence

Example: An LLM might cite "Smith et al. (2023), 'Transformer Efficiency at Scale,' arXiv:2305.12345" — a paper that never existed, with an arXiv ID that follows the correct format but doesn't resolve.

### Knowledge Cutoff and Staleness

Models have a training cutoff date. Events, releases, and discoveries after that date are unknown to the model unless provided in context. A model trained with a 2023 cutoff will not know about GPT-4o, Claude 3.5, or the latest Python version.

### Context Window Limitations

Even with large context windows (128K, 1M+ tokens), models can lose track of earlier information in long conversations. They may contradict themselves or forget constraints specified earlier.

### Sycophancy and Overconfidence

Models tend to agree with user premises, even false ones. If asked "Why is the sky green?", many models will generate explanations rather than correcting the premise. They also express high confidence in incorrect answers.

## Verification Strategies

### 1. Source Grounding

Always ask for sources and verify them. A legitimate citation should be checkable: search the title, author, DOI, or URL. If the source doesn't exist, the claim is unverified.

### 2. Cross-Reference Multiple Models

Ask the same question to different models (GPT, Claude, Gemini, open models). Convergent answers increase confidence; divergence signals uncertainty or hallucination.

### 3. Request Uncertainty Markers

Prompt the model to explicitly mark uncertainty: "If you're not certain, say 'I don't know' or 'This is speculative.'" Models trained with RLHF often comply.

### 4. Use RAG for Factual Queries

Retrieval-Augmented Generation (RAG) grounds answers in retrieved documents. The model answers based on provided context rather than parametric memory. This dramatically reduces hallucination for factual questions.

### 5. Decompose Complex Claims

Break complex claims into atomic facts. Verify each independently. A compound claim "The 2023 paper by Smith et al. introduced a 40% efficiency improvement" requires verifying: (a) paper exists, (b) authors are Smith et al., (c) year is 2023, (d) claimed improvement is 40%.

### 6. Test with Known Answers

Before trusting a model on unknown questions, test it on questions you know the answer to. This calibrates your trust for that model on that topic.

## Practical Guidelines for Students

1. **Never submit AI-generated content without verification** — Treat AI output as a draft requiring fact-checking.
2. **Use AI for structure and ideas, not facts** — Let it outline, suggest approaches, or explain concepts you'll verify independently.
3. **Cite primary sources, not the AI** — If AI helps you find a paper, cite the paper, not the AI.
4. **Be specific in prompts** — "Summarize the key findings of the 2023 Smith et al. paper on transformer efficiency" is better than "Tell me about transformer efficiency."
5. **Iterate and refine** — If the first answer seems off, ask follow-ups: "Are you certain about that date?" "Can you provide a source?"

## Conclusion

LLMs are powerful reasoning and synthesis engines, but they are not oracles. Their outputs are probabilistic predictions, not retrieved truths. The responsible user treats every AI-generated claim as a hypothesis to be tested, not a fact to be accepted. Verification is not optional—it's the price of using these tools reliably.

The gap between "sounds right" and "is right" is where hallucinations live. Your critical thinking is the bridge.
"""

# Topic and task definition for Lab 2
TOPIC = "Why AI answers need verification"
TASK = "Write a mini-essay for 9-10th grade students explaining why AI answers need verification, with two concrete examples and a cautious conclusion"
AUDIENCE = "9-10th grade students (ages 14-16)"
CONTEXT = "Educational content for a computer science or digital literacy class"
GOOD_RESULT_CRITERIA = [
    "Addresses the chosen topic directly",
    "Understandable by 9-10th grade students",
    "Has logical structure (intro, main point, examples, explanations, conclusion)",
    "Contains at least two concrete examples",
    "No fabricated facts, quotes, sources, or dates",
    "Style is calm, educational, and appropriately cautious",
    "Length within 180-220 words",
    "Conclusion doesn't introduce new arguments",
    "Text usable after minor manual editing"
]

UNDESIRABLE_ERRORS = [
    "Fabricated citations or references",
    "Invented statistics or precise numbers without basis",
    "Overconfident claims without qualification",
    "Condescending or overly complex language for the audience",
    "Missing required structural elements",
    "Exceeding or significantly under word count"
]