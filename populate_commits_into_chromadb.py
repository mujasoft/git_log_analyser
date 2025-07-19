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

from datetime import datetime
import logging

import chromadb
from dynaconf import Dynaconf
from git import Repo
from sentence_transformers import SentenceTransformer
import typer

# Setup logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s -\
%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


settings = Dynaconf(
    settings_files=["settings.toml"],
    environments=True,
    default_env="default",
)

# Load typer.
app = typer.Typer(
    help="A tool to process git commits and embed them into a \
        ChromaDB for fast retrieval."
)


def chunk_git_commits(no_of_commits: int, branch: str, git_repo_dir: str):
    """Go to a repo, checkout a branch and return a list of n commits.

    Args:
        no_of_commits (int): No. of commits.
        branch (str): Name of git branch.
        git_repo_dir (str): location of git repo.

    Returns:
        list: list of dictionarys containing commit data with field such as:
               - hexsha
               - author
               - msg
               - commited_date
    """
    repo = Repo(git_repo_dir)
    commits = list(repo.iter_commits(branch, max_count=no_of_commits))

    chunks = []

    for commit in commits:
        ts_epoch = commit.committed_date
        ts = datetime.fromtimestamp(ts_epoch).strftime('%Y-%m-%d %H:%M:%S')
        commit_dict = {
            "hexsha": commit.hexsha,
            "author": commit.author.name,
            "msg": commit.message,
            "committed_date": ts
        }
        chunks.append(commit_dict)

    return chunks


@app.command()
def add_to_chromadb(
    local_chromadb_store: str = typer.Option("./chroma_store",
                                             help="Path to local store."),
    collection_name: str = typer.Option(settings.collection_name,
                                        help="A helpful name for collection."),
    git_repo_dir: str = typer.Option(settings.git_repo_dir,
                                     help="Location of log folder."),
    no_of_commits: int = typer.Option(settings.no_of_commits,
                                      help="No. of chunks."),
    branch: str = typer.Option(settings.branch,
                               help="Name of branch.")
):
    """Chunks all n commits and inserts them to a chromaDB."""

    settings.reload()

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
                "hexsha": chunk["hexsha"]
            }],
            ids=[f"commit_{idx}_{chunk['hexsha']}"]
        )
    logger.info("*** Done")


if __name__ == "__main__":
    app()
