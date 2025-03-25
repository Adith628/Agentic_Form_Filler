"""
Main form filler module that orchestrates the agents to fill out Google Forms.
"""
import time
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from selenium.webdriver.remote.webelement import WebElement
from loguru import logger
from .browser.browser_handler import BrowserHandler
from .agents.reasoning_agent import ReasoningAgent, FormQuestion
from .agents.answer_agent import AnswerAgent
from .agents.navigation_agent import NavigationAgent
from .utils.logger import setup_logger, log_qa_entry, log_structured_question, log_structured_answer
from .config import get_config

class FormFiller:
    """
    Main class for filling out Google Forms using the agent system.
    
    This class orchestrates the Reasoning, Answer, and Navigation agents
    to analyze, fill out, and navigate through Google Forms.
    """
    
    def __init__(self, 
                browser_handler: Optional[BrowserHandler] = None,
                cohere_api_key: Optional[str] = None,
                config: Optional[Dict[str, Any]] = None):
        """
        Initialize the form filler.
        
        Args:
            browser_handler: Custom browser handler (or None to create one)
            cohere_api_key: Cohere API key (defaults to config)
            config: Custom configuration (uses default if None)
        """
        # Initialize configuration
        self.config = config or get_config("FORM_FILLER_CONFIG")
        
        # Initialize browser handler
        self.browser_handler = browser_handler or BrowserHandler()
        
        # Initialize agents
        self.reasoning_agent = ReasoningAgent(self.browser_handler)
        self.answer_agent = AnswerAgent(cohere_api_key)
        self.navigation_agent = NavigationAgent(self.browser_handler)
        
        # Initialize statistics
        self.current_page = 0
        self.questions_answered = 0
        self.total_questions = 0
        
        logger.info("Form filler initialized successfully")
    
    def fill_form(self, form_url: str) -> bool:
        """
        Fill a form at the specified URL.
        
        Args:
            form_url: URL of the form to fill
            
        Returns:
            True if form was filled successfully, False otherwise
        """
        try:
            # Navigate to the form
            if not self.browser_handler.navigate_to(form_url):
                logger.error(f"Failed to navigate to {form_url}")
                return False
            
            logger.info(f"Starting to fill form at {form_url}")
            start_time = time.time()
            
            # Fill the form page by page
            form_complete = False
            
            while not form_complete:
                self.current_page += 1
                logger.info(f"Processing page {self.current_page}")
                
                # Process the current page
                page_processed = self.process_current_page()
                
                if not page_processed:
                    logger.warning(f"Failed to process page {self.current_page}")
                    return False
                
                # Check what action to take next
                next_action = self.navigation_agent.determine_next_action()
                
                if next_action == "next":
                    # Go to the next page
                    if not self.navigation_agent.navigate_to_next_page():
                        logger.error("Failed to navigate to next page")
                        return False
                    # Allow time for page transition
                    time.sleep(1)
                
                elif next_action == "submit":
                    # Submit the form
                    logger.info("Form completed, submitting...")
                    if not self.navigation_agent.submit_form():
                        logger.error("Failed to submit form")
                        return False
                    form_complete = True
                
                elif next_action == "complete":
                    # Form is already complete
                    logger.info("Form has been completed successfully")
                    form_complete = True
                
                else:
                    logger.error("Unknown navigation action, stopping")
                    return False
            
            # Calculate and log statistics
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info("="*80)
            logger.info(f"Form filling completed in {duration:.2f} seconds")
            logger.info(f"Processed {self.current_page} pages")
            logger.info(f"Answered {self.questions_answered} questions")
            logger.info("="*80)
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            logger.debug("Exception details:", exc_info=True)
            return False
        finally:
            # Capture screenshot of final state
            self.browser_handler.take_screenshot("form_final_state.png")
    
    def process_current_page(self):
        """
        Process the current page, extracting questions and generating answers.
        
        Returns:
            bool: True if the page was processed successfully, False otherwise
        """
        try:
            # Extract all questions on the current page
            questions = self.reasoning_agent.extract_questions(self.browser_handler.get_page_source())
            if not questions:
                logger.warning("No questions found on the current page.")
                return False
                
            logger.info(f"Found {len(questions)} questions on the current page.")
            
            # Create a divider for better log readability
            logger.info("="*80)
            
            # Track question number for structured logging
            total_questions = len(questions)
            question_number = 0
                
            for question in questions:
                question_number += 1
                logger.info("-"*50)
                
                # Log the question structure
                logger.info(f"QUESTION {question_number}/{total_questions}:")
                logger.info(f"TEXT: {question['text']}")
                logger.info(f"TYPE: {question['type']}")
                
                options = None
                if 'options' in question and question['options']:
                    options = question['options']
                    logger.info("OPTIONS:")
                    for i, option in enumerate(options):
                        logger.info(f"  [{i}] {option}")
                
                # Create structured question record
                structured_q = log_structured_question(
                    question_text=question['text'],
                    question_type=question['type'],
                    question_number=question_number,
                    total_questions=total_questions,
                    options=options
                )
                
                logger.info("-"*30 + " GENERATING ANSWER " + "-"*30)
                # Generate an answer for the question
                answer = self.answer_agent.generate_answer(question)
                
                # Create structured answer record
                structured_a = log_structured_answer(
                    answer=answer,
                    question_type=question['type'],
                    options=options
                )
                
                # Log to structured jsonl file
                log_qa_entry(structured_q, structured_a)
                
                logger.info("-"*30 + " FILLING ANSWER " + "-"*30)
                
                # Log the selected answer
                if question['type'] == 'checkbox':
                    selected_options = [options[i] for i in answer if i < len(options)]
                    logger.info(f"ANSWER: Selected checkboxes: {selected_options}")
                elif question['type'] in ['multiple_choice', 'dropdown'] and options:
                    if isinstance(answer, int) and 0 <= answer < len(options):
                        logger.info(f"ANSWER: Selected option [{answer}]: {options[answer]}")
                    else:
                        logger.info(f"ANSWER: Selected option index {answer} (out of range or invalid)")
                else:
                    # Text or other types
                    logger.info(f"ANSWER: {answer}")
                    
                # Fill the answer in the form
                filled = self.browser_handler.fill_answer(question, answer)
                
                if filled:
                    logger.info(f"Successfully filled answer for question: {question['text'][:50]}...")
                    self.questions_answered += 1
                else:
                    logger.error(f"Failed to fill answer for question: {question['text'][:50]}...")
                
                logger.info("-"*50)
                
            # Create a divider to indicate end of page processing
            logger.info("="*80)
            
            # Update total questions count
            self.total_questions += total_questions
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing current page: {str(e)}")
            logger.debug(f"Exception details:", exc_info=True)
            return False
    
    def close(self) -> None:
        """Close the browser and clean up resources."""
        if self.browser_handler:
            self.browser_handler.close()
            logger.info("Form filler resources cleaned up")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close() 