# Terminai (Prototype)

**Terminai** is a proof-of-concept for a local-first, privacy-focused CLI tool that translates natural language queries into jq syntax.

It's built on the philosophy that developers shouldn't have to choose between productivity and privacy. You shouldn't have to paste sensitive production JSON into a third-party API just to build a filter.

This tool runs **100% locally**, using a GBNF-constrained local model (llama-cpp-python) to provide reliable, syntactically-correct jq queries without your data ever leaving your machine.

## The Problem

1. **jq is powerful but has high cognitive friction.** Developers often have to stop and consult documentation, breaking their workflow.
2. **Using cloud-based LLMs is a non-starter.** You cannot (and should not) paste potentially sensitive production data (like K8s outputs or AWS API responses) into a third-party service.
3. **Standard local LLMs hallucinate.** A normal local model will often produce jq syntax that is *almost* correct, making it unreliable for a deterministic tool.

## The Solution: A Reliable, Local-First Architecture

Terminai solves this by building a reliable "tool-builder" from the fundamentals, not just wrapping an API.

1. **Dynamic Context (via genson):** The tool reads your JSON from stdin and dynamically generates a JSON Schema. The model isn't guessing your data structure; it's reading a blueprint.
2. **Local-First Inference (via llama-cpp-python):** It uses llama-cpp-python to run a local GGUF model (gemma-3-4b-it-qat-Q4_0.gguf by default). Your data never leaves your terminal.
3. **Deterministic Output (via GBNF):** This is the core of the solution. It passes the `jq.gbnf` grammar to the model at inference time. This **guarantees** that the model's output is *syntactically valid* jq, completely eliminating syntactical hallucinations.

**Note:** This is an important stepping stone toward a reliable tool. It guarantees *syntactical* correctness, not *logical* correctness. The model can still produce a valid query that doesn't do what you intended, but it can no longer produce an invalid expression.

## How to Use

This is a prototype, not a packaged CLI. To run it, you'll need python >= 3.9, uv (or pip), and jq installed on your system.

### 1. Install Dependencies:

```bash
# Using uv
uv pip install -r requirements.txt

# Or from the pyproject.toml
uv pip install .
```

### 2. Run the Tool:

The script reads your JSON data from stdin and takes your natural language query as the first command-line argument. The output is piped directly to jq.

```bash
# Example 1: Get names of pods and their IPs
cat k8s-pods.json | python main.py "list the names and IPs of all pods"

# Example 2: Count pods that are not running
cat k8s-pods.json | python main.py "how many pods are not in the 'Running' phase?"

# Example 3: Filter and get back the full objects
cat data.json | python main.py "find users who are admins"
```

## Key Files in this Repo

* `main.py`: The main Python script. It handles reading stdin, generating the schema, building the prompt, calling the LLM, and piping the result to jq.
* `jq.gbnf`: The stripped down GBNF grammar that defines a subset of the jq language to constrain the LLM's output. The grammar is focused on common operations to not overwhelm the small model.
* `prompts/jq_prompt.md`: The system prompt template, which includes few-shot examples and placeholders for the dynamic schema and user query.
* `pyproject.toml` / `uv.lock`: Project dependencies.
