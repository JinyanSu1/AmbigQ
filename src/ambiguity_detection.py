#!/usr/bin/env python3
"""
Evaluate LLM's ability to detect question ambiguity.
Tests models on unambiguous, ambiguous original, and ambiguous disambiguated questions.
"""

import json
import argparse
import os
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
import re

class AmbiguityDetector:
    def __init__(self, model_name: str, api_key: str = None, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        
        # Initialize client based on model type
        if model_name.startswith("gpt"):
            # OpenAI models
            if api_key:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(base_url=base_url)
        elif model_name.startswith("claude"):
            # Claude models
            self.client = None  # Will use direct API calls for Claude
        elif model_name.startswith("Qwen"):
            # Qwen models
            self.client = None  # Will use direct API calls for Qwen
            # Initialize Qwen model and tokenizer cache
            self._qwen_model = None
            self._qwen_tokenizer = None
        else:
            raise ValueError(f"Model {model_name} not yet supported. Currently supports OpenAI (gpt-*), Claude (claude-*), and Qwen (Qwen/*) models")
    
    def detect_ambiguity(self, question: str, context: str = "", use_context: bool = False) -> dict:
        """Ask the model to detect if a question is ambiguous."""
        
        system_prompt = """You are an expert at analyzing question ambiguity. Your task is to determine whether a given question is ambiguous or unambiguous.

An ambiguous question is one that:
- Can be interpreted in multiple ways
- Has multiple possible correct answers depending on interpretation
- Lacks sufficient context to determine the intended meaning
- Could refer to different entities, time periods, or contexts

An unambiguous question is one that:
- Has a clear, single interpretation
- Has a specific, well-defined answer
- Contains sufficient context to determine the intended meaning
- Cannot be reasonably interpreted in multiple ways

Please analyze the given question and respond with:
1. Your judgment: "AMBIGUOUS" or "UNAMBIGUOUS"
2. A brief explanation of why you made this judgment
3. If ambiguous, list the different possible interpretations

Format your response as:
JUDGMENT: [AMBIGUOUS/UNAMBIGUOUS]
EXPLANATION: [Your explanation]
INTERPRETATIONS: [If ambiguous, list different interpretations]"""

        user_content = f"Question: {question}"
        if use_context and context:
            user_content += f"\n\nContext: {context}"
        
        try:
            # Call appropriate model based on type
            if self.model_name.startswith("gpt"):
                response_text = self._call_openai_api(system_prompt, user_content)
            elif self.model_name.startswith("claude"):
                response_text = self._call_claude_api(system_prompt, user_content)
            elif self.model_name.startswith("Qwen"):
                response_text = self._call_qwen_api(system_prompt, user_content)
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
            
            # Parse the response
            judgment = self._extract_judgment(response_text)
            explanation = self._extract_explanation(response_text)
            interpretations = self._extract_interpretations(response_text)
            
            return {
                "raw_response": response_text,
                "judgment": judgment,
                "explanation": explanation,
                "interpretations": interpretations,
                "is_ambiguous_predicted": judgment == "AMBIGUOUS"
            }
            
        except Exception as e:
            print(f"Error getting {self.model_name} response: {e}")
            return {
                "raw_response": "",
                "judgment": "ERROR",
                "explanation": "",
                "interpretations": [],
                "is_ambiguous_predicted": False
            }
    
    def _extract_judgment(self, response: str) -> str:
        """Extract the judgment from the response."""
        # Look for JUDGMENT: AMBIGUOUS or JUDGMENT: UNAMBIGUOUS
        judgment_match = re.search(r'JUDGMENT:\s*(AMBIGUOUS|UNAMBIGUOUS)', response, re.IGNORECASE)
        if judgment_match:
            return judgment_match.group(1).upper()
        
        # Fallback: look for AMBIGUOUS or UNAMBIGUOUS in the response
        if "AMBIGUOUS" in response.upper() and "UNAMBIGUOUS" not in response.upper():
            return "AMBIGUOUS"
        elif "UNAMBIGUOUS" in response.upper():
            return "UNAMBIGUOUS"
        
        return "UNCLEAR"
    
    def _extract_explanation(self, response: str) -> str:
        """Extract the explanation from the response."""
        explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?=INTERPRETATIONS:|$)', response, re.DOTALL | re.IGNORECASE)
        if explanation_match:
            return explanation_match.group(1).strip()
        return ""
    
    def _extract_interpretations(self, response: str) -> list:
        """Extract interpretations from the response."""
        interpretations_match = re.search(r'INTERPRETATIONS:\s*(.+?)$', response, re.DOTALL | re.IGNORECASE)
        if interpretations_match:
            interpretations_text = interpretations_match.group(1).strip()
            # Split by common separators and clean up
            interpretations = [i.strip() for i in re.split(r'[;\n•-]', interpretations_text) if i.strip()]
            return interpretations
        return []
    
    def _call_openai_api(self, system_prompt: str, user_content: str) -> str:
        """Call OpenAI API."""
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
    
    def _call_claude_api(self, system_prompt: str, user_content: str) -> str:
        """Call Claude API using anthropic library."""
        try:
            import anthropic
            
            # Use the API key passed to the constructor
            if not self.api_key:
                raise ValueError("API key not provided to AmbiguityDetector")
            
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
            
        except Exception as e:
            raise Exception(f"Claude API error: {e}")
    
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
        
        
        
        response = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        
        # For ambiguity detection, we need the full structured response
        # Don't do post-processing that extracts only short answers
        return response
            


def evaluate_ambiguity_detection(data_file: str, model_name: str, output_file: str, 
                                is_ambiguous: bool = False, evaluate_disambiguated: bool = False,
                                max_examples: int = None, api_key: str = None, use_context: bool = False,
                                resume: bool = False):
    """Evaluate ambiguity detection on a dataset."""
    
    # Load data (handle both JSON and JSONL formats)
    data = []
    with open(data_file, 'r') as f:
        try:
            # Try JSON format first
            f.seek(0)
            data = json.load(f)
        except json.JSONDecodeError:
            # Fall back to JSONL format
            f.seek(0)
            data = [json.loads(line) for line in f if line.strip()]
    
    if max_examples:
        data = data[:max_examples]
    
    # Initialize detector
    detector = AmbiguityDetector(model_name, api_key)
    
    # Check for existing results if resume is enabled
    results = []
    correct_predictions = 0
    total_predictions = 0
    start_index = 0
    
    if resume and os.path.exists(output_file):
        print(f"Found existing results file: {output_file}")
        try:
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
            
            # Check if the existing results are compatible
            if (existing_data.get('model') == model_name and 
                existing_data.get('data_file') == data_file and
                existing_data.get('is_ambiguous_ground_truth') == is_ambiguous and
                existing_data.get('evaluate_disambiguated') == evaluate_disambiguated):
                
                results = existing_data.get('results', [])
                correct_predictions = existing_data.get('correct_predictions', 0)
                total_predictions = existing_data.get('total_examples', 0)
                
                # Calculate start index based on existing results
                if evaluate_disambiguated:
                    # For disambiguated questions, count unique original examples processed
                    processed_original_ids = set()
                    for result in results:
                        if 'original_id' in result:
                            processed_original_ids.add(result['original_id'])
                        else:
                            processed_original_ids.add(result['id'])
                    start_index = len(processed_original_ids)
                else:
                    # For regular questions, count results directly
                    start_index = len(results)
                
                print(f"Resuming from example {start_index} (found {len(results)} existing results)")
                print(f"Existing accuracy: {existing_data.get('accuracy', 0):.3f} ({correct_predictions}/{total_predictions})")
            else:
                print("Existing results are incompatible, starting from scratch")
                results = []
                correct_predictions = 0
                total_predictions = 0
                start_index = 0
        except Exception as e:
            print(f"Error loading existing results: {e}")
            print("Starting from scratch")
            results = []
            correct_predictions = 0
            total_predictions = 0
            start_index = 0
    
    print(f"Evaluating ambiguity detection on {len(data)} examples (starting from {start_index})...")
    
    # Function to save intermediate results
    def save_intermediate_results():
        temp_summary = {
            "model": model_name,
            "data_file": data_file,
            "is_ambiguous_ground_truth": is_ambiguous,
            "evaluate_disambiguated": evaluate_disambiguated,
            "use_context": use_context,
            "total_examples": len(data),
            "correct_predictions": correct_predictions,
            "accuracy": correct_predictions / total_predictions if total_predictions > 0 else 0.0,
            "results": results
        }
        with open(output_file, 'w') as f:
            json.dump(temp_summary, f, indent=2)
    
    for i, example in enumerate(tqdm(data, desc="Processing")):
        # Skip already processed examples when resuming
        if i < start_index:
            continue
        question = example.get('question', '')
        context = " ".join(example.get('context', [])) if example.get('context') else ""
        
        # Determine ground truth ambiguity
        if is_ambiguous:
            ground_truth_ambiguous = True
        else:
            ground_truth_ambiguous = False
        
        # For disambiguated questions, they should be unambiguous (already clarified)
        if evaluate_disambiguated and 'disambiguated_qa_pairs' in example:
            ground_truth_ambiguous = False  # Disambiguated questions are now unambiguous
            # Evaluate ALL disambiguated questions, not just the first one
            disambiguated_pairs = example['disambiguated_qa_pairs']
            if disambiguated_pairs and 'questions' in disambiguated_pairs and len(disambiguated_pairs['questions']) > 0:
                # Process each disambiguated question separately
                for j, disambiguated_question in enumerate(disambiguated_pairs['questions']):
                    # Get model prediction for this disambiguated question
                    prediction = detector.detect_ambiguity(disambiguated_question, context, use_context)
                    
                    # Check if prediction is correct (only if no error occurred)
                    is_correct = (prediction['judgment'] != 'ERROR' and 
                                prediction['is_ambiguous_predicted'] == ground_truth_ambiguous)
                    
                    if is_correct:
                        correct_predictions += 1
                    total_predictions += 1
                    
                    # Store result for this disambiguated question
                    result = {
                        "id": f"{example.get('id', f'example_{i}')}_disambiguated_{j}",
                        "original_id": example.get('id', f"example_{i}"),
                        "question": disambiguated_question,
                        "original_question": example.get('question', ''),
                        "ground_truth_ambiguous": ground_truth_ambiguous,
                        "predicted_ambiguous": prediction['is_ambiguous_predicted'],
                        "correct": is_correct,
                        "judgment": prediction['judgment'],
                        "explanation": prediction['explanation'],
                        "interpretations": prediction['interpretations'],
                        "raw_response": prediction['raw_response'],
                        "disambiguated_qa_pairs": example['disambiguated_qa_pairs']
                    }
                    
                    # Add context if used
                    if use_context and context:
                        result["context"] = context
                    
                    results.append(result)
            else:
                # No disambiguated questions available, skip this example
                continue
        else:
            # Regular evaluation (not disambiguated)
            # Get model prediction
            prediction = detector.detect_ambiguity(question, context, use_context)
            
            # Check if prediction is correct (only if no error occurred)
            is_correct = (prediction['judgment'] != 'ERROR' and 
                        prediction['is_ambiguous_predicted'] == ground_truth_ambiguous)
            
            if is_correct:
                correct_predictions += 1
            total_predictions += 1
            
            # Store result
            result = {
                "id": example.get('id', f"example_{i}"),
                "question": question,
                "ground_truth_ambiguous": ground_truth_ambiguous,
                "predicted_ambiguous": prediction['is_ambiguous_predicted'],
                "correct": is_correct,
                "judgment": prediction['judgment'],
                "explanation": prediction['explanation'],
                "interpretations": prediction['interpretations'],
                "raw_response": prediction['raw_response']
            }
            
            # Add context if used
            if use_context and context:
                result["context"] = context
            
            results.append(result)
        
        # Save intermediate results every 10 examples
        if (i + 1) % 10 == 0:
            save_intermediate_results()
    
    # Calculate accuracy
    accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
    
    # Create summary
    summary = {
        "model": model_name,
        "data_file": data_file,
        "is_ambiguous_ground_truth": is_ambiguous,
        "evaluate_disambiguated": evaluate_disambiguated,
        "use_context": use_context,
        "total_examples": len(data),
        "correct_predictions": correct_predictions,
        "accuracy": accuracy,
        "results": results
    }
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Accuracy: {accuracy:.3f} ({correct_predictions}/{total_predictions})")
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='Evaluate LLM ambiguity detection')
    parser.add_argument('--data_file', required=True, help='Path to data file')
    parser.add_argument('--model_name', required=True, help='Model name')
    parser.add_argument('--output_file', required=True, help='Output file path')
    parser.add_argument('--is_ambiguous', action='store_true', help='Whether questions are ambiguous (ground truth)')
    parser.add_argument('--evaluate_disambiguated', action='store_true', help='Evaluate disambiguated questions')
    parser.add_argument('--max_examples', type=int, help='Maximum examples to evaluate')
    parser.add_argument('--api_key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--use_context', action='store_true', help='Use context from dataset')
    parser.add_argument('--resume', action='store_true', help='Resume from existing results file')
    
    args = parser.parse_args()
    
    # Get API key based on model type
    if args.model_name.startswith("gpt"):
        api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("Error: No API key provided. Set OPENAI_API_KEY environment variable or use --api_key")
            return
    elif args.model_name.startswith("claude"):
        api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("Error: No API key provided. Set ANTHROPIC_API_KEY environment variable or use --api_key")
            return
    elif args.model_name.startswith("Qwen"):
        # Qwen models run locally, no API key needed
        api_key = None
    else:
        api_key = args.api_key
    
    # Run evaluation
    evaluate_ambiguity_detection(
        data_file=args.data_file,
        model_name=args.model_name,
        output_file=args.output_file,
        is_ambiguous=args.is_ambiguous,
        evaluate_disambiguated=args.evaluate_disambiguated,
        max_examples=args.max_examples,
        api_key=api_key,
        use_context=args.use_context,
        resume=args.resume
    )

if __name__ == "__main__":
    main()
