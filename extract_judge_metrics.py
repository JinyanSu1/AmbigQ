#!/usr/bin/env python3
"""
Extract judge metrics from results and prepare LaTeX tables
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

def load_judge_files(directory):
    """Load all judge result files from a directory"""
    results = {}
    dir_path = Path(directory)
    
    for result_file in dir_path.glob("*_results.json"):
        try:
            # Parse model and experiment type from filename
            filename = result_file.stem  # Remove .json
            # Format: model_experimenttype_results
            base_name = filename.replace('_results', '')
            
            # Determine experiment type
            if base_name.endswith('_unambiguous_original'):
                model_part = base_name[:-len('_unambiguous_original')]
                experiment_type = 'unambiguous_original'
            elif base_name.endswith('_ambiguous_disambiguated'):
                model_part = base_name[:-len('_ambiguous_disambiguated')]
                experiment_type = 'ambiguous_disambiguated'
            elif base_name.endswith('_ambiguous_original'):
                model_part = base_name[:-len('_ambiguous_original')]
                experiment_type = 'ambiguous_original'
            else:
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

def calculate_judge_metrics(data):
    """Calculate judge metrics from a list of results"""
    if not data or len(data) == 0:
        return None
    
    total = len(data)
    successful = sum(1 for item in data if item.get('judge_success', False))
    
    if successful == 0:
        return None
    
    # Count each category (only count successful judgments)
    metrics = {
        'refusal': sum(1 for item in data if item.get('judge_success', False) and item.get('judge_refusal') == True),
        'asking_clarify': sum(1 for item in data if item.get('judge_success', False) and item.get('judge_asking_clarify_Q') == True),
        'answered': sum(1 for item in data if item.get('judge_success', False) and item.get('judge_answered') == True),
        'only_answered': sum(1 for item in data if item.get('judge_success', False) and item.get('judge_only_answered') == True),
        'total': total,
        'successful': successful
    }
    
    # Calculate percentages based on successful judgments
    if successful > 0:
        metrics['refusal_pct'] = metrics['refusal'] / successful
        metrics['asking_clarify_pct'] = metrics['asking_clarify'] / successful
        metrics['answered_pct'] = metrics['answered'] / successful
        metrics['only_answered_pct'] = metrics['only_answered'] / successful
    else:
        metrics['refusal_pct'] = 0
        metrics['asking_clarify_pct'] = 0
        metrics['answered_pct'] = 0
        metrics['only_answered_pct'] = 0
    
    return metrics

def format_percentage(value):
    """Format a decimal value as percentage string"""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}\\%"

def extract_judge_metrics(results_no_context, results_wc):
    """Extract and compare judge metrics"""
    models = get_model_order()
    
    # Structure: model -> experiment_type -> metric_type -> context_flag -> value
    metrics_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    
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
        experiment_types = ['unambiguous_original', 'ambiguous_original', 'ambiguous_disambiguated']
        
        for exp_type in experiment_types:
            key = f"{model_key}_{exp_type}"
            
            if key in results_no_context:
                data = results_no_context[key]
                metrics = calculate_judge_metrics(data)
                if metrics:
                    metrics_data[model_latex][exp_type]['refusal']['no_context'] = metrics['refusal_pct']
                    metrics_data[model_latex][exp_type]['asking_clarify']['no_context'] = metrics['asking_clarify_pct']
                    metrics_data[model_latex][exp_type]['answered']['no_context'] = metrics['answered_pct']
                    metrics_data[model_latex][exp_type]['only_answered']['no_context'] = metrics['only_answered_pct']
            
            if key in results_wc:
                data = results_wc[key]
                metrics = calculate_judge_metrics(data)
                if metrics:
                    metrics_data[model_latex][exp_type]['refusal']['with_context'] = metrics['refusal_pct']
                    metrics_data[model_latex][exp_type]['asking_clarify']['with_context'] = metrics['asking_clarify_pct']
                    metrics_data[model_latex][exp_type]['answered']['with_context'] = metrics['answered_pct']
                    metrics_data[model_latex][exp_type]['only_answered']['with_context'] = metrics['only_answered_pct']
    
    return metrics_data

def generate_judge_comparison_tables_latex(metrics_data):
    """Generate LaTeX tables comparing judge metrics with and without context"""
    models = get_model_order()
    
    # Create tables for each metric
    tables = {}
    
    metric_types = [
        ('refusal', 'Refusal'),
        ('asking_clarify', 'Asking for Clarification'),
        ('answered', 'Answered'),
        ('only_answered', 'Only Answered')
    ]
    
    for metric_key, metric_name in metric_types:
        latex_lines = [
            f"\\begin{{table*}}[h]",
            f"\\centering",
            f"\\caption{{{metric_name} Rate: With vs. Without Context}}",
            f"\\label{{tab:judge_{metric_key}_comparison}}",
            f"\\scriptsize",
            f"\\begin{{tabular}}{{lccc}}",
            f"\\toprule",
            f"\\textbf{{Model}} & \\textbf{{Unambiguous}} & \\textbf{{Ambiguous Original}} & \\textbf{{Ambiguous Disambiguated}} \\\\",
            f" & No Ctx | Ctx & No Ctx | Ctx & No Ctx | Ctx \\\\",
            f"\\midrule"
        ]
        
        for model in models:
            if model not in metrics_data:
                continue
            
            unambig_no = metrics_data[model].get('unambiguous_original', {}).get(metric_key, {}).get('no_context', None)
            unambig_wc = metrics_data[model].get('unambiguous_original', {}).get(metric_key, {}).get('with_context', None)
            ambig_orig_no = metrics_data[model].get('ambiguous_original', {}).get(metric_key, {}).get('no_context', None)
            ambig_orig_wc = metrics_data[model].get('ambiguous_original', {}).get(metric_key, {}).get('with_context', None)
            ambig_dis_no = metrics_data[model].get('ambiguous_disambiguated', {}).get(metric_key, {}).get('no_context', None)
            ambig_dis_wc = metrics_data[model].get('ambiguous_disambiguated', {}).get(metric_key, {}).get('with_context', None)
            
            row = f"{model} & "
            row += f"{format_percentage(unambig_no)} | {format_percentage(unambig_wc)} & "
            row += f"{format_percentage(ambig_orig_no)} | {format_percentage(ambig_orig_wc)} & "
            row += f"{format_percentage(ambig_dis_no)} | {format_percentage(ambig_dis_wc)} \\\\"
            latex_lines.append(row)
        
        latex_lines.extend([
            f"\\bottomrule",
            f"\\end{{tabular}}",
            f"\\end{{table*}}"
        ])
        
        tables[metric_key] = "\n".join(latex_lines)
    
    return tables

def main():
    # Get directory where script is located
    base_dir = Path(__file__).parent
    dir_no_context = base_dir / "results_all_models_judge"
    dir_with_context = base_dir / "results_all_models_judge_wc"
    
    print("Loading judge results from directories...")
    results_no_context = load_judge_files(dir_no_context)
    results_wc = load_judge_files(dir_with_context)
    
    print(f"Loaded {len(results_no_context)} result files without context")
    print(f"Loaded {len(results_wc)} result files with context")
    
    metrics_data = extract_judge_metrics(results_no_context, results_wc)
    
    tables = generate_judge_comparison_tables_latex(metrics_data)
    
    # Save all tables to a single file
    output_file = base_dir / "judge_comparison_tables.tex"
    with open(output_file, 'w') as f:
        for metric_key, table in tables.items():
            f.write(table)
            f.write("\n\n")
    
    print(f"\nLaTeX tables saved to: {output_file}")
    print("\n" + "="*80)
    print("LaTeX TABLES:")
    print("="*80)
    for metric_key, table in tables.items():
        print(f"\n--- {metric_key.upper()} ---")
        print(table)
        print()

if __name__ == "__main__":
    main()

