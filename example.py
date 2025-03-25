#!/usr/bin/env python
"""
Example script demonstrating how to use the Agentic AI Form Filler as a library.
"""
import os
import time
from dotenv import load_dotenv
from agentic_form_filler import FormFiller
from agentic_form_filler.utils.logger import setup_logger

def main():
    """Example usage of the FormFiller."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Setup logging
    logger = setup_logger()
    
    # Get Cohere API key from environment variable
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        logger.error("Cohere API key not found in environment variables.")
        return 1
    
    # Google Form URL (replace with your actual form URL)
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSf9Kz-empyZzJTsJ-kZUJEM1HAY-g2D59CQiJAWxWUYs4KfbA/viewform"
    
    logger.info(f"Starting example run on form: {form_url}")
    
    # Create the form filler instance
    form_filler = FormFiller(
        form_url=form_url,
        cohere_api_key=api_key,
        headless=True  # Set to False to see the browser
    )
    
    # Run the form filling process
    success = form_filler.run()
    
    if success:
        logger.info("Form was successfully filled and submitted!")
    else:
        logger.error("Failed to complete the form submission.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 