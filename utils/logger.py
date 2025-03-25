"""
Logging utility for the form filler.
"""
import sys
import os
import json
from datetime import datetime
from loguru import logger
from typing import Dict, List, Any, Optional, Union
from ..config import get_config

def setup_logger(config: Dict[str, Any] = None) -> logger:
    """
    Configure and setup the logger with the given configuration.
    
    Args:
        config: Custom logging configuration (optional)
        
    Returns:
        Configured logger instance
    """
    # Use default config if none provided
    if config is None:
        config = get_config("LOGGING_CONFIG")
        
        # Override the level from environment variable if it exists
        env_level = os.getenv("LOG_LEVEL")
        if env_level:
            config["level"] = env_level
    
    # Enhanced format with color highlighting
    default_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    
    # Remove default logger
    logger.remove()
    
    # Add console logger with enhanced formatting
    logger.add(
        sys.stderr,
        level=config.get("level", "INFO"),
        format=config.get("format", default_format),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file logger if specified
    if "file" in config:
        logger.add(
            config["file"],
            rotation=config.get("rotation", "10 MB"),
            level=config.get("level", "DEBUG"),  # Always log debugging info to file
            format=config.get("format", default_format),
            backtrace=True,
            diagnose=True,
        )
    
    # Add a separate file for detailed question and answer logging
    question_log = "questions_answers.log"
    logger.add(
        question_log,
        rotation="10 MB",
        level="INFO",
        format=default_format,
        filter=lambda record: any(keyword in record["message"] for keyword in 
                               ["QUESTION", "TEXT:", "TYPE:", "OPTIONS:", "ANSWER:", "SELECTED", "FILLING", "GENERATING"])
    )
    
    # Also create a structured JSON log of questions and answers
    logger.add(
        "qa_structured.jsonl",
        rotation="10 MB",
        level="INFO",
        format="{message}",
        filter=lambda record: record["name"] == "qa_logger"
    )
    
    logger.info(f"Logging initialized - Console level: {config.get('level', 'INFO')}")
    logger.info(f"Detailed question/answer logs in '{question_log}'")
    logger.info(f"Structured question/answer data in 'qa_structured.jsonl'")
    
    return logger

def log_qa_entry(question: Dict[str, Any], answer: Any) -> None:
    """
    Log a structured question and answer entry to the dedicated JSON log file.
    
    Args:
        question: Dictionary containing question details
        answer: The generated answer
    """
    qa_logger = logger.bind(name="qa_logger")
    
    # Create structured entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer
    }
    
    # Log as JSON string
    qa_logger.info(json.dumps(entry))

def log_structured_question(question_text: str, question_type: str, 
                           question_number: int, total_questions: int,
                           options: List[str] = None) -> Dict[str, Any]:
    """
    Create a structured question record and return it.
    
    Args:
        question_text: The text of the question
        question_type: The type of the question (text, multiple-choice, etc.)
        question_number: Question number (1-based)
        total_questions: Total number of questions
        options: List of options for multiple-choice questions
        
    Returns:
        Structured question dictionary
    """
    question_data = {
        "text": question_text,
        "type": question_type,
        "number": question_number,
        "total": total_questions
    }
    
    if options:
        question_data["options"] = options
    
    return question_data

def log_structured_answer(answer: Any, question_type: str, options: List[str] = None) -> Any:
    """
    Create a structured answer record.
    
    Args:
        answer: The answer (text, index, or list of indices)
        question_type: The type of the related question
        options: List of options for reference
        
    Returns:
        Structured answer (might be the original or enhanced with metadata)
    """
    if question_type in ["multiple_choice", "dropdown"] and isinstance(answer, int) and options:
        if 0 <= answer < len(options):
            return {
                "selected_index": answer,
                "selected_value": options[answer]
            }
    elif question_type == "checkbox" and isinstance(answer, list) and options:
        selected = []
        for idx in answer:
            if 0 <= idx < len(options):
                selected.append({
                    "index": idx,
                    "value": options[idx]
                })
        return {
            "selected_indices": [idx for idx in answer if 0 <= idx < len(options)],
            "selected_values": selected
        }
    
    # For text or other types, return as is
    return answer 