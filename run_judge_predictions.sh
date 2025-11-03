#!/bin/bash

# Script to judge LLM predictions for refusals and clarifying questions
# Uses gpt-5-nano-2025-08-07 as the judge model

set -e
# LOCAL: Add your API key here for local development (will be removed on git commit)
# export OPENAI_API_KEY=sk-your-key-here

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set."
    echo "Please set it with: export OPENAI_API_KEY=your_key_here"
    exit 1
fi

# Check if input directory exists
INPUT_DIR="results_all_models"
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist."
    exit 1
fi

# Check if judge script exists
JUDGE_SCRIPT="src/judge_predictions.py"
if [ ! -f "$JUDGE_SCRIPT" ]; then
    echo "Error: Judge script '$JUDGE_SCRIPT' does not exist."
    exit 1
fi

echo "=========================================="
echo "Judging LLM Predictions"
echo "=========================================="
echo "Input directory: $INPUT_DIR"
echo "Output directory: results_all_models_judge"
echo "Judge model: gpt-5-nano-2025-08-07"
echo ""

# Run the judge script
python3 "$JUDGE_SCRIPT" \
    --input_dir "$INPUT_DIR" \
    --output_dir "results_all_models_judge" \
    --judge_model "gpt-5-nano-2025-08-07" \
    --resume

echo ""
echo "=========================================="
echo "Judging complete!"
echo "=========================================="

