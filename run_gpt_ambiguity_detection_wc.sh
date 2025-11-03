#!/bin/bash

# OpenAI Ambiguity Detection Script
# Runs all OpenAI models on 3 scenarios: unambiguous, ambiguous original, ambiguous disambiguated

set -e
# LOCAL: Add your API key here for local development (will be removed on git commit)
# export OPENAI_API_KEY=sk-your-key-here

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set."
    echo "Please set it with: export OPENAI_API_KEY=your_key_here"
    exit 1
fi

# Change to the script's directory
cd "$(dirname "$0")"

# Configuration
DATA_DIR="data"
OUTPUT_DIR="results_ambiguity_detection_wc"
SCRIPT_PATH="src/ambiguity_detection.py"

# OpenAI models to test
MODELS=(
    "gpt-4"
    "gpt-4o"
    "gpt-4.1"
    "gpt-3.5-turbo"
    "gpt-4o-mini"
    "gpt-4.1-mini"
)

# Data files
VAL_AMBIG_FILE="${DATA_DIR}/val_ambig.json"
VAL_UNAMBIG_FILE="${DATA_DIR}/val_unambig.json"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo "Starting OpenAI ambiguity detection evaluation..."
echo "Models: ${MODELS[*]}"
echo "Output: ${OUTPUT_DIR}"

# Function to check if file is complete
is_file_complete() {
    local file=$1
    if [ ! -f "$file" ]; then
        return 1
    fi
    
    # Check if file has proper JSON structure and contains all expected results
    if python3 -c "
import json
import sys
try:
    with open('$file', 'r') as f:
        data = json.load(f)
    if 'results' in data and 'total_examples' in data:
        results_count = len(data['results'])
        total_examples = data['total_examples']
        if results_count >= total_examples and total_examples > 0:
            print('complete')
        else:
            print('incomplete')
    else:
        print('incomplete')
except:
    print('invalid')
" | grep -q "complete"; then
        return 0
    else
        return 1
    fi
}

# Function to run ambiguity detection
run_ambiguity_detection() {
    local model=$1
    local data_file=$2
    local is_ambiguous=$3
    local evaluate_disambiguated=$4
    local experiment_name=$5
    
    echo "Running: ${model} - ${experiment_name}"
    
    # Create output filename
    local output_file="${OUTPUT_DIR}/${model}_${experiment_name}_ambiguity_detection.json"
    
    # Check if file is complete and resume if needed
    local resume_flag=""
    if is_file_complete "$output_file"; then
        echo "  File already complete, skipping..."
        return 0
    elif [ -f "$output_file" ]; then
        # Show progress for incomplete file
        local current_count=$(python3 -c "
import json
try:
    with open('$output_file', 'r') as f:
        data = json.load(f)
    print(len(data.get('results', [])))
except:
    print('0')
")
        local total_count=$(python3 -c "
import json
try:
    with open('$output_file', 'r') as f:
        data = json.load(f)
    print(data.get('total_examples', 0))
except:
    print('0')
")
        echo "  Resuming from existing file... (${current_count}/${total_count} completed)"
        resume_flag="--resume"
    fi
    
    # Build command
    local cmd="python3 ${SCRIPT_PATH} --data_file ${data_file} --model_name ${model} --output_file ${output_file} --use_context"
    
    if [ "${is_ambiguous}" = "true" ]; then
        cmd="${cmd} --is_ambiguous"
    fi
    
    if [ "${evaluate_disambiguated}" = "true" ]; then
        cmd="${cmd} --evaluate_disambiguated"
    fi
    
    if [ -n "$resume_flag" ]; then
        cmd="${cmd} ${resume_flag}"
    fi
    
    # Run the command
    echo "  Command: ${cmd}"
    ${cmd}
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Completed: ${experiment_name}"
    else
        echo "  ✗ Failed: ${experiment_name}"
        return 1
    fi
}

# Run all experiments for each model
for model in "${MODELS[@]}"; do
    echo ""
    echo "=========================================="
    echo "Processing model: ${model}"
    echo "=========================================="
    
    # Scenario 1: Unambiguous questions
    run_ambiguity_detection "${model}" "${VAL_UNAMBIG_FILE}" "false" "false" "unambiguous"
    
    # Scenario 2: Ambiguous questions (original)
    run_ambiguity_detection "${model}" "${VAL_AMBIG_FILE}" "true" "false" "ambiguous_original"
    
    # Scenario 3: Ambiguous questions (disambiguated)
    run_ambiguity_detection "${model}" "${VAL_AMBIG_FILE}" "true" "true" "ambiguous_disambiguated"
    
    echo "Completed all scenarios for ${model}"
done

echo ""
echo "=========================================="
echo "All experiments completed!"
echo "Results saved in: ${OUTPUT_DIR}/"
echo "=========================================="

# List all result files
echo ""
echo "Generated files:"
ls -la "${OUTPUT_DIR}/"*.json 2>/dev/null || echo "No result files found"
