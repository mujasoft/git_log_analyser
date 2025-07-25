# MIT License

# Copyright (c) 2025 Mujaheed Khan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import chromadb
from chromadb.config import Settings
from dynaconf import Dynaconf
import requests
from sentence_transformers import SentenceTransformer
from pprint import pprint
import typer

# Load typer.
app = typer.Typer(
    help="Analyse git commits without having to read them manually.\n\n\
        This script has no CLI options. You are meant to fill out a\
            configuration file with the questions you want answered."
)

settings = Dynaconf(
    settings_files=["settings.toml"],
    environments=True,
    default_env="default",
)

# Extract system setup configuration
persist_dir = settings.persist_dir
collection_name = settings.collection_name
ollama_url = settings.ollama_url
model_name = settings.model_name
n_relevant_results = settings.n_relevant_results

# Initialize ChromaDB client and embedder
client = chromadb.PersistentClient(path=persist_dir)
collection = client.get_collection(name=collection_name)
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def ask_question(query: str) -> str:
    """
    Send a question to the local LLM using embedded Jenkins log context.

    Args:
        query (str): The natural language question to answer.

    Returns:
        str: The response from the LLM.
    """

    # Embed the question
    query_embedding = embedder.encode(query).tolist()

    # Search Chroma DB for relevant log chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_relevant_results
    )

    retrieved_docs = results["documents"][0]
    contexts = "\n-----------\n".join(retrieved_docs)

    # Construct full prompt for the LLM
    full_prompt = f"""You are a world-class expert at analyzing git commits.
    You will only see the message and some metadata but will not be able to
    see diffs.
    Snippets:
    {contexts}
    Question: {query}
    """

    # Send request to local LLM server
    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(ollama_url, json=payload)

    limits = {"llama3": 8000, "mistral": 4000}

    if len(full_prompt) // 4 > limits[model_name]:
        print("*** Warning: Truncated prompt detected."
              "Not all data was included.")

    return response.json().get("response", "[No response]")


# CLI option was avoided on purpose as this tool is meant to be text driven.
# It is far too tedious to type our questions on comandline without some
# interactive output. The user is meant to write his/her/their questions
# in the settings.toml and run this script.
@app.command()
def ask_all_questions():
    """Read settings.toml and ask questions to local LLM.

    In practical use, it's tedious to type out long-form questions directly on
    the commandline. Instead, this tool is designed to read questions from a
    configuration file (settings.toml), which is easier to maintain and better
    suited for repeated or automated analysis.
    """

    for key, value in sorted(settings.questions.items()):
        print(f"Q.: {value}")
        answer = ask_question(value)
        print(f"Ans: {answer.strip()}\n")


if __name__ == "__main__":
    app()