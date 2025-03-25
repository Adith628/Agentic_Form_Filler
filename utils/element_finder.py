"""
Element finder utility for locating and interacting with form elements.
"""
from typing import List, Dict, Any, Optional, Union, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException
)
from loguru import logger
from ..config import get_config

class ElementFinder:
    """Utility class for finding and interacting with form elements."""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the element finder.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.selectors = get_config("FORM_SELECTORS")
        self.browser_config = get_config("BROWSER_CONFIG")
        self.timeout = self.browser_config.get("timeout", 10)
        self.wait = WebDriverWait(self.driver, self.timeout)
    
    def find_element(self, xpath: str, wait_timeout: int = None, clickable: bool = False) -> Optional[WebElement]:
        """
        Find an element by XPath with appropriate waiting.
        
        Args:
            xpath: XPath selector
            wait_timeout: Custom timeout (or use default if None)
            clickable: Whether to wait for the element to be clickable
            
        Returns:
            WebElement if found, None otherwise
        """
        timeout = wait_timeout if wait_timeout is not None else self.timeout
        wait = WebDriverWait(self.driver, timeout)
        
        try:
            if clickable:
                return wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            else:
                return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        except (TimeoutException, NoSuchElementException):
            logger.debug(f"Element not found with XPath: {xpath}")
            return None
    
    def find_elements(self, xpath: str, wait_timeout: int = None) -> List[WebElement]:
        """
        Find all elements matching the XPath.
        
        Args:
            xpath: XPath selector
            wait_timeout: Custom timeout (or use default if None)
            
        Returns:
            List of WebElements (empty if none found)
        """
        timeout = wait_timeout if wait_timeout is not None else self.timeout
        wait = WebDriverWait(self.driver, timeout)
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return self.driver.find_elements(By.XPATH, xpath)
        except (TimeoutException, NoSuchElementException):
            logger.debug(f"No elements found with XPath: {xpath}")
            return []

    def find_button(self, selectors: List[str], clickable: bool = True) -> Optional[WebElement]:
        """
        Find a button using multiple possible XPath selectors.
        
        Args:
            selectors: List of XPath selectors to try
            clickable: Whether to wait for the element to be clickable
            
        Returns:
            WebElement if found, None otherwise
        """
        for selector in selectors:
            element = self.find_element(selector, clickable=clickable)
            if element:
                return element
        return None
    
    def find_next_button(self) -> Optional[WebElement]:
        """
        Find the 'Next' button in the form.
        
        Returns:
            WebElement if found, None otherwise
        """
        return self.find_button(self.selectors["next_button"])
    
    def find_submit_button(self) -> Optional[WebElement]:
        """
        Find the 'Submit' button in the form.
        
        Returns:
            WebElement if found, None otherwise
        """
        return self.find_button(self.selectors["submit_button"])
    
    def get_text_inputs(self) -> List[WebElement]:
        """
        Get all text input fields in the form.
        
        Returns:
            List of text input WebElements
        """
        return self.find_elements(self.selectors["text_inputs"])
    
    def get_text_areas(self) -> List[WebElement]:
        """
        Get all text area fields in the form.
        
        Returns:
            List of textarea WebElements
        """
        return self.find_elements(self.selectors["text_areas"])
    
    def get_radio_options(self) -> List[WebElement]:
        """
        Get all radio button options in the form.
        
        Returns:
            List of radio button WebElements
        """
        return self.find_elements(self.selectors["radio_options"])
    
    def get_checkbox_options(self) -> List[WebElement]:
        """
        Get all checkbox options in the form.
        
        Returns:
            List of checkbox WebElements
        """
        return self.find_elements(self.selectors["checkbox_options"])
    
    def get_dropdown_elements(self) -> Tuple[List[WebElement], List[WebElement]]:
        """
        Get all dropdown elements and their options.
        
        Returns:
            Tuple of (dropdown selectors, dropdown options)
        """
        selectors = self.find_elements(self.selectors["dropdown_select"])
        options = self.find_elements(self.selectors["dropdown_options"])
        return selectors, options
    
    def get_question_texts(self) -> List[WebElement]:
        """
        Get all question text elements.
        
        Returns:
            List of question text WebElements
        """
        return self.find_elements(self.selectors["question_texts"])
    
    def get_element_attribute(self, element: WebElement, attribute: str) -> Optional[str]:
        """
        Safely get an attribute from an element.
        
        Args:
            element: WebElement to get attribute from
            attribute: Name of the attribute
            
        Returns:
            Attribute value or None if not found
        """
        try:
            return element.get_attribute(attribute)
        except (StaleElementReferenceException, AttributeError):
            logger.debug(f"Could not get attribute {attribute} from element")
            return None
            
    def click_element(self, element: WebElement) -> bool:
        """
        Safely click an element with JavaScript fallback.
        
        Args:
            element: WebElement to click
            
        Returns:
            True if click was successful, False otherwise
        """
        try:
            # Try regular click first
            element.click()
            return True
        except Exception as e:
            logger.debug(f"Regular click failed: {str(e)}, trying JavaScript click")
            try:
                # Fall back to JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception as js_e:
                logger.debug(f"JavaScript click also failed: {str(js_e)}")
                return False 