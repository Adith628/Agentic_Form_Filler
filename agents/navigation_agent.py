#!/usr/bin/env python3
# Navigation Agent - Handles form navigation and submission

import logging
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class NavigationAgent:
    """
    The Navigation Agent is responsible for:
    1. Detecting 'Next' and 'Submit' buttons in Google Forms
    2. Navigating between pages of multi-page forms
    3. Determining when the form is complete
    """
    
    # Common button identifiers in Google Forms
    NEXT_BUTTON_IDENTIFIERS = [
        "//span[contains(text(), 'Next')]",
        "//span[contains(text(), 'Continue')]",
        "//div[contains(@role, 'button')][contains(., 'Next')]",
        "//div[contains(@class, 'freebirdFormviewerViewNavigationButtons')]/div[2]",
        "//div[contains(@class, 'appsMaterialWizButtonPaperbuttonLabel')][contains(text(), 'Next')]"
    ]
    
    SUBMIT_BUTTON_IDENTIFIERS = [
        "//span[contains(text(), 'Submit')]",
        "//div[contains(@role, 'button')][contains(., 'Submit')]",
        "//div[contains(@class, 'freebirdFormviewerViewNavigationButtons')]/div[2]",
        "//div[contains(@class, 'appsMaterialWizButtonPaperbuttonLabel')][contains(text(), 'Submit')]"
    ]
    
    COMPLETION_INDICATORS = [
        "//div[contains(text(), 'Your response has been recorded')]",
        "//div[contains(text(), 'Thanks for submitting')]",
        "//div[contains(text(), 'Thank you for your response')]"
    ]
    
    def __init__(self, form_handler):
        """
        Initialize the Navigation Agent.
        
        Args:
            form_handler: The FormHandler instance providing access to the Selenium WebDriver
        """
        logger.info("Initializing Navigation Agent")
        self.form_handler = form_handler
        self.driver = form_handler.driver
        self.next_page_attempts = 0
        self.max_attempts = 3
    
    def navigate_next(self) -> bool:
        """
        Attempt to navigate to the next page of the form.
        
        Returns:
            Boolean indicating if navigation was successful
        """
        logger.debug("Attempting to navigate to next page")
        
        # First check if the form is already completed
        if self.is_form_completed():
            logger.info("Form already completed, no further navigation needed")
            return False
        
        # Try to find the Submit button first - prioritize completing the form
        submit_button = self._find_button(self.SUBMIT_BUTTON_IDENTIFIERS)
        if submit_button:
            logger.info("Found Submit button - this appears to be the last page")
            try:
                # Add a short delay to ensure all answers are registered
                time.sleep(1)
                submit_button.click()
                logger.info("Form submitted successfully")
                
                # Wait for submission to complete
                self._wait_for_form_completion()
                return False  # Navigation is complete
                
            except Exception as e:
                logger.error(f"Error submitting form: {str(e)}")
                self.next_page_attempts += 1
                if self.next_page_attempts >= self.max_attempts:
                    logger.warning("Max submission attempts reached, assuming form is complete")
                    return False
                return True  # Try again next iteration
        
        # If not on the last page, look for Next button
        next_button = self._find_button(self.NEXT_BUTTON_IDENTIFIERS)
        if next_button:
            logger.info("Found Next button - navigating to next page")
            try:
                # Add a short delay to ensure all answers are registered
                time.sleep(1)
                next_button.click()
                
                # Wait for the next page to load
                self._wait_for_page_load()
                
                # Reset attempts counter after successful navigation
                self.next_page_attempts = 0
                
                # Indicate successful navigation to the next page
                return True
                
            except Exception as e:
                logger.error(f"Error navigating to next page: {str(e)}")
                self.next_page_attempts += 1
                if self.next_page_attempts >= self.max_attempts:
                    logger.warning("Max navigation attempts reached, assuming form is complete")
                    return False
                return True  # Try again next iteration
                
        logger.warning("No Next or Submit button found")
        return False
    
    def is_form_completed(self) -> bool:
        """
        Check if the form has been completed and submitted.
        
        Returns:
            Boolean indicating if the form is completed
        """
        # Look for completion messages
        for indicator in self.COMPLETION_INDICATORS:
            try:
                element = self.driver.find_element(By.XPATH, indicator)
                if element.is_displayed():
                    logger.info(f"Form completion detected: '{element.text}'")
                    return True
            except NoSuchElementException:
                continue
        
        # Check for common "Thank you" page URL patterns
        current_url = self.driver.current_url
        if "formResponse" in current_url or "closedform" in current_url:
            logger.info("Form completion detected from URL")
            return True
            
        return False
    
    def _find_button(self, identifiers):
        """
        Try to find a button using a list of possible identifiers.
        
        Args:
            identifiers: List of XPATH identifiers to try
            
        Returns:
            WebElement if found, None otherwise
        """
        for identifier in identifiers:
            try:
                element = self.driver.find_element(By.XPATH, identifier)
                if element.is_displayed() and element.is_enabled():
                    return element
            except NoSuchElementException:
                continue
        
        return None
    
    def _wait_for_page_load(self, timeout: int = 10) -> bool:
        """
        Wait for the page to load after clicking Next.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Boolean indicating if the page loaded successfully
        """
        try:
            # Wait for a loading indicator to disappear or for new content
            # Google Forms often has a loading animation we can look for
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'freebirdFormviewerViewFormContentLoadingContainer')]"))
            )
            
            # Additionally, wait for the new page content to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'freebirdFormviewerViewItemsItemItem')]"))
            )
            
            # Add a small delay to ensure the page is fully loaded
            time.sleep(0.5)
            return True
            
        except TimeoutException:
            logger.warning(f"Timeout waiting for page to load after {timeout} seconds")
            return False
    
    def _wait_for_form_completion(self, timeout: int = 15) -> bool:
        """
        Wait for the form submission to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Boolean indicating if the form completion was detected
        """
        try:
            # Wait for any of the completion indicators
            for indicator in self.COMPLETION_INDICATORS:
                try:
                    WebDriverWait(self.driver, timeout/len(self.COMPLETION_INDICATORS)).until(
                        EC.visibility_of_element_located((By.XPATH, indicator))
                    )
                    logger.info("Form completion confirmed")
                    return True
                except TimeoutException:
                    continue
                
            # Also check for URL change indicating completion
            start_url = self.driver.current_url
            
            def url_changed(driver):
                return driver.current_url != start_url
                
            WebDriverWait(self.driver, timeout).until(url_changed)
            
            # Verify the new URL is consistent with completion
            current_url = self.driver.current_url
            if "formResponse" in current_url or "closedform" in current_url:
                logger.info("Form completion confirmed via URL change")
                return True
                
            logger.warning("URL changed but not to a known completion URL")
            return False
            
        except TimeoutException:
            logger.warning(f"Timeout waiting for form completion after {timeout} seconds")
            return False 