import os
import json
import random
import anthropic
from typing import List, Dict, Optional, Tuple

class AIService:
    """Handles all AI-related operations: Claude API, prompt building, answer balancing"""
    
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
    
    def generate_questions(self, notes: str, num_questions: int = 6, 
                          question_type: str = "mcq", difficulty: str = "normal") -> Tuple[Optional[List[Dict]], str]:
        """Generate quiz questions using Claude API"""
        if not self.api_key:
            return None, "no_api_key"
        
        try:
            prompt = self._build_prompt(notes, num_questions, question_type, difficulty)
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response and response.content:
                return self._process_response(response.content[0].text, num_questions, question_type, difficulty)
            return None, "empty_response"
            
        except anthropic.APIConnectionError:
            return None, "api_error"
        except anthropic.RateLimitError:
            return None, "quota_exceeded"
        except anthropic.APIStatusError as e:
            return None, "auth_error" if e.status_code == 401 else "api_error"
        except Exception:
            return None, "api_error"
    
    def _build_prompt(self, notes: str, num_questions: int, question_type: str, difficulty: str) -> str:
        """Build optimized prompt for Claude"""
        truncated_notes = notes[:1500]
        
        type_instructions = {
            "mcq": f"Generate exactly {num_questions} multiple-choice questions with 4 options (A, B, C, D).",
            "tf": f"Generate exactly {num_questions} True/False questions with options ['True', 'False']."
        }
        
        difficulty_instructions = {
            "normal": "Target basic factual knowledge and general understanding.",
            "difficult": "Make questions more obscure, indirect, and challenging."
        }
        
        return f"""
You are an expert educational assistant creating quiz questions.

INPUT INTERPRETATION:
- If input is detailed notes, base questions strictly on that material.
- If input is a short phrase or topic name, generate questions based on widely accepted knowledge.

REQUIREMENTS:
{type_instructions.get(question_type, type_instructions['mcq'])}
{difficulty_instructions.get(difficulty, difficulty_instructions['normal'])}

OUTPUT FORMAT (JSON only, no extra text):
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correctAnswer": 0
    }}
  ]
}}

INPUT CONTENT:
{truncated_notes}
"""
    
    def _process_response(self, response_text: str, num_questions: int, 
                          question_type: str, difficulty: str) -> Tuple[Optional[List[Dict]], str]:
        """Process and validate API response"""
        try:
            json_str = self._extract_json(response_text)
            if not json_str:
                return None, "invalid_response"
            
            questions_data = json.loads(json_str)
            raw_questions = questions_data.get('questions', [])[:num_questions]
            
            processed = []
            for q in raw_questions:
                if not all(k in q for k in ['question', 'options', 'correctAnswer']):
                    continue
                
                options = q['options']
                correct = q['correctAnswer']
                expected_count = 4 if question_type == "mcq" else 2
                
                if len(options) != expected_count or not isinstance(correct, int) or correct >= len(options):
                    continue
                
                if question_type == "tf" and options not in (["True", "False"], ["False", "True"]):
                    continue
                
                q.update({"question_type": question_type, "difficulty": difficulty})
                processed.append(q)
            
            if not processed:
                return None, "no_valid_questions"
            
            if question_type == "mcq" and len(processed) >= 2:
                processed = self._balance_answers(processed)
            
            return processed, "success"
            
        except json.JSONDecodeError:
            return None, "parse_error"
        except Exception:
            return None, "process_error"
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from response text"""
        start = text.find('{')
        end = text.rfind('}') + 1
        return text[start:end] if start >= 0 and end > start else None
    
    def _balance_answers(self, questions: List[Dict]) -> List[Dict]:
        """Distribute correct answers across A, B, C, D to prevent patterns"""
        if len(questions) <= 1:
            return questions
        
        positions = [0, 1, 2, 3]
        position_count = {0: 0, 1: 0, 2: 0, 3: 0}
        
        # Count current distribution
        for q in questions:
            correct = q.get('correctAnswer')
            if correct in position_count:
                position_count[correct] += 1
        
        total = len(questions)
        base = total // 4
        remainder = total % 4
        target = {i: base + (1 if i < remainder else 0) for i in positions}
        
        # Check if rebalancing needed
        if all(position_count[p] <= target[p] + 1 for p in positions):
            return questions
        
        # Rebalance
        indices = list(range(len(questions)))
        random.shuffle(indices)
        
        for i in indices:
            q = questions[i]
            current = q.get('correctAnswer')
            options = q.get('options', [])
            
            if current not in position_count or position_count[current] <= target.get(current, 0):
                continue
            
            underused = [p for p in positions if position_count.get(p, 0) < target.get(p, 0) and p < len(options)]
            
            if underused:
                new_pos = min(underused, key=lambda p: position_count.get(p, 0))
                if current < len(options) and new_pos < len(options):
                    # Swap options
                    options[current], options[new_pos] = options[new_pos], options[current]
                    q['correctAnswer'] = new_pos
                    position_count[current] -= 1
                    position_count[new_pos] = position_count.get(new_pos, 0) + 1
        
        return questions