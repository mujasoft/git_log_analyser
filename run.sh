#!/bin/bash

# MIT License
# Copyright (c) 2025 Mujaheed Khan

# This script chunks Jenkins logs into ChromaDB and analyzes them using a local LLM.

set -e  # Exit immediately if any command fails

# Color formatting
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function help() {
  echo -e "${YELLOW}Git Log Ai Analyser - CLI Tool${NC}"
  echo ""
  echo "Usage:"
  echo "  $0             Run full pipeline: ingest commits into chromaDB and analyze them"
  echo "  $0 --help      Show this help message"
  echo ""
  echo "Description:"
  echo "  - This tool loads a repository (configured in settings.toml), extracts n commits"
  echo "    embeds commits, and stores them in ChromaDB."
  echo "  - Then it sends questions (defined in settings.toml) to a local LLM like Mistral"
  echo "    via Ollama and prints the responses."
  echo ""
  echo "Author: Mujaheed Khan"
  echo "License: MIT (c) 2025"
}

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  help
  exit 0
fi

# Run main pipeline
echo "*** Populating ChromaDB with commits..."
python3 populate_commits_into_chromadb.py
echo "*** Done."

echo "*** Interrogating LLM..."
python3 analyse_commits.py
echo "*** Done"
