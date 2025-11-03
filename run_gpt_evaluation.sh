#!/bin/bash

# GPT model evaluation script
# Runs all 6 OpenAI models on 3 experiment types

set -e
# You can add your API key here for local convenience (will be auto-removed on commit, then restored)
# export OPENAI_API_KEY=sk-your-key-here

# Check if API key is set (either locally or from environment)
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set."
    echo "Please set it with: export OPENAI_API_KEY=your_key_here"
    exit 1
fi

# Configuration
DATA_DIR="data"
OUTPUT_DIR="results_all_models"

# Models to test
MODELS=(
    "gpt-3.5-turbo"
    "gpt-4"
    "gpt-4.1"
    "gpt-4.1-mini"
    "gpt-4o"
    "gpt-4o-mini"
)

# Data files
VAL_AMBIG_FILE="${DATA_DIR}/val_ambig.json"
VAL_UNAMBIG_FILE="${DATA_DIR}/val_unambig.json"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo "Starting GPT evaluation..."
echo "Models: ${MODELS[*]}"
echo "Output: ${OUTPUT_DIR}"

# Function to run evaluation
run_evaluation() {
    local model=$1
    local data_file=$2
    local is_ambiguous=$3
    local evaluate_disambiguated=$4
    local experiment_name=$5
    
    echo "Running: ${model} - ${experiment_name}"
    
    # Build command
    cmd="python src/evaluate.py --data_file ${data_file} --model_name ${model} --output_dir ${OUTPUT_DIR}"
    
    if [ "${is_ambiguous}" = "true" ]; then
        cmd="${cmd} --is_ambiguous"
    fi
    
    if [ "${evaluate_disambiguated}" = "true" ]; then
        cmd="${cmd} --evaluate_disambiguated"
    fi
    
    # Run the command
    ${cmd}
}

# Run all experiments for each model
for model in "${MODELS[@]}"; do
    echo "Processing model: ${model}"
    
    # Experiment 1: Ambiguous questions, evaluate disambiguated
    run_evaluation "${model}" "${VAL_AMBIG_FILE}" "true" "true" "ambiguous_disambiguated"
    
    # Experiment 2: Ambiguous questions, evaluate original
    run_evaluation "${model}" "${VAL_AMBIG_FILE}" "true" "false" "ambiguous_original"
    
    # Experiment 3: Unambiguous questions
    run_evaluation "${model}" "${VAL_UNAMBIG_FILE}" "false" "false" "unambiguous_original"
done

echo "All experiments completed!"
echo "Results saved in: ${OUTPUT_DIR}/"
