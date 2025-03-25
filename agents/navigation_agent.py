"""
Navigation Agent for handling form navigation.
"""
import time
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.remote.webelement import WebElement
from loguru import logger
from ..browser.browser_handler import BrowserHandler
from ..config import get_config

class NavigationAgent:
    """
    Agent for handling form navigation.
    
    This agent is responsible for detecting and interacting with
    navigation elements like "Next" and "Submit" buttons.
    """
    
    def __init__(self, browser_handler: BrowserHandler):
        """
        Initialize the navigation agent.
        
        Args:
            browser_handler: Browser handler instance
        """
        self.browser = browser_handler
        self.element_finder = browser_handler.element_finder
        self.retry_config = get_config("RETRY_CONFIG")
    
    def check_for_next_button(self) -> Optional[WebElement]:
        """
        Check if a "Next" button is present on the current page.
        
        Returns:
            Next button WebElement if found, None otherwise
        """
        logger.info("Checking for Next button")
        return self.element_finder.find_next_button()
    
    def check_for_submit_button(self) -> Optional[WebElement]:
        """
        Check if a "Submit" button is present on the current page.
        
        Returns:
            Submit button WebElement if found, None otherwise
        """
        logger.info("Checking for Submit button")
        return self.element_finder.find_submit_button()
    
    def navigate_to_next_page(self) -> bool:
        """
        Navigate to the next page of the form.
        
        Returns:
            True if navigation was successful, False otherwise
        """
        logger.info("Attempting to navigate to next page")
        
        # Try to find the Next button
        next_button = self.check_for_next_button()
        if not next_button:
            logger.warning("Next button not found")
            return False
        
        # Try to click the Next button
        return self._click_navigation_button(next_button, "Next")
    
    def submit_form(self) -> bool:
        """
        Submit the form.
        
        Returns:
            True if submission was successful, False otherwise
        """
        logger.info("Attempting to submit form")
        
        # Try to find the Submit button
        submit_button = self.check_for_submit_button()
        if not submit_button:
            logger.warning("Submit button not found")
            return False
        
        # Try to click the Submit button
        result = self._click_navigation_button(submit_button, "Submit")
        
        if result:
            # Wait for submission to complete
            time.sleep(2)
            
            # Check if we're still on a form page (submission might have failed)
            next_button = self.check_for_next_button()
            submit_button = self.check_for_submit_button()
            
            if next_button or submit_button:
                logger.warning("We're still on a form page after submission attempt")
                return False
        
        return result
    
    def _click_navigation_button(self, button: WebElement, button_type: str) -> bool:
        """
        Click a navigation button with retries.
        
        Args:
            button: Navigation button WebElement
            button_type: Type of button ("Next" or "Submit")
            
        Returns:
            True if click was successful, False otherwise
        """
        max_retries = self.retry_config.get("max_retries", 3)
        retry_delay = self.retry_config.get("retry_delay", 1)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Clicking {button_type} button (attempt {attempt + 1}/{max_retries})")
                
                # Try using our utility method which tries both regular and JS clicks
                if self.element_finder.click_element(button):
                    logger.info(f"Successfully clicked {button_type} button")
                    # Give the page time to update
                    time.sleep(1)
                    return True
                
                # If still here, the click failed
                logger.warning(f"Failed to click {button_type} button")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Error clicking {button_type} button: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.error(f"Failed to click {button_type} button after {max_retries} attempts")
        return False
    
    def detect_form_completion(self) -> bool:
        """
        Detect if the form has been completed.
        
        Returns:
            True if form appears to be completed, False otherwise
        """
        # Check for common completion indicators
        try:
            # Look for common thank you messages
            success_indicators = [
                "//div[contains(text(), 'Thank you')]",
                "//div[contains(text(), 'Your response has been recorded')]",
                "//div[contains(text(), 'Form submitted')]",
                "//div[contains(text(), 'successfully submitted')]",
            ]
            
            for indicator in success_indicators:
                element = self.element_finder.find_element(indicator)
                if element:
                    logger.info(f"Form completion detected: '{element.text}'")
                    return True
            
            # If no "Next" or "Submit" buttons are found, and we previously 
            # clicked Submit, we can assume the form is complete
            next_button = self.check_for_next_button()
            submit_button = self.check_for_submit_button()
            
            if not next_button and not submit_button:
                logger.info("Form appears to be completed (no navigation buttons found)")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error detecting form completion: {str(e)}")
            return False
    
    def determine_next_action(self) -> str:
        """
        Determine the next navigation action to take.
        
        Returns:
            Action to take ("next", "submit", "complete", or "unknown")
        """
        logger.info("Determining next navigation action")
        
        # Check if form appears to be completed
        if self.detect_form_completion():
            return "complete"
        
        # Check for Submit button first (if present, we're on the last page)
        submit_button = self.check_for_submit_button()
        if submit_button:
            return "submit"
        
        # Check for Next button
        next_button = self.check_for_next_button()
        if next_button:
            return "next"
        
        # If neither button is found and we're not on a completion page,
        # something might be wrong
        logger.warning("Could not determine navigation action")
        return "unknown" 