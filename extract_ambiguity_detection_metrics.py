#!/usr/bin/env python3
"""
Extract ambiguity detection metrics from results and prepare LaTeX table
Compare results with and without context
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def normalize_model_name(model_name):
    """Normalize model names to match LaTeX table format"""
    mapping = {
        'gpt-4.1': 'GPT-4.1',
        'gpt-4o': 'GPT-4O',
        'gpt-4': 'GPT-4',
        'gpt-3.5-turbo': 'GPT-3.5-Turbo',
        'gpt-4o-mini': 'GPT-4O-Mini',
        'gpt-4.1-mini': 'GPT-4.1-Mini',
        'claude-sonnet-4-5-20250929': 'Claude-Sonnet-4.5',
        'claude-haiku-4-5-20251001': 'Claude-Haiku-4.5',
        'Qwen_Qwen2.5-14B-Instruct': 'Qwen2.5-14B',
        'Qwen_Qwen2.5-7B-Instruct': 'Qwen2.5-7B'
    }
    return mapping.get(model_name, model_name)

def get_model_order():
    """Return model order for tables (GPT, Claude, Qwen)"""
    return [
        'GPT-4.1',
        'GPT-4O',
        'GPT-4',
        'GPT-3.5-Turbo',
        'GPT-4O-Mini',
        'GPT-4.1-Mini',
        'Claude-Sonnet-4.5',
        'Claude-Haiku-4.5',
        'Qwen2.5-14B',
        'Qwen2.5-7B'
    ]

def load_ambiguity_detection_files(directory):
    """Load all ambiguity detection result files from a directory"""
    results = {}
    dir_path = Path(directory)
    
    for result_file in dir_path.glob("*_ambiguity_detection.json"):
        try:
            # Parse model and experiment type from filename
            filename = result_file.stem  # Remove .json
            # Remove _ambiguity_detection suffix
            base_name = filename.replace('_ambiguity_detection', '')
            
            # Determine experiment type
            if base_name.endswith('_unambiguous'):
                model_part = base_name[:-len('_unambiguous')]
                experiment_type = 'unambiguous'
            elif base_name.endswith('_ambiguous_disambiguated'):
                model_part = base_name[:-len('_ambiguous_disambiguated')]
                experiment_type = 'ambiguous_disambiguated'
            elif base_name.endswith('_ambiguous_original'):
                model_part = base_name[:-len('_ambiguous_original')]
                experiment_type = 'ambiguous_original'
            else:
                print(f"Warning: Could not parse experiment type from {filename}")
                continue
            
            # Normalize model name: replace / with _
            model = model_part.replace('/', '_')
            
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            # Create key: model_experimenttype
            key = f"{model}_{experiment_type}"
            results[key] = data
        except Exception as e:
            print(f"Error loading {result_file}: {e}")
            continue
    
    return results

def format_percentage(value):
    """Format a decimal value as percentage string"""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}\\%"

def extract_metrics(results_no_context, results_wc):
    """Extract and compare metrics"""
    models = get_model_order()
    
    # Structure: model -> experiment_type -> context_flag -> value
    metrics_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    for model_latex in models:
        # Find matching model names
        model_keys = {
            'GPT-4.1': 'gpt-4.1',
            'GPT-4O': 'gpt-4o',
            'GPT-4': 'gpt-4',
            'GPT-3.5-Turbo': 'gpt-3.5-turbo',
            'GPT-4O-Mini': 'gpt-4o-mini',
            'GPT-4.1-Mini': 'gpt-4.1-mini',
            'Claude-Sonnet-4.5': 'claude-sonnet-4-5-20250929',
            'Claude-Haiku-4.5': 'claude-haiku-4-5-20251001',
            'Qwen2.5-14B': 'Qwen_Qwen2.5-14B-Instruct',
            'Qwen2.5-7B': 'Qwen_Qwen2.5-7B-Instruct'
        }
        
        model_key = model_keys.get(model_latex)
        if not model_key:
            continue
        
        # Extract metrics for each experiment type
        experiment_types = ['unambiguous', 'ambiguous_original', 'ambiguous_disambiguated']
        
        for exp_type in experiment_types:
            key = f"{model_key}_{exp_type}"
            
            if key in results_no_context:
                data = results_no_context[key]
                # For disambiguated questions, recalculate accuracy from results
                # because the stored accuracy might be incorrect (uses wrong denominator)
                if exp_type == 'ambiguous_disambiguated':
                    results_list = data.get('results', [])
                    if results_list:
                        correct_count = sum(1 for r in results_list if r.get('correct', False))
                        total_predictions = len(results_list)
                        accuracy = correct_count / total_predictions if total_predictions > 0 else 0
                    else:
                        accuracy = data.get('accuracy', None)
                else:
                    accuracy = data.get('accuracy', None)
                metrics_data[model_latex][exp_type]['no_context'] = accuracy
            
            if key in results_wc:
                data = results_wc[key]
                # For disambiguated questions, recalculate accuracy from results
                # because the stored accuracy might be incorrect (uses wrong denominator)
                if exp_type == 'ambiguous_disambiguated':
                    results_list = data.get('results', [])
                    if results_list:
                        correct_count = sum(1 for r in results_list if r.get('correct', False))
                        total_predictions = len(results_list)
                        accuracy = correct_count / total_predictions if total_predictions > 0 else 0
                    else:
                        accuracy = data.get('accuracy', None)
                else:
                    accuracy = data.get('accuracy', None)
                metrics_data[model_latex][exp_type]['with_context'] = accuracy
    
    return metrics_data

def generate_comparison_table_latex(metrics_data):
    """Generate LaTeX table comparing ambiguity detection with and without context"""
    models = get_model_order()
    
    latex_lines = [
        "\\begin{table*}[h]",
        "\\centering",
        "\\caption{Ambiguity Detection Performance: With vs. Without Context}",
        "\\label{tab:ambiguity_detection_comparison}",
        "\\scriptsize",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "\\textbf{Model} & \\textbf{Unambiguous} & \\textbf{Ambiguous Original} & \\textbf{Ambiguous Disambiguated} \\\\",
        " & No Ctx | Ctx & No Ctx | Ctx & No Ctx | Ctx \\\\",
        "\\midrule"
    ]
    
    for model in models:
        if model not in metrics_data:
            continue
        
        unambig_no = metrics_data[model].get('unambiguous', {}).get('no_context', None)
        unambig_wc = metrics_data[model].get('unambiguous', {}).get('with_context', None)
        ambig_orig_no = metrics_data[model].get('ambiguous_original', {}).get('no_context', None)
        ambig_orig_wc = metrics_data[model].get('ambiguous_original', {}).get('with_context', None)
        ambig_dis_no = metrics_data[model].get('ambiguous_disambiguated', {}).get('no_context', None)
        ambig_dis_wc = metrics_data[model].get('ambiguous_disambiguated', {}).get('with_context', None)
        
        row = f"{model} & "
        row += f"{format_percentage(unambig_no)} | {format_percentage(unambig_wc)} & "
        row += f"{format_percentage(ambig_orig_no)} | {format_percentage(ambig_orig_wc)} & "
        row += f"{format_percentage(ambig_dis_no)} | {format_percentage(ambig_dis_wc)} \\\\"
        latex_lines.append(row)
    
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table*}",
        "",
        "\\textbf{Note:} This table shows ambiguity detection accuracy. \"No Ctx\" refers to detection without context, \"Ctx\" refers to detection with context. Unambiguous shows accuracy on unambiguous questions (where ground truth is unambiguous), Ambiguous Original shows accuracy on ambiguous questions, and Ambiguous Disambiguated shows accuracy on disambiguated sub-questions."
    ])
    
    return "\n".join(latex_lines)

def main():
    # Get directory where script is located
    base_dir = Path(__file__).parent
    dir_no_context = base_dir / "results_ambiguity_detection"
    dir_with_context = base_dir / "results_ambiguity_detection_wc"
    
    print("Loading ambiguity detection results from directories...")
    results_no_context = load_ambiguity_detection_files(dir_no_context)
    results_wc = load_ambiguity_detection_files(dir_with_context)
    
    print(f"Loaded {len(results_no_context)} results without context")
    print(f"Loaded {len(results_wc)} results with context")
    
    metrics_data = extract_metrics(results_no_context, results_wc)
    
    latex_table = generate_comparison_table_latex(metrics_data)
    
    # Save to file
    output_file = base_dir / "ambiguity_detection_comparison_table.tex"
    with open(output_file, 'w') as f:
        f.write(latex_table)
    
    print(f"\nLaTeX table saved to: {output_file}")
    print("\n" + "="*80)
    print("LaTeX TABLE:")
    print("="*80)
    print(latex_table)

if __name__ == "__main__":
    main()

