#!/usr/bin/env python3
"""
Judge LLM predictions to classify:
1. Whether the response is a refusal (True/False)
2. Whether it's asking for a clarifying question (True/False)
3. Whether the model answered the question (True/False) - even if it also asks for clarification
4. Whether the model ONLY answered (True/False) - answered without refusal or clarifying questions

Uses gpt-5-nano-2025-08-07 as the judge model.
"""

import json
import argparse
import os
from typing import Dict, List, Any
from openai import OpenAI
from tqdm import tqdm

class PredictionJudge:
    def __init__(self, judge_model: str = "gpt-5-nano-2025-08-07", api_key: str = None):
        """Initialize the judge model."""
        self.judge_model = judge_model
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set and no API key provided")
        self.client = OpenAI(api_key=self.api_key)
    
    def judge_prediction(self, prediction: str, question: str = "", max_retries: int = 3) -> Dict[str, Any]:
        """
        Judge a prediction to classify:
        1. If it's a refusal
        2. If it's asking for clarification
        3. If it answered the question (even if it also asks for clarification)
        4. If it ONLY answered (no refusal, no clarifying question)
        
        Returns:
            {
                "success": bool,
                "judge_refusal": bool (only if success=True),
                "judge_asking_clarify_Q": bool (only if success=True),
                "judge_answered": bool (only if success=True),
                "judge_only_answered": bool (only if success=True)
            }
        """
        system_prompt = """You are an expert judge evaluating LLM responses. Your task is to classify responses into four categories:

1. **Refusal**: The response refuses to answer the question or states it cannot answer. This includes:
   - Explicit refusals ("I cannot", "I don't know", "I'm not able to", "I don't have information")
   - Safety refusals or policy-based refusals
   - Any response that indicates the model cannot or will not provide an answer
   - Mark as TRUE only if there's an explicit refusal, even if the model also provides some information

2. **Asking for Clarifying Question**: The response asks the user for clarification, more information, or disambiguation. This includes:
   - Questions asking for more context ("Could you clarify?", "What do you mean by...?", "Can you provide more details?")
   - Requests for disambiguation ("Are you asking about...?", "Did you mean...?")
   - Any response that seeks additional information before or while answering
   - Mark as TRUE if the response asks any clarifying question, even if it also provides an answer

3. **Answered**: The response provides an actual answer to the question, regardless of whether it also:
   - Asks for clarification
   - Refuses (though typically these don't co-occur)
   - Provides additional context or explanation
   - Mark as TRUE if there's any substantive answer to the question, even if the model guesses or is uncertain
   - Mark as TRUE even if the answer is provided alongside a clarifying question
   - Mark as FALSE only if the response contains no actual answer (e.g., only refusal, only asking for clarification without providing any answer)

4. **Only Answered**: The response provides an answer AND does NOT refuse AND does NOT ask for clarification. This means:
   - The model directly answered the question
   - No refusal is present
   - No clarifying question is asked
   - This is a pure, direct answer without additional requests or refusals
   - Mark as TRUE only if judge_answered is TRUE AND judge_refusal is FALSE AND judge_asking_clarify_Q is FALSE

Important notes:
- These categories are NOT mutually exclusive:
  - A response can answer while also asking for clarification (judge_answered=true, judge_asking_clarify_Q=true, judge_only_answered=false)
  - A response can be just a refusal (judge_refusal=true, judge_answered=false)
  - A response can be just a clarifying question without an answer (judge_asking_clarify_Q=true, judge_answered=false)
- Be strict: only mark as refusal if there's an explicit refusal
- Be strict: only mark as asking for clarification if there's an explicit question or request
- Be lenient for "answered": mark as true if any answer is provided, even if uncertain or accompanied by clarification requests

Output your judgment as a JSON object with exactly this format:
{
    "judge_refusal": true or false,
    "judge_asking_clarify_Q": true or false,
    "judge_answered": true or false,
    "judge_only_answered": true or false
}

Do not include any other text, only the JSON object."""

        user_content = f"""Original Question: {question}

Model Response: {prediction}

Please classify this response. Output only the JSON object with judge_refusal, judge_asking_clarify_Q, judge_answered, and judge_only_answered."""
        
        for attempt in range(max_retries):
            try:
                # Use new responses.create API for gpt-5 models
                if self.judge_model.startswith("gpt-5"):
                    # Combine system prompt and user content
                    full_input = f"{system_prompt}\n\n{user_content}"
                    
                    response = self.client.responses.create(
                        model=self.judge_model,
                        input=full_input,
                        reasoning={"effort": "low"},
                        text={"verbosity": "low"}
                    )
                    
                    response_text = response.output_text.strip()
                else:
                    # Use chat completions API for other models
                    response = self.client.chat.completions.create(
                        model=self.judge_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        max_tokens=200,
                        temperature=0.0
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                
                # Try to parse JSON from the response
                # Sometimes the response might have markdown code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                # Parse JSON
                try:
                    result = json.loads(response_text)
                    judge_refusal = bool(result.get("judge_refusal", False))
                    judge_asking = bool(result.get("judge_asking_clarify_Q", False))
                    judge_answered = bool(result.get("judge_answered", False))
                    judge_only_answered = bool(result.get("judge_only_answered", False))
                    
                    # Ensure logical consistency: judge_only_answered can only be true if judge_answered is true and both refusal and asking are false
                    if judge_only_answered and not (judge_answered and not judge_refusal and not judge_asking):
                        judge_only_answered = False
                    
                    return {
                        "success": True,
                        "judge_refusal": judge_refusal,
                        "judge_asking_clarify_Q": judge_asking,
                        "judge_answered": judge_answered,
                        "judge_only_answered": judge_only_answered
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract boolean values manually
                    response_lower = response_text.lower()
                    judge_refusal = "judge_refusal" in response_lower and ("true" in response_lower or "yes" in response_lower.split())
                    judge_asking = "judge_asking_clarify_q" in response_lower and ("true" in response_lower or "yes" in response_lower.split())
                    judge_answered = "judge_answered" in response_lower and ("true" in response_lower or "yes" in response_lower.split())
                    judge_only_answered = "judge_only_answered" in response_lower and ("true" in response_lower or "yes" in response_lower.split())
                    
                    # Ensure logical consistency
                    if judge_only_answered and not (judge_answered and not judge_refusal and not judge_asking):
                        judge_only_answered = False
                    
                    return {
                        "success": True,
                        "judge_refusal": judge_refusal,
                        "judge_asking_clarify_Q": judge_asking,
                        "judge_answered": judge_answered,
                        "judge_only_answered": judge_only_answered
                    }
            
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error on attempt {attempt + 1}: {e}, retrying...")
                else:
                    print(f"All {max_retries} attempts failed: {e}")
                    # Return failure status without judge fields
                    return {
                        "success": False
                    }
        
        # If all retries exhausted without success
        return {
            "success": False
        }


def process_result_file(input_file: str, output_file: str, judge: PredictionJudge, resume: bool = False):
    """
    Process a single result file, adding judge classifications.
    
    Args:
        input_file: Path to input result file
        output_file: Path to output file with judge classifications
        judge: PredictionJudge instance
        resume: If True, resume from existing output file
    """
    # Load input data
    print(f"Loading results from {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Load existing results if resuming
    existing_data = None
    processed_indices = set()
    if resume and os.path.exists(output_file):
        print(f"Found existing output file: {output_file}, resuming...")
        try:
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
            
            # Check which items are fully processed
            for i, item in enumerate(existing_data):
                # Consider processed if all required fields exist (regardless of success status)
                # This includes both successful (judge_success=True) and failed (judge_success=False) items
                judge_success = item.get('judge_success', None)
                has_all_fields = ('judge_refusal' in item and 'judge_asking_clarify_Q' in item and 
                                  'judge_answered' in item and 'judge_only_answered' in item)
                
                if judge_success is True and has_all_fields:
                    # Fully processed with success
                    processed_indices.add(i)
                elif judge_success is False and has_all_fields:
                    # Fully processed but failed - don't retry (fields exist with None values)
                    processed_indices.add(i)
                elif judge_success is None and has_all_fields:
                    # Old format without success field - assume successful and processed
                    processed_indices.add(i)
                elif 'judge_refusal' in item and 'judge_asking_clarify_Q' in item:
                    # Very old format with only 2 fields - will need to be re-processed
                    pass
            
            print(f"Found {len(processed_indices)} already processed items out of {len(existing_data)} in existing file")
            
            # Check if input and existing data lengths match
            if len(existing_data) != len(data):
                print(f"Warning: Existing file has {len(existing_data)} items, but input has {len(data)} items.")
                print("Will process all items from input file, preserving existing judgments where indices match.")
        except Exception as e:
            print(f"Error loading existing file: {e}, starting fresh")
            existing_data = None
    
    # Process each entry
    print(f"Processing {len(data)} entries...")
    results = []
    
    for i, item in enumerate(tqdm(data, desc="Judging predictions")):
        # If resuming and already processed, use existing result
        if i in processed_indices and existing_data is not None and i < len(existing_data):
            # Ensure all judge fields exist (for backward compatibility)
            existing_item = existing_data[i].copy()
            
            # Ensure judge_success field exists
            if 'judge_success' not in existing_item:
                existing_item['judge_success'] = True  # Assume success if fields exist
            
            # Ensure all judge fields exist (set to False if missing for backward compatibility)
            if 'judge_refusal' not in existing_item:
                existing_item['judge_refusal'] = False
            if 'judge_asking_clarify_Q' not in existing_item:
                existing_item['judge_asking_clarify_Q'] = False
            if 'judge_answered' not in existing_item:
                existing_item['judge_answered'] = False
            if 'judge_only_answered' not in existing_item:
                existing_item['judge_only_answered'] = False
            
            # Note: Fields may be None if judge_success=False, which is correct
            results.append(existing_item)
            continue
        
        # Create a copy of the item
        result_item = item.copy()
        
        # Get prediction and question
        prediction = item.get('prediction', '')
        question = item.get('disambiguated_question') or item.get('original_question', '')
        
        # Judge the prediction
        if prediction:
            judgment = judge.judge_prediction(prediction, question)
            result_item['judge_success'] = judgment.get('success', False)
            
            # Always set judge fields - use None if unsuccessful
            if judgment.get('success', False):
                result_item['judge_refusal'] = judgment.get('judge_refusal', False)
                result_item['judge_asking_clarify_Q'] = judgment.get('judge_asking_clarify_Q', False)
                result_item['judge_answered'] = judgment.get('judge_answered', False)
                result_item['judge_only_answered'] = judgment.get('judge_only_answered', False)
            else:
                # Failed - set fields to None (not True/False) to indicate unknown/undetermined
                result_item['judge_refusal'] = None
                result_item['judge_asking_clarify_Q'] = None
                result_item['judge_answered'] = None
                result_item['judge_only_answered'] = None
        else:
            # Empty prediction - mark as unsuccessful
            result_item['judge_success'] = False
            result_item['judge_refusal'] = None
            result_item['judge_asking_clarify_Q'] = None
            result_item['judge_answered'] = None
            result_item['judge_only_answered'] = None
        
        results.append(result_item)
        
        # Save periodically (every 10 items) to avoid losing progress
        if (i + 1) % 10 == 0:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
    
    # Final save
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved results to {output_file}")


def process_all_files(input_dir: str, output_dir: str, judge_model: str = "gpt-5-nano-2025-08-07", api_key: str = None, resume: bool = False):
    """
    Process all result files in the input directory.
    
    Args:
        input_dir: Directory containing input result files
        output_dir: Directory to save output files with judge classifications
        judge_model: Model to use as judge
        api_key: API key for judge model
        resume: If True, resume from existing output files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize judge
    judge = PredictionJudge(judge_model=judge_model, api_key=api_key)
    
    # Find all result files
    result_files = [f for f in os.listdir(input_dir) if f.endswith('_results.json')]
    
    print(f"Found {len(result_files)} result files to process")
    
    for result_file in result_files:
        input_path = os.path.join(input_dir, result_file)
        output_path = os.path.join(output_dir, result_file)
        
        print(f"\n{'='*80}")
        print(f"Processing: {result_file}")
        print(f"{'='*80}")
        
        try:
            process_result_file(input_path, output_path, judge, resume=resume)
        except Exception as e:
            print(f"Error processing {result_file}: {e}")
            import traceback
            traceback.print_exc()
            continue


def main():
    parser = argparse.ArgumentParser(description="Judge LLM predictions for refusals and clarifying questions")
    parser.add_argument('--input_dir', default='results_all_models', help='Input directory containing result files')
    parser.add_argument('--output_dir', default='results_all_models_judge', help='Output directory for judged results')
    parser.add_argument('--judge_model', default='gpt-5-nano-2025-08-07', help='Model to use as judge (default: gpt-5-nano-2025-08-07)')
    parser.add_argument('--api_key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--resume', action='store_true', help='Resume from existing output files')
    parser.add_argument('--file', help='Process a single file (relative to input_dir)')
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute if needed
    if not os.path.isabs(args.input_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        args.input_dir = os.path.join(os.path.dirname(script_dir), args.input_dir)
    if not os.path.isabs(args.output_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        args.output_dir = os.path.join(os.path.dirname(script_dir), args.output_dir)
    
    # Process single file or all files
    if args.file:
        input_path = os.path.join(args.input_dir, args.file)
        output_path = os.path.join(args.output_dir, args.file)
        
        if not os.path.exists(input_path):
            print(f"Error: File not found: {input_path}")
            return
        
        judge = PredictionJudge(judge_model=args.judge_model, api_key=args.api_key)
        process_result_file(input_path, output_path, judge, resume=args.resume)
    else:
        process_all_files(args.input_dir, args.output_dir, args.judge_model, args.api_key, resume=args.resume)


if __name__ == "__main__":
    main()

