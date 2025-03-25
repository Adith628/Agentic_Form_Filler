#!/usr/bin/env python3
# Form Handler - Handles Selenium interactions with Google Forms

import logging
import time
from typing import List, Dict, Any, Optional, Union
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, StaleElementReferenceException

# Import constants for question types
from agents.reasoning_agent import ReasoningAgent

logger = logging.getLogger(__name__)

class FormHandler:
    """
    The Form Handler is responsible for:
    1. Initializing and managing Selenium WebDriver
    2. Extracting questions from the Google Form
    3. Filling in answers based on question type
    """
    
    # XPaths for finding form elements
    QUESTION_CONTAINER_XPATH = "//div[contains(@class, 'freebirdFormviewerViewItemsItemItem')]"
    QUESTION_TITLE_XPATH = ".//div[contains(@class, 'freebirdFormviewerViewItemsItemItemTitle')]"
    REQUIRED_INDICATOR_XPATH = ".//span[contains(@class, 'freebirdFormviewerViewItemsItemRequiredAsterisk')]"
    
    # Input field selectors
    TEXT_INPUT_XPATH = ".//input[@type='text']"
    TEXTAREA_XPATH = ".//textarea"
    RADIO_OPTION_XPATH = ".//div[contains(@role, 'radio')]"
    CHECKBOX_OPTION_XPATH = ".//div[contains(@role, 'checkbox')]"
    DROPDOWN_XPATH = ".//div[contains(@role, 'listbox')]"
    DROPDOWN_OPTION_XPATH = "//div[contains(@role, 'option')]"
    
    def __init__(self, headless: bool = True, chrome_driver_path: Optional[str] = None):
        """
        Initialize the Form Handler with a Selenium WebDriver.
        
        Args:
            headless: Whether to run the browser in headless mode
            chrome_driver_path: Optional path to chromedriver executable
        """
        logger.info("Initializing Form Handler")
        
        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize the WebDriver
        try:
            if chrome_driver_path:
                service = Service(chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
                
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing WebDriver: {str(e)}")
            raise
    
    def open_form(self, url: str, timeout: int = 10) -> bool:
        """
        Open a Google Form URL in the browser.
        
        Args:
            url: The URL of the Google Form
            timeout: Maximum time to wait for the form to load
            
        Returns:
            Boolean indicating if the form loaded successfully
        """
        logger.info(f"Opening Google Form at URL: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for the form to load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, self.QUESTION_CONTAINER_XPATH))
            )
            
            logger.info("Form loaded successfully")
            # Add a small delay to ensure everything is fully loaded
            time.sleep(1)
            return True
            
        except TimeoutException:
            logger.error(f"Timeout waiting for form to load after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"Error opening form: {str(e)}")
            return False
    
    def extract_questions(self) -> List[Dict[str, Any]]:
        """
        Extract all questions from the current page of the Google Form.
        
        Returns:
            List of dictionaries containing question data
        """
        logger.debug("Extracting questions from current page")
        questions = []
        
        try:
            # Find all question containers
            question_containers = self.driver.find_elements(By.XPATH, self.QUESTION_CONTAINER_XPATH)
            logger.debug(f"Found {len(question_containers)} question containers")
            
            for container in question_containers:
                question_data = self._extract_question_data(container)
                if question_data:
                    questions.append(question_data)
            
        except Exception as e:
            logger.error(f"Error extracting questions: {str(e)}")
        
        return questions
    
    def _extract_question_data(self, container) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single question container.
        
        Args:
            container: The WebElement containing the question
            
        Returns:
            Dictionary with question data or None if extraction failed
        """
        try:
            # Extract question title
            title_element = container.find_element(By.XPATH, self.QUESTION_TITLE_XPATH)
            question_text = title_element.text.strip()
            
            # Check if question is empty
            if not question_text:
                return None
                
            # Build question data dictionary
            question_data = {
                'element': container,
                'text': question_text,
                'options': []
            }
            
            # Check for multiple choice options (radio buttons)
            try:
                radio_options = container.find_elements(By.XPATH, self.RADIO_OPTION_XPATH)
                if radio_options:
                    question_data['options'] = [option.text.strip() for option in radio_options if option.text.strip()]
            except NoSuchElementException:
                pass
                
            # Check for checkbox options
            try:
                checkbox_options = container.find_elements(By.XPATH, self.CHECKBOX_OPTION_XPATH)
                if checkbox_options:
                    question_data['options'] = [option.text.strip() for option in checkbox_options if option.text.strip()]
            except NoSuchElementException:
                pass
                
            # Check for dropdown
            try:
                dropdown = container.find_element(By.XPATH, self.DROPDOWN_XPATH)
                if dropdown:
                    # Need to click to see options
                    dropdown.click()
                    time.sleep(0.5)  # Wait for dropdown to open
                    
                    # Get options
                    dropdown_options = self.driver.find_elements(By.XPATH, self.DROPDOWN_OPTION_XPATH)
                    question_data['options'] = [option.text.strip() for option in dropdown_options if option.text.strip()]
                    
                    # Click again to close dropdown
                    self.driver.find_element(By.XPATH, "//body").click()
            except (NoSuchElementException, ElementNotInteractableException):
                pass
                
            return question_data
            
        except (NoSuchElementException, StaleElementReferenceException) as e:
            logger.warning(f"Error extracting question data: {str(e)}")
            return None
    
    def fill_answer(self, question_element, question_type: str, answer: Union[str, List[str]]) -> bool:
        """
        Fill in an answer for a specific question based on its type.
        
        Args:
            question_element: The WebElement containing the question
            question_type: The type of question
            answer: The answer to fill in (string or list of strings for checkboxes)
            
        Returns:
            Boolean indicating if the answer was filled successfully
        """
        logger.debug(f"Filling answer for question type: {question_type}")
        
        try:
            if question_type == ReasoningAgent.TYPE_TEXT:
                return self._fill_text_answer(question_element, answer)
                
            elif question_type == ReasoningAgent.TYPE_PARAGRAPH:
                return self._fill_paragraph_answer(question_element, answer)
                
            elif question_type == ReasoningAgent.TYPE_MULTIPLE_CHOICE:
                return self._select_radio_option(question_element, answer)
                
            elif question_type == ReasoningAgent.TYPE_CHECKBOX:
                return self._select_checkbox_options(question_element, answer)
                
            elif question_type == ReasoningAgent.TYPE_DROPDOWN:
                return self._select_dropdown_option(question_element, answer)
                
            else:
                logger.warning(f"Unknown question type: {question_type}, cannot fill answer")
                return False
                
        except Exception as e:
            logger.error(f"Error filling answer: {str(e)}")
            return False
    
    def _fill_text_answer(self, question_element, answer: str) -> bool:
        """
        Fill in a text input field.
        
        Args:
            question_element: The WebElement containing the question
            answer: The text answer to fill in
            
        Returns:
            Boolean indicating if the answer was filled successfully
        """
        try:
            input_field = question_element.find_element(By.XPATH, self.TEXT_INPUT_XPATH)
            input_field.clear()
            input_field.send_keys(answer)
            return True
            
        except NoSuchElementException:
            logger.warning("No text input field found")
            return False
        except Exception as e:
            logger.error(f"Error filling text answer: {str(e)}")
            return False
    
    def _fill_paragraph_answer(self, question_element, answer: str) -> bool:
        """
        Fill in a paragraph (textarea) field.
        
        Args:
            question_element: The WebElement containing the question
            answer: The paragraph answer to fill in
            
        Returns:
            Boolean indicating if the answer was filled successfully
        """
        try:
            textarea = question_element.find_element(By.XPATH, self.TEXTAREA_XPATH)
            textarea.clear()
            textarea.send_keys(answer)
            return True
            
        except NoSuchElementException:
            logger.warning("No textarea field found, trying text input")
            # Fall back to regular text input in case the detection was wrong
            return self._fill_text_answer(question_element, answer)
        except Exception as e:
            logger.error(f"Error filling paragraph answer: {str(e)}")
            return False
    
    def _select_radio_option(self, question_element, option: str) -> bool:
        """
        Select a radio button option.
        
        Args:
            question_element: The WebElement containing the question
            option: The option text to select
            
        Returns:
            Boolean indicating if the option was selected successfully
        """
        try:
            # Find all radio options
            radio_options = question_element.find_elements(By.XPATH, self.RADIO_OPTION_XPATH)
            
            # Try to find and click the matching option
            for radio in radio_options:
                if radio.text.strip() == option:
                    radio.click()
                    return True
            
            # If exact match not found, try case-insensitive partial match
            for radio in radio_options:
                if option.lower() in radio.text.lower():
                    radio.click()
                    return True
                    
            logger.warning(f"Radio option '{option}' not found, selecting first option")
            if radio_options:
                radio_options[0].click()
                return True
                
            return False
            
        except NoSuchElementException:
            logger.warning("No radio options found")
            return False
        except Exception as e:
            logger.error(f"Error selecting radio option: {str(e)}")
            return False
    
    def _select_checkbox_options(self, question_element, options: List[str]) -> bool:
        """
        Select multiple checkbox options.
        
        Args:
            question_element: The WebElement containing the question
            options: List of option texts to select
            
        Returns:
            Boolean indicating if at least one option was selected
        """
        if not options:
            logger.warning("No options provided for checkbox question")
            return False
            
        try:
            # Find all checkbox options
            checkbox_elements = question_element.find_elements(By.XPATH, self.CHECKBOX_OPTION_XPATH)
            
            selected_count = 0
            
            # Try to select all specified options
            for option in options:
                option_found = False
                
                # Try exact match first
                for checkbox in checkbox_elements:
                    if checkbox.text.strip() == option:
                        checkbox.click()
                        selected_count += 1
                        option_found = True
                        break
                
                # If not found, try partial match
                if not option_found:
                    for checkbox in checkbox_elements:
                        if option.lower() in checkbox.text.lower():
                            checkbox.click()
                            selected_count += 1
                            option_found = True
                            break
            
            # If no options were found and selected, select the first one
            if selected_count == 0 and checkbox_elements:
                checkbox_elements[0].click()
                selected_count = 1
                
            return selected_count > 0
            
        except NoSuchElementException:
            logger.warning("No checkbox options found")
            return False
        except Exception as e:
            logger.error(f"Error selecting checkbox options: {str(e)}")
            return False
    
    def _select_dropdown_option(self, question_element, option: str) -> bool:
        """
        Select an option from a dropdown.
        
        Args:
            question_element: The WebElement containing the question
            option: The option text to select
            
        Returns:
            Boolean indicating if the option was selected successfully
        """
        try:
            # Find and click the dropdown to open it
            dropdown = question_element.find_element(By.XPATH, self.DROPDOWN_XPATH)
            dropdown.click()
            time.sleep(0.5)  # Wait for dropdown to open
            
            # Find all dropdown options
            dropdown_options = self.driver.find_elements(By.XPATH, self.DROPDOWN_OPTION_XPATH)
            
            # Try to find and click the matching option
            for dropdown_option in dropdown_options:
                if dropdown_option.text.strip() == option:
                    dropdown_option.click()
                    return True
            
            # If exact match not found, try case-insensitive partial match
            for dropdown_option in dropdown_options:
                if option.lower() in dropdown_option.text.lower():
                    dropdown_option.click()
                    return True
            
            # If no match found, select the first non-empty option
            for dropdown_option in dropdown_options:
                if dropdown_option.text.strip():
                    dropdown_option.click()
                    return True
                    
            return False
            
        except NoSuchElementException:
            logger.warning("No dropdown or dropdown options found")
            return False
        except Exception as e:
            logger.error(f"Error selecting dropdown option: {str(e)}")
            # If anything goes wrong, try clicking outside to close dropdown
            try:
                self.driver.find_element(By.XPATH, "//body").click()
            except:
                pass
            return False
    
    def close(self):
        """Close the browser and clean up the WebDriver."""
        logger.info("Closing WebDriver")
        try:
            self.driver.quit()
        except Exception as e:
            logger.error(f"Error closing WebDriver: {str(e)}") 