![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/github/license/mujasoft/git_log_analyser)
![Status](https://img.shields.io/badge/status-WIP-orange)

# Git Log Analyser

A CLI tool that uses AI to analyze git commit history and extract meaningful insights — without manually reading through hundreds of commits.

This tool keeps all processing local. No API keys, no vendor lock-in. Works with Ollama + ChromaDB for 100% offline insight generation.

---

## Why This Exists

You want to understand what’s going on in a codebase but reading commit logs is tedious and time-consuming.

**This tool solves that.**

- Configure once — no need to modify the code
- Simple CLI interface, CI/CD-ready
- Each component is modular and focused — Unix-style design

---

## How It Works

This tool:
1. Connects to any Git repository
2. Parses and embeds commit logs using `SentenceTransformers`
3. Stores commit vectors in a local **ChromaDB**
4. Answers natural-language questions about the commit history using a local LLM (via **llama3**)


## Limitations
This project uses RAG (Retrieval-Augmented Generation) to analyze Git commit history using a local LLM. It works well for answering questions about specific commits or patterns, as long as the context stays within the model’s token limit.

However, questions like “What’s the biggest commit?” or “Which commit is the riskiest?” don’t work out of the box. These require access to all the data — and since LLMs can’t process huge datasets in a single prompt, the answers will often be incomplete or inaccurate.

To handle that properly, the system needs to do some of the heavy lifting itself. For example, the LLM could suggest that a calculation is needed (like total lines changed), and the tool could run that logic separately before asking the model for insight.

This has been a valuable learning experience — it shows that building useful AI tools means combining LLMs with real, thoughtful engineering. It’s not about replacing logic with AI, but getting them to work together.


##  Components

### `populate_commits_into_chromadb.py`
- Parses commits using `GitPython`
- Embeds commit messages
- Stores them into ChromaDB for retrieval
- CLI-friendly via `Typer` or fully config-driven via `settings.toml`

### `analyse_commits.py`
- Loads your configured questions
- Retrieves relevant commit context from ChromaDB
- Sends the question + context to your local LLM (e.g., Mistral)
- Prints concise, eloquent answers

---

## Configuration

All runtime settings live in a single file: `settings.toml`

```toml
[default]
persist_dir = "./chroma_store"
collection_name = "commits"
ollama_url = "http://localhost:11434/api/generate"
model_name = "mistral"
no_of_commits = 50
branch = "main"
git_repo_dir = "~/Desktop/development/brew"
n_relevant_results = 10

[default.questions]
question1 = "Who is the most frequent author?"
question2 = "Can you summarize all the commits?"
question3 = "Can you tabulate a table of the different types of commits?"
```

> You can modify, add, or remove questions anytime — no code changes required.

---

## Usage

### 1. Start your local LLM
```bash
ollama run llama3
# You can use mistral too but that has a smaller token limit
```

### 2. Configure your settings
```bash
vim settings.toml
```

### 3. Run the tool
```bash
python3 populate_commits_into_chromadb.py add-to-chromadb
python3 analyse_commits.py
```

Or combine both steps into a script:
```bash
./run.sh
```

---

## Sample Output

```text
Q.: Who is the most frequent author?
>>ANS: The most frequent contributor is BrewTestBot, responsible for over 40% of recent commits.

Q.: Can you summarize all the commits?
>>ANS: The commits largely focus on dependency updates, auto-generated documentation, and a few feature merges related to Homebrew package handling.

Q.: Can you tabulate a table of the different types of commits?
>>ANS:
| Type           | Count |
|----------------|-------|
| Merge          | 12    |
| Feature        | 5     |
| Auto-generated | 18    |
| Docs           | 3     |
```

---

## Requirements

- Python 3.8+
- [`chromadb`](https://pypi.org/project/chromadb/)
- [`dynaconf`](https://www.dynaconf.com/)
- [`typer`](https://typer.tiangolo.com/)
- [`requests`](https://docs.python-requests.org/en/master/)
- [`sentence-transformers`](https://www.sbert.net/)
- [`GitPython`](https://gitpython.readthedocs.io/en/stable/)
- [`ollama`](https://ollama.com) (optional but recommended for local LLM inference)

---

## TODO

- add unit tests
- add output options such as json or yaml
- add a check to see if ollama+mistral is running and if they are not, perform a sys.exit()

## License

MIT License — see [LICENSE](./LICENSE)

---

## Author

**Mujaheed Khan**  
DevOps | Python | Automation | CI/CD  
GitHub: [github.com/mujasoft](https://github.com/mujasoft)