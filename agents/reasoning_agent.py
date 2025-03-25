#!/usr/bin/env python3
# Reasoning Agent - Responsible for analyzing questions and determining strategies

import logging
from typing import Dict, Tuple, Any, List

logger = logging.getLogger(__name__)

class ReasoningAgent:
    """
    The Reasoning Agent is responsible for:
    1. Analyzing and classifying form questions
    2. Determining required vs optional fields
    3. Determining appropriate answering strategies
    """
    
    # Question type constants
    TYPE_TEXT = "text"
    TYPE_PARAGRAPH = "paragraph"
    TYPE_MULTIPLE_CHOICE = "multiple_choice"
    TYPE_CHECKBOX = "checkbox"
    TYPE_DROPDOWN = "dropdown"
    TYPE_UNKNOWN = "unknown"
    
    def __init__(self):
        """Initialize the Reasoning Agent."""
        logger.info("Initializing Reasoning Agent")
    
    def analyze_question(self, question: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Analyze a question and determine its type and if it's required.
        
        Args:
            question: Dictionary containing question data including element, text, etc.
            
        Returns:
            Tuple containing (question_type, is_required)
        """
        logger.debug(f"Analyzing question: {question['text']}")
        
        # Extract question element and text
        element = question['element']
        question_text = question['text']
        
        # Default values
        question_type = self.TYPE_UNKNOWN
        is_required = False
        
        try:
            # Detect if question is required
            # In Google Forms, required questions typically have an asterisk or special class
            is_required = '*' in question_text or self._check_required_class(element)
            
            # Analyze question type based on HTML structure
            question_type = self._detect_question_type(element, question)
            
            logger.debug(f"Question type determined as: {question_type}, Required: {is_required}")
            
        except Exception as e:
            logger.error(f"Error analyzing question '{question_text}': {str(e)}")
        
        return question_type, is_required
    
    def _detect_question_type(self, element, question: Dict[str, Any]) -> str:
        """
        Detect the type of question based on the element's structure.
        
        Args:
            element: The HTML element representing the question
            question: The question dictionary with additional data
            
        Returns:
            String representing the question type
        """
        # Check for common Google Form input patterns
        
        # If question has radio buttons, it's multiple choice
        if self._has_element_type(element, "radio"):
            return self.TYPE_MULTIPLE_CHOICE
            
        # If question has checkboxes, it's checkbox type
        elif self._has_element_type(element, "checkbox"):
            return self.TYPE_CHECKBOX
            
        # If question has a select/dropdown element
        elif self._has_element_type(element, "select"):
            return self.TYPE_DROPDOWN
            
        # If question has a textarea, it's paragraph type
        elif self._has_element_type(element, "textarea"):
            return self.TYPE_PARAGRAPH
            
        # If question has a short text input
        elif self._has_element_type(element, "text") or self._has_element_type(element, "input"):
            # Check if it's a short answer by looking at size/class
            if self._is_short_answer(element):
                return self.TYPE_TEXT
            else:
                return self.TYPE_PARAGRAPH
                
        # Default to unknown if type couldn't be determined
        return self.TYPE_UNKNOWN
    
    def _check_required_class(self, element) -> bool:
        """
        Check if the element has classes indicating it's required.
        
        Args:
            element: The HTML element
            
        Returns:
            Boolean indicating if the question is required
        """
        # Google Forms typically uses specific classes for required questions
        # This is a simplified implementation - actual implementation would need to check
        # specific class names used in Google Forms
        try:
            # Check for common required indicators in class names
            class_name = element.get_attribute("class")
            required_indicators = ["required", "mandatory", "freebirdFormviewerViewItemsItemRequiredAsterisk"]
            
            if class_name:
                for indicator in required_indicators:
                    if indicator in class_name:
                        return True
                
            # Check for the asterisk in nearby elements
            # In Google Forms, required questions often have an asterisk in a child element
            asterisk_elements = element.find_elements_by_xpath(".//*[contains(text(), '*')]")
            if asterisk_elements:
                return True
                
        except Exception as e:
            logger.warning(f"Error checking if field is required: {str(e)}")
            
        return False

    def _has_element_type(self, parent_element, element_type: str) -> bool:
        """
        Check if the parent element contains child elements of the specified type.
        
        Args:
            parent_element: The parent HTML element
            element_type: The type of element to look for (input, select, etc.)
            
        Returns:
            Boolean indicating if the element type was found
        """
        try:
            # For input elements, check the type attribute
            if element_type in ["radio", "checkbox", "text"]:
                elements = parent_element.find_elements_by_xpath(f".//input[@type='{element_type}']")
            else:
                # For other elements, check the tag name
                elements = parent_element.find_elements_by_xpath(f".//{element_type}")
                
            return len(elements) > 0
        except Exception as e:
            logger.warning(f"Error checking for element type {element_type}: {str(e)}")
            return False
    
    def _is_short_answer(self, element) -> bool:
        """
        Determine if a text input is a short answer or paragraph.
        
        Args:
            element: The HTML element
            
        Returns:
            Boolean indicating if it's a short answer (True) or paragraph (False)
        """
        try:
            # Check for size attributes
            size_attr = element.get_attribute("size")
            maxlength_attr = element.get_attribute("maxlength")
            class_name = element.get_attribute("class")
            
            # If input has small size or maxlength, it's likely a short answer
            if size_attr and int(size_attr) < 50:
                return True
                
            if maxlength_attr and int(maxlength_attr) < 200:
                return True
                
            # Check class name for indicators
            if class_name:
                short_indicators = ["short", "small", "freebirdFormviewerViewItemsTextShortText"]
                for indicator in short_indicators:
                    if indicator in class_name:
                        return True
                
                paragraph_indicators = ["paragraph", "long", "freebirdFormviewerViewItemsTextLongText"]
                for indicator in paragraph_indicators:
                    if indicator in class_name:
                        return False
                
        except Exception as e:
            logger.warning(f"Error determining if input is short answer: {str(e)}")
            
        # Default to short answer if can't determine
        return True 