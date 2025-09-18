#!/bin/bash
ollama serve &
echo "serve"
sleep 10
ollama pull hf.co/TheBloke/sqlcoder-7B-GGUF:Q4_K_M
wait