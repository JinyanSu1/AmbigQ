# LLM Evaluation on AmbigQA Dataset

This project evaluates various Large Language Models (LLMs) on the AmbigQA dataset for question-answering and ambiguity detection tasks.

## Supported Models

### OpenAI Models
- `gpt-3.5-turbo`
- `gpt-4`
- `gpt-4.1`
- `gpt-4.1-mini`
- `gpt-4o`
- `gpt-4o-mini`

### Claude Models
- `claude-sonnet-4-5-20250929`
- `claude-haiku-4-5-20251001`

### Qwen Models (Local Inference)
- `Qwen/Qwen2.5-7B-Instruct`
- `Qwen/Qwen2.5-14B-Instruct`

## Setup

1. **Create/Activate Environment:**
   ```bash
   # Option 1: Use conda (if you have adaptiverag environment)
   conda activate adaptiverag
   
   # Option 2: Create a new virtual environment
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Set API Keys:**
   ```bash
   export OPENAI_API_KEY="your_openai_key_here"
   export ANTHROPIC_API_KEY="your_claude_key_here"
   # Optional for Qwen models:
   export HUGGINGFACE_API_KEY="your_hf_key_here"
   ```

3. **Install Dependencies:**
   ```bash
   pip install anthropic transformers torch
   ```

## Usage




### Run Specific Evaluations

**OpenAI Models (6 models × 3 experiments):**
```bash
./run_all_experiments.sh
```

**Claude Models (2 models × 3 experiments):**
```bash
./run_claude_evaluation.sh
```

**Qwen Models (2 models × 3 experiments):**
```bash
./run_qwen_evaluation.sh
```

**Ambiguity Detection (6 models × 3 experiments):**
```bash
./run_all_missing_ambiguity_detection.sh
```

### Run All in Parallel
```bash
./run_all_experiments.sh &
./run_claude_evaluation.sh &
./run_qwen_evaluation.sh &
./run_all_missing_ambiguity_detection.sh &
```

## Evaluation Types

1. **Unambiguous Questions** - Direct question answering
2. **Ambiguous Original Questions** - Answering ambiguous questions as-is
3. **Ambiguous Disambiguated Questions** - Answering clarified versions of ambiguous questions
4. **Ambiguity Detection** - Classifying questions as ambiguous or unambiguous

## Results

Results are saved in:
- `results_all_models/` - Main evaluation results
- `results_ambiguity_detection/` - Ambiguity detection results

Each result file contains detailed metrics including:
- Recall, Precision, F1 Score
- Exact Match (EM)
- Question-level and Example-level metrics
- Pass@1 for disambiguated questions

## Project Structure

```
clarifying_questions/
├── data/                           # Dataset files
├── results_all_models/            # Main evaluation results
├── results_ambiguity_detection/   # Ambiguity detection results
├── src/                          # Core evaluation scripts
│   ├── evaluate_flexible.py      # Main evaluation script
│   ├── evaluate_ambiguity_detection.py  # Ambiguity detection
│   ├── analyze_ambiguity_results.py    # Results analysis
│   └── utils.py                  # Utility functions
├── run_evaluation.sh             # Main entry point
├── run_all_experiments.sh        # OpenAI models
├── run_claude_evaluation.sh      # Claude models
├── run_qwen_evaluation.sh        # Qwen models
├── run_all_missing_ambiguity_detection.sh  # Ambiguity detection
└── README.md                     # This file
```