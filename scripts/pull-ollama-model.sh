#!/usr/bin/env bash
set -euo pipefail

MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo "Pulling model: ${MODEL}"
OLLAMA_HOST="${OLLAMA_HOST}" ollama pull "${MODEL}"
echo "Model pulled successfully"
