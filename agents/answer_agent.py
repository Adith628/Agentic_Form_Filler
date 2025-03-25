#!/usr/bin/env python3
# Answer Generation Agent - Generates appropriate responses to form questions

import logging
import os
import random
import cohere
from typing import List, Dict, Any, Optional, Union

# Import constants for question types
from agents.reasoning_agent import ReasoningAgent

logger = logging.getLogger(__name__)

class AnswerGenerationAgent:
    """
    The Answer Generation Agent is responsible for:
    1. Generating appropriate responses to form questions using Cohere AI
    2. Selecting relevant options for multiple-choice questions
    3. Adapting response length and format based on question type
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Answer Generation Agent with Cohere API.
        
        Args:
            api_key: Optional Cohere API key. If not provided, 
                    will attempt to get from COHERE_API_KEY environment variable.
        """
        logger.info("Initializing Answer Generation Agent")
        
        # Get API key from environment variable if not provided
        if not api_key:
            api_key = os.environ.get("COHERE_API_KEY")
            
        if not api_key:
            logger.warning("No Cohere API key provided. Using mock responses instead.")
            self.client = None
        else:
            # Initialize Cohere client
            try:
                self.client = cohere.Client(api_key)
                logger.info("Cohere client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client: {str(e)}")
                self.client = None
    
    def generate_answer(self, question_text: str, question_type: str, 
                        options: Optional[List[str]] = None) -> Union[str, List[str]]:
        """
        Generate an appropriate answer for the given question.
        
        Args:
            question_text: The text of the question
            question_type: The type of question (text, paragraph, multiple_choice, etc.)
            options: Optional list of choice options for multiple-choice questions
            
        Returns:
            Either a string answer or a list of selected options
        """
        logger.debug(f"Generating answer for question: '{question_text}'")
        
        # Handle different question types
        if question_type == ReasoningAgent.TYPE_TEXT:
            return self._generate_text_answer(question_text, short=True)
            
        elif question_type == ReasoningAgent.TYPE_PARAGRAPH:
            return self._generate_text_answer(question_text, short=False)
            
        elif question_type == ReasoningAgent.TYPE_MULTIPLE_CHOICE:
            return self._select_choice(question_text, options)
            
        elif question_type == ReasoningAgent.TYPE_CHECKBOX:
            return self._select_multiple_choices(question_text, options)
            
        elif question_type == ReasoningAgent.TYPE_DROPDOWN:
            return self._select_choice(question_text, options)
            
        else:
            # Default to a simple response for unknown types
            logger.warning(f"Unknown question type: {question_type}, using default response")
            return self._generate_default_answer()
    
    def _generate_text_answer(self, question_text: str, short: bool = True) -> str:
        """
        Generate a text answer using Cohere AI.
        
        Args:
            question_text: The text of the question
            short: Whether to generate a short or detailed response
            
        Returns:
            Generated text answer
        """
        if not self.client:
            # Use mock response if no Cohere client
            return self._mock_text_answer(question_text, short)
        
        try:
            # Prepare prompt based on question type
            max_tokens = 30 if short else 150
            temperature = 0.7 if short else 0.8
            
            # Create a prompt that instructs the model to answer appropriately
            prompt = self._create_answer_prompt(question_text, short)
            
            # Call Cohere API to generate a response
            response = self.client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                k=0,
                p=0.75,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop_sequences=["###"]
            )
            
            # Extract and clean the generated answer
            answer = response.generations[0].text.strip()
            
            logger.debug(f"Generated answer: '{answer}'")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating text answer: {str(e)}")
            return self._mock_text_answer(question_text, short)
    
    def _create_answer_prompt(self, question_text: str, short: bool) -> str:
        """
        Create a prompt for the Cohere model to answer a question.
        
        Args:
            question_text: The text of the question
            short: Whether to generate a short or detailed response
            
        Returns:
            Prompt string for Cohere
        """
        if short:
            return f"""Answer the following question with a short, concise response (no more than 20 words):
            
Question: {question_text}

Answer:"""
        else:
            return f"""Answer the following question with a detailed, thoughtful response (2-3 sentences):
            
Question: {question_text}

Answer:"""
    
    def _select_choice(self, question_text: str, options: List[str]) -> str:
        """
        Select the most appropriate choice for multiple-choice or dropdown questions.
        
        Args:
            question_text: The text of the question
            options: List of available options
            
        Returns:
            The selected option
        """
        if not options:
            logger.warning("No options provided for choice question")
            return ""
            
        if not self.client:
            # Use mock response if no Cohere client
            return random.choice(options)
        
        try:
            # Create a prompt that asks the model to select the best option
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
            prompt = f"""Select the most appropriate answer to the following question:
            
Question: {question_text}

Options:
{options_text}

Select the best option number:"""
            
            # Call Cohere API to select an option
            response = self.client.generate(
                prompt=prompt,
                max_tokens=5,
                temperature=0.2,
                k=0,
                p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop_sequences=["###"]
            )
            
            # Extract the option number from the response
            answer_text = response.generations[0].text.strip()
            
            # Try to extract a number from the response
            for word in answer_text.split():
                if word.isdigit() and 1 <= int(word) <= len(options):
                    selected_index = int(word) - 1
                    logger.debug(f"Selected option {selected_index + 1}: '{options[selected_index]}'")
                    return options[selected_index]
            
            # If no valid number found, fall back to the first option
            logger.warning(f"Could not extract valid option number from '{answer_text}', using first option")
            return options[0]
            
        except Exception as e:
            logger.error(f"Error selecting choice: {str(e)}")
            return random.choice(options)
    
    def _select_multiple_choices(self, question_text: str, options: List[str]) -> List[str]:
        """
        Select multiple appropriate choices for checkbox questions.
        
        Args:
            question_text: The text of the question
            options: List of available options
            
        Returns:
            List of selected options
        """
        if not options:
            logger.warning("No options provided for checkbox question")
            return []
            
        if not self.client:
            # Use mock response - select 1-3 random options
            num_to_select = random.randint(1, min(3, len(options)))
            return random.sample(options, num_to_select)
        
        try:
            # Create a prompt that asks the model to select multiple options
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
            prompt = f"""Select the most appropriate answers to the following checkbox question (you may select multiple options):
            
Question: {question_text}

Options:
{options_text}

List the numbers of all relevant options (e.g., "1, 3, 4"):"""
            
            # Call Cohere API to select options
            response = self.client.generate(
                prompt=prompt,
                max_tokens=20,
                temperature=0.3,
                k=0,
                p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop_sequences=["###"]
            )
            
            # Extract the option numbers from the response
            answer_text = response.generations[0].text.strip()
            
            # Parse out all numbers
            selected_indices = []
            for word in answer_text.replace(',', ' ').split():
                if word.isdigit() and 1 <= int(word) <= len(options):
                    selected_indices.append(int(word) - 1)
            
            # Ensure at least one option is selected
            if not selected_indices:
                logger.warning(f"No valid options found in '{answer_text}', selecting random option")
                selected_indices = [random.randint(0, len(options) - 1)]
            
            selected_options = [options[i] for i in selected_indices]
            logger.debug(f"Selected {len(selected_options)} options: {selected_options}")
            
            return selected_options
            
        except Exception as e:
            logger.error(f"Error selecting multiple choices: {str(e)}")
            # Fall back to random selection
            num_to_select = random.randint(1, min(3, len(options)))
            return random.sample(options, num_to_select)
    
    def _mock_text_answer(self, question_text: str, short: bool) -> str:
        """
        Generate a mock text answer when Cohere is not available.
        
        Args:
            question_text: The text of the question
            short: Whether to generate a short or detailed response
            
        Returns:
            Mock text answer
        """
        # Sample mock responses
        short_responses = [
            "Yes, definitely.",
            "No, I don't think so.",
            "Sometimes, it depends.",
            "Occasionally, but not often.",
            "Absolutely!",
            "Never tried it before.",
            "I think so.",
            "Not really.",
            "About 5-10 times.",
            "Once a week.",
            "Every day.",
            "John Smith",
            "example@email.com",
            "555-123-4567",
            "New York City"
        ]
        
        long_responses = [
            "I believe this is an important issue that requires careful consideration. There are multiple factors to weigh, and the context matters significantly.",
            "Based on my experience, I would approach this situation by first analyzing the requirements and then developing a step-by-step plan to address each component systematically.",
            "This question touches on several interesting aspects of the topic. On one hand, we should consider the practical implications, while on the other hand, theoretical principles provide valuable guidance.",
            "When faced with this kind of scenario, I typically evaluate the pros and cons before making a decision. This methodical approach has served me well in similar situations.",
            "I have mixed feelings about this matter. While there are clear advantages to one approach, there are also compelling reasons to consider alternatives depending on specific circumstances."
        ]
        
        if short:
            return random.choice(short_responses)
        else:
            return random.choice(long_responses)
    
    def _generate_default_answer(self) -> str:
        """Generate a default answer for unknown question types."""
        default_answers = [
            "Yes",
            "No",
            "Maybe",
            "Not applicable",
            "I prefer not to say",
            "Other"
        ]
        return random.choice(default_answers) 