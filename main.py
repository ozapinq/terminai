import sys
import json
import subprocess
import ctypes
import warnings
from llama_cpp import Llama
from llama_cpp import LlamaGrammar
from llama_cpp import llama_log_set
from genson import SchemaBuilder

# Suppress Hugging Face Hub deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

def my_log_callback(level, message, user_data):
    pass

log_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)(my_log_callback)
llama_log_set(log_callback, ctypes.c_void_p())

def read_stdin():
    """Read all available input from stdin without truncation"""
    return sys.stdin.read()

def main():
    # Read stdin for JSON input
    input_data = read_stdin()

    # Generate schema using genson
    builder = SchemaBuilder()
    try:
        parsed_data = json.loads(input_data)
        builder.add_object(parsed_data)
    except json.JSONDecodeError:
        print("Error: invalid JSON input", file=sys.stderr)
        sys.exit(1)

    schema = builder.to_schema()
    schema_str = json.dumps(schema, indent=2)

    # Get natural language query from command line arguments
    if len(sys.argv) < 2:
        print("Error: no natural language query provided", file=sys.stderr)
        sys.exit(1)
    natural_language = sys.argv[1]

    llm = Llama.from_pretrained(
        repo_id="ggml-org/gemma-3-4b-it-qat-GGUF",
        filename="gemma-3-4b-it-qat-Q4_0.gguf",
        n_ctx=131072,
        n_gpu_layers=1,
        verbose=False,
    )

    with open('jq.gbnf') as f:
        grammar_spec = f.read()

    grammar = LlamaGrammar.from_string(grammar_spec)

    # Generate jq filter using LLM
    jq_filter = generate_jq_filter(llm, grammar, schema_str, natural_language)

    # Execute jq using subprocess with proper pipe handling
    try:
        result = subprocess.run(
            ['jq', jq_filter],
            input=input_data,
            text=True,
            capture_output=False,  # Let jq output directly to stdout/stderr
            check=True
        )
    except subprocess.CalledProcessError as e:
        # jq will have already printed error messages to stderr
        sys.exit(e.returncode)


def load_prompt_template():
    """Load the prompt template from file"""
    with open('prompts/jq_prompt.md', 'r') as f:
        return f.read()

def generate_jq_filter(llm, grammar, schema_str, natural_language) -> str:
    """Generate a jq filter using the LLM based on the schema and natural language query"""
    prompt_template = load_prompt_template()
    # Replace placeholders manually to avoid issues with curly braces in JSON
    prompt = prompt_template.replace('{schema_str}', schema_str).replace('{natural_language}', natural_language)

    output = llm.create_completion(
        prompt,
        grammar=grammar,
        temperature=0.1,
        max_tokens=256,
    )

    # Extract the generated jq filter from the response
    filter: str = output['choices'][0]['text'].strip()
    return filter

if __name__ == "__main__":
    main()
