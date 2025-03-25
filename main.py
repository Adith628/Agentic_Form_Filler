#!/usr/bin/env python3
# Agentic Form Filler - Main Script
# An autonomous agent that intelligently fills out Google Forms

import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Import agents
from agents.reasoning_agent import ReasoningAgent
from agents.answer_agent import AnswerGenerationAgent
from agents.navigation_agent import NavigationAgent

# Import utils
from utils.form_handler import FormHandler
from utils.logger import setup_logger

def main():
    """Main entry point for the Agentic Form Filler application."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Agentic Form Filler")
    
    # Check for form URL as command line argument
    if len(sys.argv) < 2:
        logger.error("Please provide a Google Form URL as argument")
        print("Usage: python main.py <google_form_url>")
        sys.exit(1)
    
    form_url = sys.argv[1]
    logger.info(f"Form URL: {form_url}")
    
    # Initialize the form handler with Selenium
    form_handler = FormHandler(headless=False)  # Set to True for production
    
    try:
        # Open the form
        form_handler.open_form(form_url)
        logger.info("Form opened successfully")
        
        # Initialize agents
        reasoning_agent = ReasoningAgent()
        answer_agent = AnswerGenerationAgent()
        navigation_agent = NavigationAgent(form_handler)
        
        # Process form until completion
        while True:
            # Extract current form elements
            questions = form_handler.extract_questions()
            logger.info(f"Extracted {len(questions)} questions from current page")
            
            if not questions:
                logger.warning("No questions found on page")
                if navigation_agent.is_form_completed():
                    logger.info("Form appears to be completed")
                    break
            
            # Process each question
            for question in questions:
                # Use reasoning agent to analyze the question
                question_type, required = reasoning_agent.analyze_question(question)
                logger.info(f"Question: '{question['text']}' - Type: {question_type}, Required: {required}")
                
                # Generate answer using the answer agent
                answer = answer_agent.generate_answer(
                    question_text=question['text'],
                    question_type=question_type,
                    options=question.get('options', [])
                )
                logger.info(f"Generated answer: {answer}")
                
                # Fill the answer
                form_handler.fill_answer(question['element'], question_type, answer)
                logger.info(f"Answer filled for question: '{question['text']}'")
            
            # Navigate to next page or submit form
            if not navigation_agent.navigate_next():
                logger.info("Navigation complete - form submitted or no next button found")
                break
            
            logger.info("Navigated to next page")
        
        logger.info("Form filling process completed successfully")
        
    except Exception as e:
        logger.error(f"Error during form filling: {str(e)}")
    finally:
        # Close the browser
        form_handler.close()
        logger.info("Browser closed")

if __name__ == "__main__":
    main() 