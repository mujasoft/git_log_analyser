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


from dynaconf import Dynaconf
import logging
import re
from pathlib import Path
import chromadb
from concurrent.futures import ThreadPoolExecutor, as_completed
from sentence_transformers import SentenceTransformer
import typer
from git import Repo

# Setup logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s -\
%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load config. 
settings = Dynaconf(settings_files=["settings.toml"])

# Load typer.
app = typer.Typer(
    help="A tool to process Jenkins log files, chunk them by pipeline stages, \
and embed them into a ChromaDB for fast retrieval."
)


def chunk_git_commits(no_of_commits: int, branch: str, git_repo_dir: str):

    repo = Repo(git_repo_dir)
    commits = list(repo.iter_commits(branch, max_count=no_of_commits))

    chunks = []

    for commit in commits:

        commit_dict = {
            "hexsha": commit.hexsha,
            "author": commit.author.name,
            "msg": commit.message,
            "committed_date": commit.committed_date
        }
        chunks.append(commit_dict)

    return chunks


@app.command()
def add_to_chromadb(
    local_chromadb_store: str = typer.Option(settings.system_setup.persist_dir,
                                             help="Path to local store."),
    collection_name: str = typer.Option(settings.system_setup.collection_name,
                                        help="A helpful name for collection."),
    git_repo_dir: str = typer.Option(settings.git_repo_dir,
                                     help="Location of log folder."),
    no_of_commits: int = typer.Option(settings.system_setup.no_of_commits,
                                      help="No. of chunks."),
    branch: int = typer.Option(settings.no_of_commits,
                               help="No. of commits.")
):
    """Chunks all the logs and inserts them to a chromaDB."""

    logger.info("*** Creating chunks from logs based on pipeline stages...")
    chunks = chunk_git_commits(no_of_commits, branch, git_repo_dir)
    logger.info("*** Done")

    # Initialize ChromaDB client (local store)
    chroma_client = chromadb.PersistentClient(path=local_chromadb_store)

    # Create or get the collection
    collection = chroma_client.get_or_create_collection(name=collection_name)

    # Load the embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")  # small and fast

    logger.info(f"*** Embed and add chunks to \"{local_chromadb_store}\"")
    # Embed and add to ChromaDB
    for idx, chunk in enumerate(chunks):
        embedding = model.encode(chunk["msg"]).tolist()
        collection.add(
            documents=[chunk["msg"]],
            embeddings=[embedding],
            metadatas=[{
                "author": chunk["author"],
                "committed_date": chunk["committed_date"],
                "hexsha": chunks["hexsha"]
            }],
            ids=[f"commit_{idx}_{chunk['hexsha']}"]
        )
    logger.info("*** Done")


if __name__ == "__main__":
    app()
