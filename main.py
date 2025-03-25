#!/usr/bin/env python
"""
Main script for running the Agentic AI Google Form Filler.
"""
import os
import sys
import argparse
import time
from dotenv import load_dotenv
from loguru import logger
from .form_filler import FormFiller
from .utils.logger import setup_logger
from .browser.browser_handler import BrowserHandler
from .config import get_config

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Agentic AI Google Form Filler",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--form-url", 
        type=str, 
        required=True,
        help="URL of the Google Form to fill"
    )
    
    parser.add_argument(
        "--headless", 
        action="store_true", 
        default=True,
        help="Run in headless mode"
    )
    
    parser.add_argument(
        "--no-headless", 
        action="store_false", 
        dest="headless",
        help="Run with visible browser"
    )
    
    parser.add_argument(
        "--api-key", 
        type=str, 
        help="Cohere API key (can also be set via COHERE_API_KEY env variable)"
    )
    
    parser.add_argument(
        "--submissions", 
        type=int, 
        default=1,
        help="Number of form submissions to make"
    )
    
    parser.add_argument(
        "--delay", 
        type=int, 
        default=5,
        help="Delay between submissions in seconds"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level"
    )
    
    parser.add_argument(
        "--screenshot-dir", 
        type=str,
        default="screenshots",
        help="Directory to save screenshots (will be created if it doesn't exist)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the form filler script."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse command line arguments
    args = parse_args()
    
    # Setup logging with custom config
    log_config = {
        "level": args.log_level,
        "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        "file": "form_filler.log",
        "rotation": "10 MB",
    }
    setup_logger(log_config)
    
    # Get API key from args or environment
    api_key = args.api_key or os.getenv("COHERE_API_KEY")
    if not api_key:
        logger.error("Cohere API key not provided. Please set via --api-key or COHERE_API_KEY environment variable.")
        return 1
    
    # Create screenshot directory if needed
    if not os.path.exists(args.screenshot_dir):
        os.makedirs(args.screenshot_dir)
        logger.info(f"Created screenshot directory: {args.screenshot_dir}")
    
    logger.info("="*80)
    logger.info(f"Starting Agentic AI Google Form Filler")
    logger.info(f"Form URL: {args.form_url}")
    logger.info(f"Headless mode: {args.headless}")
    logger.info(f"Submissions: {args.submissions}")
    logger.info(f"Log level: {args.log_level}")
    logger.info("="*80)
    
    successful_submissions = 0
    
    # Run specified number of submissions
    for i in range(args.submissions):
        logger.info(f"Starting submission {i+1}/{args.submissions}")
        screenshot_path = os.path.join(args.screenshot_dir, f"submission_{i+1}_final.png")
        
        try:
            # Configure browser
            browser_config = get_config("BROWSER_CONFIG")
            browser_config["headless"] = args.headless
            browser_handler = BrowserHandler(browser_config)
            
            # Create form filler instance
            form_filler = FormFiller(
                browser_handler=browser_handler,
                cohere_api_key=api_key
            )
            
            # Run the form filling process
            start_time = time.time()
            result = form_filler.fill_form(args.form_url)
            elapsed_time = time.time() - start_time
            
            # Save final state screenshot
            browser_handler.take_screenshot(screenshot_path)
            
            if result:
                successful_submissions += 1
                logger.info(f"Submission {i+1} completed successfully in {elapsed_time:.2f} seconds")
                logger.info(f"Screenshot saved to {screenshot_path}")
            else:
                logger.error(f"Submission {i+1} failed after {elapsed_time:.2f} seconds")
            
            # Clean up resources
            form_filler.close()
            
            # Delay between submissions
            if i < args.submissions - 1:
                logger.info(f"Waiting {args.delay} seconds before next submission")
                time.sleep(args.delay)
                
        except Exception as e:
            logger.error(f"Error in submission {i+1}: {str(e)}")
            logger.debug("Exception details:", exc_info=True)
    
    # Print final summary
    logger.info("="*80)
    logger.info(f"Form filling complete")
    logger.info(f"Successful submissions: {successful_submissions}/{args.submissions}")
    logger.info("="*80)
    
    if successful_submissions == 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 