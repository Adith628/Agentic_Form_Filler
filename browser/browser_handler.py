"""
Browser handler for Selenium interaction with forms.
"""
import time
from typing import Optional, Dict, Any, List, Union
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
from ..config import get_config
from ..utils.element_finder import ElementFinder

class BrowserHandler:
    """
    Browser handler for Selenium-based form interaction.
    
    This class provides high-level functionality for browser initialization,
    navigation, and form interaction.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the browser handler.
        
        Args:
            config: Browser configuration (uses default if None)
        """
        self.config = config or get_config("BROWSER_CONFIG")
        self.driver = None
        self.element_finder = None
        self.init_driver()
    
    def init_driver(self) -> None:
        """Initialize the Selenium WebDriver with appropriate configuration."""
        try:
            # Configure Chrome options
            chrome_options = Options()
            
            # Set headless mode if specified
            if self.config.get("headless", True):
                chrome_options.add_argument("--headless")
            
            # Set window size
            window_size = self.config.get("window_size", (1920, 1080))
            chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
            
            # Add performance optimizations
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            
            # Reduce logging
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-infobars")
            
            # Initialize Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set implicit wait time
            implicit_wait = self.config.get("implicit_wait", 2)
            self.driver.implicitly_wait(implicit_wait)
            
            # Initialize the element finder utility
            self.element_finder = ElementFinder(self.driver)
            
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    def navigate_to(self, url: str) -> bool:
        """
        Navigate to the specified URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            self.driver.get(url)
            logger.info(f"Navigated to {url}")
            return True
        except WebDriverException as e:
            logger.error(f"Navigation failed: {str(e)}")
            # Try to recover by reinitializing the driver
            self.close()
            self.init_driver()
            return False
    
    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Result of the script execution
        """
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"Failed to execute script: {str(e)}")
            return None
    
    def get_page_source(self) -> str:
        """
        Get the current page source.
        
        Returns:
            HTML source of the current page
        """
        return self.driver.page_source
    
    def take_screenshot(self, filename: str) -> bool:
        """
        Take a screenshot of the current page.
        
        Args:
            filename: Path to save the screenshot
            
        Returns:
            True if screenshot was taken successfully, False otherwise
        """
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return False
    
    def wait(self, seconds: float) -> None:
        """
        Wait for the specified number of seconds.
        
        Args:
            seconds: Number of seconds to wait
        """
        time.sleep(seconds)
    
    def close(self) -> None:
        """Close the browser and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None
                self.element_finder = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
    
    def fill_answer(self, question: Dict[str, Any], answer: Any) -> bool:
        """
        Fill the answer for a given question.
        
        Args:
            question: Dictionary containing question data including type and elements
            answer: The answer value to fill (varies by question type)
            
        Returns:
            True if the answer was successfully filled, False otherwise
        """
        try:
            question_type = question['type']
            elements = question.get('elements', [])
            
            if not elements:
                logger.error(f"No elements found for question: {question['text'][:30]}...")
                return False
                
            logger.debug(f"Filling answer for {question_type} question")
            
            if question_type == "text" or question_type == "paragraph":
                # Text and paragraph inputs
                if not isinstance(answer, str):
                    answer = str(answer)
                
                element = elements[0]
                # Clear existing text
                try:
                    element.clear()
                except ElementNotInteractableException:
                    # Some elements can't be cleared directly, try with keys
                    element.send_keys(Keys.CONTROL + "a")
                    element.send_keys(Keys.DELETE)
                
                # Send keys with small delay to simulate typing
                element.send_keys(answer)
                return True
                
            elif question_type == "multiple_choice":
                # Radio buttons
                if isinstance(answer, int) and 0 <= answer < len(elements):
                    success = self.element_finder.click_element(elements[answer])
                    return success
                else:
                    logger.warning(f"Invalid answer index for multiple choice: {answer}")
                    return False
                    
            elif question_type == "checkbox":
                # Checkboxes (multiple selections)
                if isinstance(answer, list):
                    success = True
                    for idx in answer:
                        if 0 <= idx < len(elements):
                            if not self.element_finder.click_element(elements[idx]):
                                success = False
                        else:
                            logger.warning(f"Invalid checkbox index: {idx}")
                            success = False
                    return success
                else:
                    logger.warning(f"Expected list for checkbox answer, got: {type(answer)}")
                    return False
                    
            elif question_type == "dropdown":
                # Dropdown selection
                if isinstance(answer, int) and elements:
                    # First click the dropdown to open it
                    if not self.element_finder.click_element(elements[0]):
                        logger.warning("Could not click dropdown to open it")
                        return False
                        
                    # Wait for dropdown options to appear
                    time.sleep(0.5)
                    
                    # Find dropdown options
                    dropdown_options = self.element_finder.find_elements("//div[@role='option']")
                    if dropdown_options and 0 <= answer < len(dropdown_options):
                        success = self.element_finder.click_element(dropdown_options[answer])
                        return success
                    else:
                        logger.warning(f"Dropdown option {answer} not found")
                        return False
                else:
                    logger.warning(f"Invalid dropdown answer: {answer}")
                    return False
                    
            else:
                logger.warning(f"Unsupported question type: {question_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error filling answer: {str(e)}")
            logger.debug("Exception details:", exc_info=True)
            return False 