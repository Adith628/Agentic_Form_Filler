"""
Configuration settings for the Agentic Form Filler.
"""
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Cohere API configuration
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# Browser configuration
BROWSER_CONFIG = {
    "headless": True,  # Run browser in headless mode
    "window_size": (1920, 1080),  # Browser window size
    "timeout": 10,  # Maximum wait time for elements (seconds)
    "implicit_wait": 2,  # Implicit wait time (seconds)
}

# Form element selectors (XPath)
FORM_SELECTORS = {
    # Text field questions (input elements)
    "text_inputs": "//input[@type='text' or @type='email' or @type='tel' or @type='number']",
    
    # Text area questions (textarea elements)
    "text_areas": "//textarea",
    
    # Multiple choice questions (radio buttons)
    "radio_options": "//div[@role='radio']",
    
    # Checkbox questions
    "checkbox_options": "//div[@role='checkbox']",
    
    # Dropdown questions
    "dropdown_select": "//div[@role='listbox']",
    "dropdown_options": "//div[@role='option']",
    
    # Question text elements
    "question_texts": "//div[contains(@class, 'freebirdFormviewerComponentsQuestionBaseTitle')]",
    
    # Navigation buttons
    "next_button": [
        "//span[text()='Next']/ancestor::div[@role='button']",
        "//div[@role='button']//span[contains(text(), 'Next')]",
    ],
    "submit_button": [
        "//span[text()='Submit']/ancestor::div[@role='button']",
        "//div[@role='button']//span[contains(text(), 'Submit')]",
        "//div[@jsname='M2UYVd']"
    ],
    
    # Form sections and pages
    "form_sections": "//div[contains(@class, 'freebirdFormviewerViewNumberedItemContainer')]",
}

# Question type definitions
QUESTION_TYPES = {
    "TEXT": "text",
    "PARAGRAPH": "paragraph",
    "MULTIPLE_CHOICE": "multiple_choice",
    "CHECKBOX": "checkbox",
    "DROPDOWN": "dropdown",
    "DATE": "date",
    "TIME": "time",
    "UNKNOWN": "unknown"
}

# Cohere API settings for answer generation
COHERE_CONFIG = {
    "model": "command",
    "max_tokens": 100,
    "temperature": 0.7,
    "response_format": "text",
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    "file": "form_filler.log",
    "rotation": "10 MB",
}

# Default retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1,
}

def get_config(key: str = None) -> Any:
    """Get configuration by key or return all if key is None."""
    config = {
        "COHERE_API_KEY": COHERE_API_KEY,
        "BROWSER_CONFIG": BROWSER_CONFIG,
        "FORM_SELECTORS": FORM_SELECTORS,
        "QUESTION_TYPES": QUESTION_TYPES,
        "COHERE_CONFIG": COHERE_CONFIG,
        "LOGGING_CONFIG": LOGGING_CONFIG,
        "RETRY_CONFIG": RETRY_CONFIG,
    }
    
    if key:
        return config.get(key)
    return config 