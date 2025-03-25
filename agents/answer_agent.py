"""
Answer Generation Agent using Cohere AI.
"""
import random
import time
import re
from typing import Dict, List, Any, Optional, Union, Tuple
import cohere
from loguru import logger
from ..config import get_config
from ..utils.logger import log_structured_answer

class AnswerAgent:
    """
    Agent for generating answers to form questions using Cohere AI.
    
    This agent is responsible for generating contextually appropriate responses
    for different types of form questions.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the answer agent.
        
        Args:
            api_key: Cohere API key (defaults to config)
        """
        # Get API key from config if not provided
        if not api_key:
            api_key = get_config("COHERE_API_KEY")
        
        if not api_key:
            raise ValueError("Cohere API key not found. Please set it in config or .env file.")
        
        self.client = cohere.Client(api_key)
        self.config = get_config("COHERE_CONFIG")
        self.question_types = get_config("QUESTION_TYPES")
        logger.info("Answer agent initialized with Cohere client")
    
    def generate_answer(self, question: Dict[str, Any]) -> Union[str, int, List[int]]:
        """
        Generate an answer for the given question.
        
        Args:
            question: Dictionary containing question data including:
              - text: Question text
              - type: Question type (text, multiple_choice, etc.)
              - options: List of options for multiple choice/checkbox
            
        Returns:
            Generated answer appropriate for the question type
        """
        question_text = question['text']
        question_type = question['type']
        logger.info(f"Generating answer for question: '{question_text}' (Type: {question_type})")
        
        try:
            # Choose appropriate answering strategy based on question type
            if question_type == self.question_types["TEXT"]:
                return self._generate_text_answer(question)
            elif question_type == self.question_types["PARAGRAPH"]:
                return self._generate_paragraph_answer(question)
            elif question_type == self.question_types["MULTIPLE_CHOICE"]:
                return self._select_multiple_choice_answer(question)
            elif question_type == self.question_types["CHECKBOX"]:
                return self._select_checkbox_answers(question)
            elif question_type == self.question_types["DROPDOWN"]:
                return self._select_dropdown_answer(question)
            else:
                logger.warning(f"Unknown question type: {question_type}")
                return ""
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            # Provide a fallback answer
            return self._generate_fallback_answer(question)
    
    def _generate_text_answer(self, question: Dict[str, Any]) -> str:
        """
        Generate a short text answer using Cohere.
        
        Args:
            question: Text question dictionary
            
        Returns:
            Generated text answer
        """
        try:
            logger.info("Generating text answer using Cohere API")
            
            # Create a prompt for the text answer
            prompt = f"""
            Please provide a brief and realistic answer to this question: 
            "{question['text']}"
            
            Think about how a real person would answer this. Keep your answer brief and natural.
            Ensure your answer demonstrates honesty and clarity.
            """
            
            response = self.client.generate(
                prompt=prompt,
                model=self.config.get("model", "command"),
                max_tokens=self.config.get("max_tokens", 20),
                temperature=self.config.get("temperature", 0.7),
                response_format=self.config.get("response_format", "text"),
            )
            
            # Process and clean the response
            answer = response.generations[0].text.strip()
            
            # Enforce a reasonable length (30 chars) for text fields
            if len(answer) > 30:
                answer = answer[:30]
            
            logger.info(f"Generated text answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error generating text answer with Cohere: {str(e)}")
            return "Sample response"
    
    def _generate_paragraph_answer(self, question: Dict[str, Any]) -> str:
        """
        Generate a longer paragraph answer using Cohere.
        
        Args:
            question: Paragraph question dictionary
            
        Returns:
            Generated paragraph answer
        """
        try:
            logger.info("Generating paragraph answer using Cohere API")
            
            # Create a prompt for the paragraph answer
            prompt = f"""
            Please provide a detailed response (2-3 sentences) to this question: 
            "{question['text']}"
            
            Think about how a real person would answer this. Be thoughtful and conversational.
            Provide specific examples or details where appropriate to make your answer authentic.
            """
            
            response = self.client.generate(
                prompt=prompt,
                model=self.config.get("model", "command"),
                max_tokens=self.config.get("max_tokens", 100),
                temperature=self.config.get("temperature", 0.7),
                response_format=self.config.get("response_format", "text"),
            )
            
            # Process and clean the response
            answer = response.generations[0].text.strip()
            
            logger.info(f"Generated paragraph answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error generating paragraph answer with Cohere: {str(e)}")
            return "This is a sample paragraph response. It contains multiple sentences to demonstrate a longer form answer that would be appropriate for a text area field in a form."
    
    def _select_multiple_choice_answer(self, question: Dict[str, Any]) -> int:
        """
        Select an appropriate option for a multiple-choice question.
        
        Args:
            question: Multiple choice question dictionary
            
        Returns:
            Index of selected option
        """
        try:
            options = question.get('options', [])
            if not options:
                # If no options available, return default
                logger.warning("No options available for multiple choice question, using default answer")
                return 0
            
            logger.info(f"Selecting from {len(options)} multiple choice options")
            
            # If fewer than 4 options, sometimes just pick randomly for efficiency
            if len(options) < 4 and random.random() < 0.3:
                selected_index = random.randint(0, len(options) - 1)
                logger.info(f"Randomly selected option {selected_index}: {options[selected_index]}")
                return selected_index
            
            # Create a prompt for selecting an option with reasoning
            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            prompt = f"""
            Question: {question['text']}
            
            Options:
            {options_text}
            
            From the options above, which one would be the most appropriate response? 
            First provide a brief explanation of your reasoning, considering what would be a good, honest answer.
            End with "Selected option: X" where X is the number of the option.
            """
            
            response = self.client.generate(
                prompt=prompt,
                model=self.config.get("model", "command"),
                max_tokens=80,  # Increased to allow for explanation
                temperature=0.3,  # Lower temperature for more deterministic results
                response_format="text",
            )
            
            # Extract the option number and reasoning from the response
            answer_text = response.generations[0].text.strip()
            
            # Log the reasoning
            logger.info(f"AI reasoning: {answer_text}")
            
            # Try to extract a number from the response
            selected_index = 0  # Default to first option
            
            # Look for "Selected option: X" pattern
            match = re.search(r"Selected option:\s*(\d+)", answer_text)
            if match:
                option_num = int(match.group(1))
                if 1 <= option_num <= len(options):
                    selected_index = option_num - 1
                    logger.info(f"AI selected option {option_num} ({options[selected_index]})")
            else:
                # Try to extract any number if the pattern wasn't found
                for word in answer_text.split():
                    if word.isdigit() and 1 <= int(word) <= len(options):
                        selected_index = int(word) - 1
                        logger.info(f"Extracted option {selected_index+1} from AI response")
                        break
                
                # Default to random if we couldn't parse the response
                if selected_index == 0 and len(options) > 1:
                    selected_index = random.randint(0, len(options) - 1)
                    logger.info(f"Defaulting to random option {selected_index+1}: {options[selected_index]}")
            
            return selected_index
        except Exception as e:
            logger.error(f"Error selecting multiple choice answer: {str(e)}")
            # Default to first option on error
            return 0
    
    def _select_checkbox_answers(self, question: Dict[str, Any]) -> List[int]:
        """
        Select appropriate options for a checkbox question.
        
        Args:
            question: Checkbox question dictionary
            
        Returns:
            List of indices of selected options
        """
        try:
            options = question.get('options', [])
            if not options:
                # If no options available, return empty list
                logger.warning("No options available for checkbox question")
                return []
            
            logger.info(f"Selecting from {len(options)} checkbox options")
            
            # If there are many options, use Cohere to help decide
            if len(options) > 3:
                # Create a prompt for selecting multiple options
                options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
                prompt = f"""
                Question: {question['text']}
                
                Options:
                {options_text}
                
                From the options above, select all that would be appropriate. You can select multiple options.
                First explain your reasoning for choosing certain options, then end with 
                "Selected options: X, Y, Z" where X, Y, Z are the numbers of the selected options.
                """
                
                response = self.client.generate(
                    prompt=prompt,
                    model=self.config.get("model", "command"),
                    max_tokens=100,
                    temperature=0.5,
                    response_format="text",
                )
                
                answer_text = response.generations[0].text.strip()
                logger.info(f"AI reasoning for checkbox selection: {answer_text}")
                
                # Try to extract numbers from "Selected options: X, Y, Z" pattern
                selected_indices = []
                match = re.search(r"Selected options?:\s*([\d,\s]+)", answer_text)
                if match:
                    options_str = match.group(1)
                    # Extract all numbers
                    for num_str in re.finditer(r'\d+', options_str):
                        num = int(num_str.group(0))
                        if 1 <= num <= len(options):
                            selected_indices.append(num - 1)  # Convert to 0-based index
                
                # If AI didn't select any options, fall back to random selection
                if not selected_indices:
                    logger.info("AI didn't clearly select options, falling back to random selection")
                    num_selections = random.randint(1, min(3, len(options)))
                    selected_indices = random.sample(range(len(options)), num_selections)
            else:
                # For simplicity on checkboxes with few options, select 1-2 options randomly
                num_selections = random.randint(1, min(2, len(options)))
                selected_indices = random.sample(range(len(options)), num_selections)
            
            # Ensure we always select at least one option
            if not selected_indices and options:
                selected_indices = [0]  # Select first option as fallback
            
            selected_options = [options[i] for i in selected_indices]
            logger.info(f"Selected {len(selected_indices)} checkbox options: {selected_options}")
            
            return selected_indices
        except Exception as e:
            logger.error(f"Error selecting checkbox answers: {str(e)}")
            # Default to first option on error
            return [0] if question.get('options') else []
    
    def _select_dropdown_answer(self, question: Dict[str, Any]) -> int:
        """
        Select an appropriate option for a dropdown question.
        
        Args:
            question: Dropdown question dictionary
            
        Returns:
            Index of selected option
        """
        logger.info("Treating dropdown selection like multiple choice")
        # Dropdown selection is similar to multiple choice
        return self._select_multiple_choice_answer(question)
    
    def _generate_fallback_answer(self, question: Dict[str, Any]) -> Union[str, int, List[int]]:
        """
        Generate a fallback answer when API or processing fails.
        
        Args:
            question: Question dictionary that failed generation
            
        Returns:
            Fallback answer appropriate for the question type
        """
        question_type = question['type']
        logger.warning(f"Using fallback answer for {question_type} question: {question['text']}")
        
        # Provide appropriate fallback based on question type
        if question_type == self.question_types["TEXT"]:
            return "Fallback response"
        elif question_type == self.question_types["PARAGRAPH"]:
            return "This is a fallback response for a paragraph question. It is provided when the AI generation fails for some reason."
        elif question_type == self.question_types["MULTIPLE_CHOICE"] or question_type == self.question_types["DROPDOWN"]:
            return 0  # First option
        elif question_type == self.question_types["CHECKBOX"]:
            return [0] if question.get('options') else []  # First option
        else:
            return "" 