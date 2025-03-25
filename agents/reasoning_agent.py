"""
Reasoning Agent for extracting and classifying form questions.
"""
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.remote.webelement import WebElement
from loguru import logger
from ..browser.browser_handler import BrowserHandler
from ..config import get_config
from bs4 import BeautifulSoup
import re

class ReasoningAgent:
    """
    Agent for extracting and classifying form questions.
    
    This agent is responsible for analyzing the form structure, extracting
    questions, and determining the appropriate question type.
    """
    
    def __init__(self, browser_handler: BrowserHandler):
        """
        Initialize the reasoning agent.
        
        Args:
            browser_handler: Browser handler instance
        """
        self.browser = browser_handler
        self.element_finder = browser_handler.element_finder
        self.question_types = get_config("QUESTION_TYPES")
    
    def extract_questions(self, page_source: str) -> List[Dict[str, Any]]:
        """
        Extract all questions from the current form page.
        
        Args:
            page_source: HTML source of the current page
            
        Returns:
            List of question dictionaries with structure:
            {
                'text': str,           # Question text
                'type': str,           # Question type (text, multiple_choice, etc.)
                'options': List[str],  # Options for multiple choice/checkbox questions
                'elements': List       # Associated WebElements for interacting with the question
            }
        """
        logger.info("Extracting questions from current form page")
        
        # Get all question texts
        question_texts = self.element_finder.get_question_texts()
        
        # If no question texts found, try alternative approach
        if not question_texts:
            logger.warning("No question texts found using standard selectors, trying alternative approach")
            return self._extract_questions_by_elements()
        
        # Process each question
        questions = []
        for i, question_text_elem in enumerate(question_texts):
            try:
                # Extract question text
                question_text = question_text_elem.text.strip()
                if not question_text:
                    continue
                
                # Determine question type and associated elements
                q_type, elements, options = self._classify_question(question_text_elem)
                
                # Create question dictionary
                question = {
                    'text': question_text,
                    'type': q_type,
                    'options': options,
                    'elements': elements
                }
                
                questions.append(question)
                logger.debug(f"Extracted question: {question['text'][:50]}... (Type: {q_type})")
            except Exception as e:
                logger.error(f"Error extracting question {i}: {str(e)}")
        
        logger.info(f"Extracted {len(questions)} questions from form")
        return questions
    
    def _extract_questions_by_elements(self) -> List[Dict[str, Any]]:
        """
        Alternative question extraction method based on form elements.
        
        Returns:
            List of question dictionaries
        """
        questions = []
        
        # Process text inputs
        text_inputs = self.element_finder.get_text_inputs()
        for i, input_elem in enumerate(text_inputs):
            try:
                # Look for a label or question text near this input
                label = self._find_label_for_element(input_elem)
                q_type = self.question_types["TEXT"]
                question = {
                    'text': label or f"Text Question {i+1}",
                    'type': q_type,
                    'options': [],
                    'elements': [input_elem]
                }
                questions.append(question)
            except Exception as e:
                logger.error(f"Error processing text input {i}: {str(e)}")
        
        # Process text areas
        text_areas = self.element_finder.get_text_areas()
        for i, textarea_elem in enumerate(text_areas):
            try:
                label = self._find_label_for_element(textarea_elem)
                q_type = self.question_types["PARAGRAPH"]
                question = {
                    'text': label or f"Paragraph Question {i+1}",
                    'type': q_type,
                    'options': [],
                    'elements': [textarea_elem]
                }
                questions.append(question)
            except Exception as e:
                logger.error(f"Error processing textarea {i}: {str(e)}")
        
        # Process radio buttons (group by proximity)
        radio_options = self.element_finder.get_radio_options()
        if radio_options:
            try:
                radio_groups = self._group_elements_by_question(radio_options)
                for i, group in enumerate(radio_groups):
                    if group:
                        label = self._find_label_for_element(group[0])
                        options = [self._get_option_text(opt) for opt in group]
                        question = {
                            'text': label or f"Multiple Choice Question {i+1}",
                            'type': self.question_types["MULTIPLE_CHOICE"],
                            'options': options,
                            'elements': group
                        }
                        questions.append(question)
            except Exception as e:
                logger.error(f"Error processing radio buttons: {str(e)}")
        
        # Process checkboxes
        checkbox_options = self.element_finder.get_checkbox_options()
        if checkbox_options:
            try:
                checkbox_groups = self._group_elements_by_question(checkbox_options)
                for i, group in enumerate(checkbox_groups):
                    if group:
                        label = self._find_label_for_element(group[0])
                        options = [self._get_option_text(opt) for opt in group]
                        question = {
                            'text': label or f"Checkbox Question {i+1}",
                            'type': self.question_types["CHECKBOX"],
                            'options': options,
                            'elements': group
                        }
                        questions.append(question)
            except Exception as e:
                logger.error(f"Error processing checkboxes: {str(e)}")
        
        # Process dropdowns
        dropdowns, options = self.element_finder.get_dropdown_elements()
        for i, dropdown in enumerate(dropdowns):
            try:
                label = self._find_label_for_element(dropdown)
                dropdown_options = []
                for opt in options:
                    opt_text = self._get_option_text(opt)
                    if opt_text:
                        dropdown_options.append(opt_text)
                
                question = {
                    'text': label or f"Dropdown Question {i+1}",
                    'type': self.question_types["DROPDOWN"],
                    'options': dropdown_options,
                    'elements': [dropdown]
                }
                questions.append(question)
            except Exception as e:
                logger.error(f"Error processing dropdown {i}: {str(e)}")
        
        logger.info(f"Extracted {len(questions)} questions using element-based approach")
        return questions
    
    def _classify_question(self, question_elem: WebElement) -> Tuple[str, List[WebElement], List[str]]:
        """
        Classify a question's type based on its associated elements.
        
        Args:
            question_elem: Question text WebElement
            
        Returns:
            Tuple of (question_type, associated_elements, options)
        """
        # Search for related elements near the question
        question_div = self._find_parent_container(question_elem)
        if not question_div:
            question_div = question_elem
        
        # Check for text inputs
        text_inputs = self.element_finder.find_elements(
            ".//input[@type='text' or @type='email' or @type='tel' or @type='number']",
            question_div
        )
        if text_inputs:
            return self.question_types["TEXT"], text_inputs, []
        
        # Check for textareas
        textareas = self.element_finder.find_elements(".//textarea", question_div)
        if textareas:
            return self.question_types["PARAGRAPH"], textareas, []
        
        # Check for radio buttons
        radio_buttons = self.element_finder.find_elements(".//div[@role='radio']", question_div)
        if radio_buttons:
            options = [self._get_option_text(rb) for rb in radio_buttons]
            return self.question_types["MULTIPLE_CHOICE"], radio_buttons, options
        
        # Check for checkboxes
        checkboxes = self.element_finder.find_elements(".//div[@role='checkbox']", question_div)
        if checkboxes:
            options = [self._get_option_text(cb) for cb in checkboxes]
            return self.question_types["CHECKBOX"], checkboxes, options
        
        # Check for dropdowns
        dropdowns = self.element_finder.find_elements(".//div[@role='listbox']", question_div)
        if dropdowns:
            # Get dropdown options
            dropdown_options = self.element_finder.find_elements(".//div[@role='option']", question_div)
            options = [self._get_option_text(opt) for opt in dropdown_options]
            return self.question_types["DROPDOWN"], dropdowns, options
        
        # If no specific elements found, default to unknown
        return self.question_types["UNKNOWN"], [], []
    
    def _find_parent_container(self, element: WebElement) -> Optional[WebElement]:
        """
        Find the parent container element for a question.
        
        Args:
            element: WebElement to find parent for
            
        Returns:
            Parent container WebElement or None if not found
        """
        try:
            # Try to find parent based on common Google Forms classes
            parent = self.browser.execute_script(
                """
                function findParentContainer(el) {
                    // Try to find parent with classes often used in forms
                    let current = el;
                    while (current && current.tagName !== 'BODY') {
                        // Look for common container classes
                        if (current.classList.contains('freebirdFormviewerComponentsQuestionBaseRoot') ||
                            current.classList.contains('freebirdFormviewerViewNumberedItemContainer')) {
                            return current;
                        }
                        current = current.parentElement;
                    }
                    return null;
                }
                return findParentContainer(arguments[0]);
                """, 
                element
            )
            return parent
        except Exception as e:
            logger.debug(f"Error finding parent container: {str(e)}")
            return None
    
    def _find_label_for_element(self, element: WebElement) -> str:
        """
        Find a label or description for an input element.
        
        Args:
            element: WebElement to find label for
            
        Returns:
            Label text or empty string if not found
        """
        try:
            # Try various approaches to find a label
            label = self.browser.execute_script(
                """
                function findLabel(el) {
                    // Try to find the label using various strategies
                    
                    // 1. Check for aria-labelledby
                    let labelledby = el.getAttribute('aria-labelledby');
                    if (labelledby) {
                        let labelEl = document.getElementById(labelledby);
                        if (labelEl && labelEl.textContent.trim()) {
                            return labelEl.textContent.trim();
                        }
                    }
                    
                    // 2. Check for associated label element
                    if (el.id) {
                        let label = document.querySelector(`label[for="${el.id}"]`);
                        if (label && label.textContent.trim()) {
                            return label.textContent.trim();
                        }
                    }
                    
                    // 3. Look for nearby heading elements
                    let current = el;
                    while (current && current.tagName !== 'BODY') {
                        // Check for heading elements that are siblings
                        let parent = current.parentElement;
                        if (parent) {
                            for (let child of parent.children) {
                                if (/^H[1-6]$/.test(child.tagName) || 
                                    child.classList.contains('freebirdFormviewerComponentsQuestionBaseTitle')) {
                                    return child.textContent.trim();
                                }
                            }
                        }
                        current = parent;
                    }
                    
                    // 4. Check preceding siblings for text
                    current = el;
                    while (current && current.previousElementSibling) {
                        let prev = current.previousElementSibling;
                        if (prev.textContent.trim() && !prev.querySelector('input, select, textarea')) {
                            return prev.textContent.trim();
                        }
                        current = prev;
                    }
                    
                    return '';
                }
                return findLabel(arguments[0]);
                """, 
                element
            )
            return label or ""
        except Exception as e:
            logger.debug(f"Error finding label: {str(e)}")
            return ""
    
    def _get_option_text(self, option_element: WebElement) -> str:
        """
        Get the text content of an option element.
        
        Args:
            option_element: Option WebElement
            
        Returns:
            Option text
        """
        try:
            # Try getting text directly
            text = option_element.text.strip()
            if text:
                return text
            
            # If no text, try getting from child elements
            option_text = self.browser.execute_script(
                """
                function getOptionText(el) {
                    // Try to find text in specific child elements
                    const textEl = el.querySelector('.docssharedWizToggleLabeledContent') || 
                                  el.querySelector('.quantumWizTogglePaperradioOffRadio') ||
                                  el.querySelector('[role="radio"]') ||
                                  el.querySelector('[role="checkbox"]');
                    
                    if (textEl && textEl.textContent.trim()) {
                        return textEl.textContent.trim();
                    }
                    
                    // Get all text nodes within the element
                    let text = '';
                    for (let child of el.childNodes) {
                        if (child.nodeType === 3) { // Text node
                            text += child.textContent.trim();
                        }
                    }
                    
                    return text || 'Option';
                }
                return getOptionText(arguments[0]);
                """, 
                option_element
            )
            return option_text or "Option"
        except Exception as e:
            logger.debug(f"Error getting option text: {str(e)}")
            return "Option"
    
    def _group_elements_by_question(self, elements: List[WebElement]) -> List[List[WebElement]]:
        """
        Group form elements by their associated questions.
        
        Args:
            elements: List of WebElements to group
            
        Returns:
            List of element groups
        """
        if not elements:
            return []
        
        try:
            # Get y-coordinates of elements
            y_positions = []
            for element in elements:
                location = element.location
                y_positions.append(location.get('y', 0))
            
            # Group elements by proximity
            groups = []
            current_group = [elements[0]]
            
            for i in range(1, len(elements)):
                # If this element is close to the previous one, add to current group
                # Otherwise start a new group
                if abs(y_positions[i] - y_positions[i-1]) < 50:
                    current_group.append(elements[i])
                else:
                    if current_group:
                        groups.append(current_group)
                    current_group = [elements[i]]
            
            # Add the last group
            if current_group:
                groups.append(current_group)
            
            return groups
        except Exception as e:
            logger.error(f"Error grouping elements: {str(e)}")
            return [elements]  # Return all elements as a single group on error 