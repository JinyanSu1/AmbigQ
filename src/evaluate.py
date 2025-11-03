#!/usr/bin/env python3
"""
Flexible evaluation script for various LLMs on AmbigQA dataset.
Supports different evaluation modes and configurations.

Supported models:
- OpenAI: gpt-3.5-turbo, gpt-4, gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini
- Claude: claude-sonnet-4-5-20250929, claude-haiku-4-5-20251001
- Qwen: Qwen/Qwen3-4B-Instruct-2507, Qwen/Qwen3-4B-Thinking-2507
"""

import json
import argparse
from collections import Counter
from typing import Dict, List, Any
from openai import OpenAI
import os
from tqdm import tqdm
import datetime
import requests

# Import utilities
try:
    from .utils import normalize
except ImportError:
    from utils import normalize

def check_answer_match(model_answer, disambiguated_answers):
    """Check if model answer matches any of the disambiguated answers using improved_em function."""
    if not model_answer or not disambiguated_answers:
        return False
    return improved_em([model_answer], disambiguated_answers)

class LLMEvaluator:
    def __init__(self, model_name: str = "gpt-4o", api_key: str = None, base_url: str = None):
        """Initialize LLM evaluator for various models."""
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        
        # Initialize client based on model type
        if model_name.startswith("gpt"):
            # OpenAI models (GPT-3.5, GPT-4, GPT-4o, GPT-4.1, etc.)
            if api_key:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(base_url=base_url)  # Uses OPENAI_API_KEY environment variable
        elif model_name.startswith("claude"):
            # Claude models (claude-sonnet-4-5-20250929, claude-haiku-4-5-20251001)
            self.client = None  # Will use direct API calls for Claude
        elif model_name.startswith("Qwen"):
            # Qwen models (Qwen/Qwen2.5-7B-Instruct, Qwen/Qwen2.5-14B-Instruct)
            self.client = None  # Will use direct API calls for Qwen
            # Initialize Qwen model and tokenizer cache
            self._qwen_model = None
            self._qwen_tokenizer = None
        else:
            raise ValueError(f"Model {model_name} not yet supported. Currently supports: OpenAI (gpt-*), Claude (claude-*), and Qwen (Qwen/*) models")
    
    def get_response(self, question: str, context: str = "", system_prompt: str = None, use_context: bool = True, max_retries: int = 3) -> str:
        """Get response from the specified model with retry logic for empty responses."""
        if system_prompt is None:
            system_prompt = "You are a helpful assistant. Answer the user's question directly and concisely. Provide only the final answer without extensive reasoning or explanation."
            
        
        # Prepare the user message based on context usage
        if use_context and context:
            user_content = f"{question}\n\nContext: {context}"
        else:
            user_content = question
        
        # Retry logic for empty responses
        for attempt in range(max_retries):
            response = self._make_api_call(system_prompt, user_content)
            if response and response.strip():
                return response
            elif attempt < max_retries - 1:
                print(f"Empty response on attempt {attempt + 1}, retrying...")
            else:
                print(f"All {max_retries} attempts returned empty response")
        
        return ""  # Return empty string if all retries failed
    
    def _make_api_call(self, system_prompt: str, user_content: str) -> str:
        """Make the actual API call."""
        try:
            if self.model_name.startswith("gpt"):
                # OpenAI models
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            
            elif self.model_name.startswith("claude"):
                # Claude models - using Anthropic API
                return self._call_claude_api(system_prompt, user_content)
            
            elif self.model_name.startswith("Qwen"):
                # Qwen models - using Hugging Face API or local inference
                return self._call_qwen_api(system_prompt, user_content)
            
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
                
        except Exception as e:
            print(f"Error getting {self.model_name} response: {e}")
            return ""
    
    def _call_claude_api(self, system_prompt: str, user_content: str) -> str:
        """Call Claude API (Anthropic)."""
        # Note: This is a placeholder implementation
        # You'll need to install anthropic package and configure API key
        try:
            import anthropic
            
            if not self.api_key:
                self.api_key = os.environ.get('ANTHROPIC_API_KEY')
            
            if not self.api_key:
                raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Combine system prompt and user content
            full_prompt = f"{system_prompt}\n\n{user_content}"
            
            response = client.messages.create(
                model=self.model_name,
                max_tokens=500,
                temperature=0.1,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            return response.content[0].text.strip()
            
        except ImportError:
            print("Error: anthropic package not installed. Install with: pip install anthropic")
            return ""
        except Exception as e:
            print(f"Claude API error: {e}")
            return ""
    
    def _load_qwen_model(self):
        """Load Qwen model and tokenizer only once (cached)."""
        if self._qwen_model is None or self._qwen_tokenizer is None:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            model_name = self.model_name
            print(f"Loading Qwen model: {model_name} (this will only happen once)")
            
            # Load tokenizer and model with proper configuration
            self._qwen_tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self._qwen_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype="auto",
                device_map="auto",
                trust_remote_code=True
            )
            print(f"Qwen model loaded successfully!")

    def _call_qwen_api(self, system_prompt: str, user_content: str) -> str:
        """Call Qwen model locally using transformers with proper chat template."""
        import torch
        
        # Load model only once (cached)
        self._load_qwen_model()
        
        model = self._qwen_model
        tokenizer = self._qwen_tokenizer
        
        # Prepare the model input using chat template
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        # Generate response
        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=500,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Extract only the new tokens
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        
        # Return the full response
        response = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        
        return response
            



def improved_precision_recall(pred_answers, gold_answers):
    """Improved precision/recall calculation with substring matching."""
    pred_normalized = [normalize(p) for p in pred_answers if p and normalize(p)]
    gold_normalized = [normalize(g) for g in gold_answers if g and normalize(g)]
    
    # Count how many gold answers are found in predictions
    found_gold = 0
    for gold in gold_normalized:
        for pred in pred_normalized:
            if gold and pred and (gold in pred or pred in gold):
                found_gold += 1
                break  # Each gold answer can only be found once
    
    # Count how many predictions match any gold answer
    found_pred = 0
    for pred in pred_normalized:
        for gold in gold_normalized:
            if gold and pred and (gold in pred or pred in gold):
                found_pred += 1
                break  # Each prediction can only match once
    
    # Calculate metrics
    recall = found_gold / len(gold_normalized) if gold_normalized else 0.0
    precision = found_pred / len(pred_normalized) if pred_normalized else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'macro_f1': f1,
        'macro_rec': recall,
        'macro_pre': precision,
        'micro_rec': found_gold,
        'micro_pre': found_pred,
        'micro_pred_total': len(pred_normalized),
        'micro_gold_total': len(gold_normalized),
    }

def improved_em(pred_answers, gold_answers):
    """Improved exact match with substring matching."""
    pred_normalized = [normalize(p) for p in pred_answers if p and normalize(p)]
    gold_normalized = [normalize(g) for g in gold_answers if g and normalize(g)]
    
    for gold in gold_normalized:
        for pred in pred_normalized:
            if gold and pred and (gold in pred or pred in gold):
                return True
    return False

def evaluate_original_questions(data: List[Dict], evaluator: LLMEvaluator, is_ambiguous: bool, results: List[Dict] = None, use_context: bool = True, start_index: int = 0) -> Dict[str, float]:
    """Evaluate original questions (ambiguous or unambiguous)."""
    metrics_counter = Counter()
    
    question_type = "ambiguous" if is_ambiguous else "unambiguous"
    print(f"Evaluating {len(data)} {question_type} original questions...")
    
    # For ambiguous questions, also track coverage metrics using disambiguated answers as ground truth
    coverage_metrics_counter = Counter() if is_ambiguous else None
    
    for i, ex in enumerate(tqdm(data[start_index:], desc=f"{question_type.capitalize()} original questions", initial=start_index)):
        # Use nq_answers as ground truth for standard metrics
        gold_answers = set(ex['nq_answers'])
        
        # Get LLM response
        context = " ".join(ex.get('context', [])) if ex.get('context') else ""
        response = evaluator.get_response(ex['question'], context, use_context=use_context)
        
        # Calculate standard metrics with improved matching
        pred_answers = [response]  # Single prediction
        metrics_counter.update(improved_precision_recall(pred_answers, gold_answers))
        metrics_counter['any_em'] += improved_em(pred_answers, gold_answers)
        
        # For ambiguous questions, calculate coverage metrics using disambiguated answers as ground truth
        if is_ambiguous and coverage_metrics_counter is not None:
            # Get all disambiguated answers as ground truth for coverage
            disambiguated_qa_pairs = ex.get('disambiguated_qa_pairs', {})
            all_disambiguated_answers = disambiguated_qa_pairs.get('answers', [])
            # Flatten the list of lists
            all_disambiguated_answers = [answer for answer_list in all_disambiguated_answers for answer in answer_list]
            
            # Calculate coverage metrics using disambiguated answers as ground truth
            disambiguated_gold_answers = set(all_disambiguated_answers)
            coverage_metrics_counter.update(improved_precision_recall(pred_answers, disambiguated_gold_answers))
            coverage_metrics_counter['any_em'] += improved_em(pred_answers, disambiguated_gold_answers)
        
        # Store result if results list provided
        if results is not None:
            result_entry = {
                'id': ex.get('id', ''),
                'question': ex['question'],
                'gold_answers': list(gold_answers),
                'prediction': response,
                'context': ex.get('context', []),
                'correct': improved_em(pred_answers, gold_answers),
                'evaluation_type': 'original',
                'question_type': question_type
            }
            
            # Add coverage information for ambiguous questions
            if is_ambiguous and coverage_metrics_counter is not None:
                disambiguated_qa_pairs = ex.get('disambiguated_qa_pairs', {})
                all_disambiguated_answers = disambiguated_qa_pairs.get('answers', [])
                # Flatten the list of lists
                all_disambiguated_answers = [answer for answer_list in all_disambiguated_answers for answer in answer_list]
                disambiguated_gold_answers = set(all_disambiguated_answers)
                result_entry['coverage_correct'] = improved_em(pred_answers, disambiguated_gold_answers)
                result_entry['disambiguated_answers'] = all_disambiguated_answers
            
            results.append(result_entry)
    
    # Calculate final metrics
    metrics = {
        'rec': metrics_counter['macro_rec'] / len(data),
        'f1': metrics_counter['macro_f1'] / len(data),
        'em': metrics_counter['any_em'] / len(data),
    }
    
    # Add coverage metrics for ambiguous questions (using disambiguated answers as ground truth)
    if is_ambiguous and coverage_metrics_counter is not None:
        coverage_metrics = {
            'coverage_rec': coverage_metrics_counter['macro_rec'] / len(data),
            'coverage_f1': coverage_metrics_counter['macro_f1'] / len(data),
            'coverage_em': coverage_metrics_counter['any_em'] / len(data),
            'coverage_prec': coverage_metrics_counter['macro_prec'] / len(data),
        }
        metrics.update(coverage_metrics)
    
    return metrics

def evaluate_disambiguated_questions(data: List[Dict], evaluator: LLMEvaluator, results: List[Dict] = None, use_context: bool = True, start_index: int = 0) -> Dict[str, float]:
    """Evaluate disambiguated questions (only for ambiguous data)."""
    metrics_counter = Counter()
    
    print(f"Evaluating {len(data)} examples for disambiguated questions...")
    
    # Track per-example metrics
    example_metrics = []
    
    for i, ex in enumerate(tqdm(data[start_index:], desc="Disambiguated questions", initial=start_index)):
        # Get all disambiguated question-answer pairs
        disambiguated_pairs = ex['disambiguated_qa_pairs']
        questions = disambiguated_pairs['questions']
        answers = disambiguated_pairs['answers']
        
        # Track metrics for this example
        example_correct = 0
        example_total = len(questions)
        
        # Evaluate each disambiguated question
        for i, (question, gold_answers) in enumerate(zip(questions, answers)):
            # Get LLM response for this disambiguated question
            context = " ".join(ex.get('context', [])) if ex.get('context') else ""
            response = evaluator.get_response(question, context, use_context=use_context)
            
            # Calculate metrics with improved matching
            pred_answers = [response]  # Single prediction
            is_correct = improved_em(pred_answers, gold_answers)
            
            if is_correct:
                example_correct += 1
                metrics_counter['any_em'] += 1
            
            metrics_counter.update(improved_precision_recall(pred_answers, gold_answers))
            
            # Store result if results list provided
            if results is not None:
                results.append({
                    'id': f"{ex.get('id', '')}_disambig_{i}",
                    'original_question': ex['question'],
                    'disambiguated_question': question,
                    'gold_answers': gold_answers,
                    'prediction': response,
                    'context': ex.get('context', []),
                    'correct': is_correct,
                    'evaluation_type': 'disambiguated',
                    'question_type': 'ambiguous'
                })
        
        # Track per-example metrics
        example_accuracy = example_correct / example_total if example_total > 0 else 0
        example_metrics.append({
            'example_id': ex.get('id', ''),
            'total_questions': example_total,
            'correct_questions': example_correct,
            'accuracy': example_accuracy,
            'all_correct': example_correct == example_total
        })
    
    # Calculate comprehensive metrics
    total_questions = sum(len(ex['disambiguated_qa_pairs']['questions']) for ex in data)
    total_examples = len(data)
    
    # Basic metrics
    basic_metrics = {
        'rec': metrics_counter['macro_rec'] / total_questions if total_questions > 0 else 0,
        'f1': metrics_counter['macro_f1'] / total_questions if total_questions > 0 else 0,
        'em': metrics_counter['any_em'] / total_questions if total_questions > 0 else 0,
    }
    
    # Per-example metrics
    example_accuracies = [em['accuracy'] for em in example_metrics]
    examples_all_correct = sum(1 for em in example_metrics if em['all_correct'])
    
    # Calculate distribution metrics
    if example_accuracies:
        min_example_accuracy = min(example_accuracies)
        max_example_accuracy = max(example_accuracies)
        std_example_accuracy = (sum((x - sum(example_accuracies) / len(example_accuracies))**2 for x in example_accuracies) / len(example_accuracies))**0.5
    else:
        min_example_accuracy = 0
        max_example_accuracy = 0
        std_example_accuracy = 0
    
    # Additional disambiguated-specific metrics
    disambiguated_metrics = {
        # Basic question-level metrics
        'question_level_recall': basic_metrics['rec'],
        'question_level_f1': basic_metrics['f1'],
        'question_level_em': basic_metrics['em'],
        
        # Example-level metrics
        'example_level_accuracy': sum(example_accuracies) / len(example_accuracies) if example_accuracies else 0,
        'examples_all_correct': examples_all_correct,
        'examples_all_correct_rate': examples_all_correct / total_examples if total_examples > 0 else 0,
        
        # Coverage metrics
        'avg_questions_per_example': total_questions / total_examples if total_examples > 0 else 0,
        'total_questions_evaluated': total_questions,
        'total_examples_evaluated': total_examples,
        
        # Distribution metrics
        'min_example_accuracy': min_example_accuracy,
        'max_example_accuracy': max_example_accuracy,
        'std_example_accuracy': std_example_accuracy,
    }
    
    return disambiguated_metrics

def main():
    parser = argparse.ArgumentParser(description="Flexible GPT-4o evaluation on AmbigQA dataset")
    parser.add_argument('--data_file', required=True, help='Path to data file (JSONL format)')
    parser.add_argument('--is_ambiguous', action='store_true', help='Whether the data file contains ambiguous questions')
    parser.add_argument('--evaluate_disambiguated', action='store_true', help='Evaluate disambiguated questions (only for ambiguous data)')
    parser.add_argument('--max_examples', type=int, help='Maximum examples to evaluate')
    parser.add_argument('--api_key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--output_dir', default='results', help='Output directory for results')
    parser.add_argument('--model_name', default='gpt-4o', help='Model name (e.g., gpt-3.5-turbo, gpt-4, gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini, claude-sonnet-4-5-20250929, claude-haiku-4-5-20251001, Qwen/Qwen3-4B-Instruct-2507, Qwen/Qwen3-4B-Thinking-2507)')
    parser.add_argument('--base_url', help='Custom base URL for API (e.g., for local models)')
    parser.add_argument('--use_context', action='store_true', help='Use context from dataset (default: False)')
    parser.add_argument('--resume', action='store_true', help='Resume from existing results')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # For Qwen models, create subdirectory if needed
    if args.model_name.startswith("Qwen"):
        model_dir = os.path.join(args.output_dir, args.model_name.replace("/", "_"))
        os.makedirs(model_dir, exist_ok=True)
    
    # Initialize evaluator
    # Determine which API key to use based on model type
    if args.model_name.startswith("gpt"):
        api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    elif args.model_name.startswith("claude"):
        api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    elif args.model_name.startswith("Qwen"):
        # Qwen models run locally, no API key needed
        api_key = None
    else:
        api_key = args.api_key
    
    evaluator = LLMEvaluator(model_name=args.model_name, api_key=api_key, base_url=args.base_url)
    
    # Load data
    with open(args.data_file, 'r') as f:
        data = [json.loads(line) for line in f if line.strip()]
    
    if args.max_examples:
        data = data[:args.max_examples]
    
    # Determine evaluation type and file names
    question_type = "ambiguous" if args.is_ambiguous else "unambiguous"
    evaluation_type = "disambiguated" if args.evaluate_disambiguated else "original"
    
    # Check if we can evaluate disambiguated questions
    if args.evaluate_disambiguated and not args.is_ambiguous:
        print("Error: Cannot evaluate disambiguated questions on unambiguous data")
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Use the main directory for all models
    result_file = f"{args.output_dir}/{args.model_name.replace('/', '_')}_{question_type}_{evaluation_type}_results.json"
    
    print("="*60)
    print(f"LLM EVALUATION: {question_type.upper()} {evaluation_type.upper()}")
    print("="*60)
    print(f"Data file: {args.data_file}")
    print(f"Question type: {question_type}")
    print(f"Evaluation type: {evaluation_type}")
    print(f"Model: {args.model_name}")
    print(f"Use context: {args.use_context}")
    print(f"Max examples: {args.max_examples or 'all'}")
    print(f"Output file: {result_file}")
    print("="*60)
    
    # Check if results already exist
    # Handle resume functionality
    existing_results = []
    start_index = 0
    if args.resume and os.path.exists(result_file):
        print(f"Loading existing results from {result_file}")
        with open(result_file, 'r') as f:
            existing_results = json.load(f)
        print(f"Found {len(existing_results)} existing results")
        start_index = len(existing_results)
        print(f"Resuming from index {start_index}")
    
    # Initialize results list with existing results
    results = existing_results.copy()
    
    # Run evaluation
    if args.evaluate_disambiguated:
        metrics = evaluate_disambiguated_questions(data, evaluator, results, use_context=args.use_context, start_index=start_index)
    else:
        metrics = evaluate_original_questions(data, evaluator, args.is_ambiguous, results, use_context=args.use_context, start_index=start_index)
    
    # Print metrics
    print(f"\nResults:")
    if args.evaluate_disambiguated:
        # Print comprehensive disambiguated metrics
        print(f"Question-Level Metrics:")
        print(f"  Recall: {metrics['question_level_recall']:.3f}")
        print(f"  F1: {metrics['question_level_f1']:.3f}")
        print(f"  Exact Match: {metrics['question_level_em']:.3f}")
        print(f"\nExample-Level Metrics:")
        print(f"  Example Accuracy: {metrics['example_level_accuracy']:.3f}")
        print(f"  Examples All Correct: {metrics['examples_all_correct']}/{metrics['total_examples_evaluated']}")
        print(f"  All Correct Rate: {metrics['examples_all_correct_rate']:.3f}")
        print(f"\nCoverage Metrics:")
        print(f"  Total Questions: {metrics['total_questions_evaluated']}")
        print(f"  Total Examples: {metrics['total_examples_evaluated']}")
        print(f"  Avg Questions/Example: {metrics['avg_questions_per_example']:.2f}")
        print(f"\nDistribution Metrics:")
        print(f"  Min Example Accuracy: {metrics['min_example_accuracy']:.3f}")
        print(f"  Max Example Accuracy: {metrics['max_example_accuracy']:.3f}")
        print(f"  Std Example Accuracy: {metrics['std_example_accuracy']:.3f}")
    else:
        # Print basic metrics for original questions
        print(f"Recall: {metrics['rec']:.3f}")
        print(f"F1: {metrics['f1']:.3f}")
        print(f"Exact Match: {metrics['em']:.3f}")
        
        # Display coverage metrics for ambiguous questions
        if args.is_ambiguous and 'coverage_rec' in metrics:
            print(f"\n  Ambiguous Answer Coverage (using disambiguated answers as ground truth):")
            print(f"  Coverage Precision: {metrics['coverage_prec']:.3f}")
            print(f"  Coverage Recall: {metrics['coverage_rec']:.3f}")
            print(f"  Coverage F1: {metrics['coverage_f1']:.3f}")
            print(f"  Coverage Exact Match: {metrics['coverage_em']:.3f}")
    
    # Save results
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {result_file}")
    
    # Save summary
    summary = {
        'timestamp': datetime.datetime.now().isoformat(),
        'model': args.model_name,
        'question_type': question_type,
        'evaluation_type': evaluation_type,
        'data_file': args.data_file,
        'total_examples': len(results),
        'correct': sum(1 for r in results if r['correct']),
        'accuracy': sum(1 for r in results if r['correct']) / len(results) if results else 0,
        'metrics': metrics
    }
    
    # Generate summary file name
    summary_file = f"{args.output_dir}/{args.model_name.replace('/', '_')}_{question_type}_{evaluation_type}_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_file}")
    
    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
