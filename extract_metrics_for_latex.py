#!/usr/bin/env python3
"""
Extract metrics from summary files and prepare data for LaTeX tables
Compare results with and without context
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def normalize_model_name(model_name):
    """Normalize model names to match LaTeX table format"""
    # Map actual model names to LaTeX table names
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

def load_summary_files(directory):
    """Load all summary files from a directory"""
    summaries = {}
    dir_path = Path(directory)
    
    for summary_file in dir_path.glob("*_summary.json"):
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
                model = data.get('model', '')
                # Normalize model name: replace / with _
                model = model.replace('/', '_')
                question_type = data.get('question_type', '')
                evaluation_type = data.get('evaluation_type', '')
                
                # Create key: model_questiontype_evaluationtype
                key = f"{model}_{question_type}_{evaluation_type}"
                summaries[key] = data
        except Exception as e:
            print(f"Error loading {summary_file}: {e}")
            continue
    
    return summaries

def calculate_coverage_from_results(directory, model_key, question_type):
    """Calculate coverage metrics from result files using coverage_correct field or by recalculating"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from evaluate import improved_em
    
    dir_path = Path(directory)
    
    # Try to find the result file
    pattern = f"{model_key}_{question_type}_original_results.json"
    files = list(dir_path.glob(pattern))
    
    if not files:
        # Try alternative naming
        pattern = f"{model_key.replace('/', '_')}_{question_type}_original_results.json"
        files = list(dir_path.glob(pattern))
    
    if files:
        try:
            with open(files[0], 'r') as f:
                results = json.load(f)
            
            if results and len(results) > 0:
                # First try to use coverage_correct if it exists
                if 'coverage_correct' in results[0]:
                    coverage_correct_count = sum(1 for r in results if r.get('coverage_correct', False))
                    total = len(results)
                    return coverage_correct_count / total if total > 0 else 0
                
                # Otherwise, calculate from disambiguated_answers if available
                if 'disambiguated_answers' in results[0]:
                    coverage_correct_count = sum(1 for r in results if improved_em([r.get('prediction', '')], r.get('disambiguated_answers', [])))
                    total = len(results)
                    return coverage_correct_count / total if total > 0 else 0
                
                # Last resort: load data file and calculate
                data_file = dir_path.parent.parent / "data" / "val_ambig.json"
                if data_file.exists():
                    with open(data_file) as f:
                        data = json.load(f)
                    
                    # Create mapping of id to disambiguated answers
                    id_to_disambiguated = {}
                    for ex in data:
                        disamb_pairs = ex.get('disambiguated_qa_pairs', {})
                        all_answers = disamb_pairs.get('answers', [])
                        flattened = [ans for ans_list in all_answers for ans in ans_list]
                        id_to_disambiguated[ex.get('id')] = list(flattened)
                    
                    # Calculate coverage
                    coverage_correct_count = 0
                    for r in results:
                        pred = r.get('prediction', '')
                        ex_id = r.get('id', '')
                        disamb_answers = id_to_disambiguated.get(ex_id, [])
                        if improved_em([pred], disamb_answers):
                            coverage_correct_count += 1
                    
                    total = len(results)
                    return coverage_correct_count / total if total > 0 else 0
        except Exception as e:
            print(f"Error calculating coverage from {files[0]}: {e}")
            import traceback
            traceback.print_exc()
    
    return None

def format_percentage(value):
    """Format a decimal value as percentage string"""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}\\%"

def load_coverage_analysis(base_dir):
    """Load coverage analysis data from ambiguous_answer_coverage_analysis.json"""
    coverage_file = base_dir / "ambiguous_answer_coverage_analysis.json"
    model_to_coverage = {}
    
    if coverage_file.exists():
        try:
            with open(coverage_file, 'r') as f:
                data = json.load(f)
            
            for entry in data.get('summary', []):
                model = entry.get('model', '')
                # Normalize model name
                model_normalized = model.replace('/', '_')
                model_to_coverage[model_normalized] = entry.get('accuracy', None)
        except Exception as e:
            print(f"Error loading coverage analysis: {e}")
    
    return model_to_coverage

def extract_metrics(summaries_no_context, summaries_wc, base_dir):
    """Extract and compare metrics"""
    models = get_model_order()
    
    # Load coverage data from analysis file
    coverage_analysis = load_coverage_analysis(base_dir)
    
    # Structure: model -> metric_type -> context_flag -> value
    metrics_data = defaultdict(lambda: defaultdict(dict))
    
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
        
        # Extract unambiguous original
        key_unambig = f"{model_key}_unambiguous_original"
        if key_unambig in summaries_no_context:
            data = summaries_no_context[key_unambig]
            metrics_data[model_latex]['unambiguous']['no_context'] = data.get('accuracy', 0)
        if key_unambig in summaries_wc:
            data = summaries_wc[key_unambig]
            metrics_data[model_latex]['unambiguous']['with_context'] = data.get('accuracy', 0)
        
        # Extract ambiguous original
        key_ambig_orig = f"{model_key}_ambiguous_original"
        if key_ambig_orig in summaries_no_context:
            data = summaries_no_context[key_ambig_orig]
            metrics = data.get('metrics', {})
            metrics_data[model_latex]['ambiguous_original']['no_context'] = data.get('accuracy', 0)
            # Try to get coverage from metrics, otherwise from coverage analysis file, or calculate from results
            coverage_no = metrics.get('coverage_em', None)
            if coverage_no is None:
                # Try from coverage analysis file
                coverage_no = coverage_analysis.get(model_key, None)
            if coverage_no is None:
                coverage_no = calculate_coverage_from_results(base_dir / "results_all_models", model_key, "ambiguous")
            metrics_data[model_latex]['ambiguous_coverage']['no_context'] = coverage_no
        if key_ambig_orig in summaries_wc:
            data = summaries_wc[key_ambig_orig]
            metrics = data.get('metrics', {})
            metrics_data[model_latex]['ambiguous_original']['with_context'] = data.get('accuracy', 0)
            # Try to get coverage from metrics, otherwise calculate from results
            coverage_wc = metrics.get('coverage_em', None)
            if coverage_wc is None:
                coverage_wc = calculate_coverage_from_results(base_dir / "results_all_models_wc", model_key, "ambiguous")
            metrics_data[model_latex]['ambiguous_coverage']['with_context'] = coverage_wc
        
        # Extract ambiguous disambiguated (question-level)
        key_ambig_dis = f"{model_key}_ambiguous_disambiguated"
        if key_ambig_dis in summaries_no_context:
            data = summaries_no_context[key_ambig_dis]
            metrics = data.get('metrics', {})
            metrics_data[model_latex]['disambiguated_qlevel']['no_context'] = metrics.get('question_level_em', 0)
            metrics_data[model_latex]['disambiguated_elevel']['no_context'] = metrics.get('examples_all_correct_rate', 0)
        if key_ambig_dis in summaries_wc:
            data = summaries_wc[key_ambig_dis]
            metrics = data.get('metrics', {})
            metrics_data[model_latex]['disambiguated_qlevel']['with_context'] = metrics.get('question_level_em', 0)
            metrics_data[model_latex]['disambiguated_elevel']['with_context'] = metrics.get('examples_all_correct_rate', 0)
    
    return metrics_data

def generate_comparison_table_latex(metrics_data):
    """Generate LaTeX table comparing with and without context"""
    models = get_model_order()
    
    latex_lines = [
        "\\begin{table*}[h]",
        "\\centering",
        "\\caption{Model Performance Comparison: With vs. Without Context}",
        "\\label{tab:context_comparison}",
        "\\scriptsize",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "\\textbf{Model} & \\textbf{Unambiguous} & \\textbf{Ambiguous Original} & \\textbf{Disambiguated (Q-Level)} & \\textbf{Disambiguated (E-Level)} & \\textbf{Ambiguous Coverage} \\\\",
        " & No Ctx | Ctx & No Ctx | Ctx & No Ctx | Ctx & No Ctx | Ctx & No Ctx | Ctx \\\\",
        "\\midrule"
    ]
    
    for model in models:
        if model not in metrics_data:
            continue
        
        unambig_no = metrics_data[model].get('unambiguous', {}).get('no_context', None)
        unambig_wc = metrics_data[model].get('unambiguous', {}).get('with_context', None)
        ambig_orig_no = metrics_data[model].get('ambiguous_original', {}).get('no_context', None)
        ambig_orig_wc = metrics_data[model].get('ambiguous_original', {}).get('with_context', None)
        disambig_q_no = metrics_data[model].get('disambiguated_qlevel', {}).get('no_context', None)
        disambig_q_wc = metrics_data[model].get('disambiguated_qlevel', {}).get('with_context', None)
        disambig_e_no = metrics_data[model].get('disambiguated_elevel', {}).get('no_context', None)
        disambig_e_wc = metrics_data[model].get('disambiguated_elevel', {}).get('with_context', None)
        coverage_no = metrics_data[model].get('ambiguous_coverage', {}).get('no_context', None)
        coverage_wc = metrics_data[model].get('ambiguous_coverage', {}).get('with_context', None)
        
        row = f"{model} & "
        row += f"{format_percentage(unambig_no)} | {format_percentage(unambig_wc)} & "
        row += f"{format_percentage(ambig_orig_no)} | {format_percentage(ambig_orig_wc)} & "
        row += f"{format_percentage(disambig_q_no)} | {format_percentage(disambig_q_wc)} & "
        row += f"{format_percentage(disambig_e_no)} | {format_percentage(disambig_e_wc)} & "
        row += f"{format_percentage(coverage_no)} | {format_percentage(coverage_wc)} \\\\"
        latex_lines.append(row)
    
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table*}",
        "",
        "\\textbf{Note:} This table compares model performance with and without context. \"No Ctx\" refers to answers without context, \"Ctx\" refers to answers with context. Disambiguated (Q-Level) shows question-level accuracy on individual sub-questions, while Disambiguated (E-Level) shows example-level accuracy on original ambiguous questions. Ambiguous Coverage shows the percentage of ambiguous questions where the model's answer matches at least one disambiguated ground truth answer using improved exact match."
    ])
    
    return "\n".join(latex_lines)

def main():
    # Get directory where script is located
    base_dir = Path(__file__).parent
    dir_no_context = base_dir / "results_all_models"
    dir_with_context = base_dir / "results_all_models_wc"
    
    print("Loading summaries from directories...")
    summaries_no_context = load_summary_files(dir_no_context)
    summaries_wc = load_summary_files(dir_with_context)
    
    print(f"Loaded {len(summaries_no_context)} summaries without context")
    print(f"Loaded {len(summaries_wc)} summaries with context")
    
    metrics_data = extract_metrics(summaries_no_context, summaries_wc, base_dir)
    
    latex_table = generate_comparison_table_latex(metrics_data)
    
    # Save to file
    output_file = base_dir / "context_comparison_table.tex"
    with open(output_file, 'w') as f:
        f.write(latex_table)
    
    print(f"\nLaTeX table saved to: {output_file}")
    print("\n" + "="*80)
    print("LaTeX TABLE:")
    print("="*80)
    print(latex_table)

if __name__ == "__main__":
    main()

