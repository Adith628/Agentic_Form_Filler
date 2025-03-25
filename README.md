# Agentic AI Google Form Filler

This system uses an Agentic AI architecture to autonomously fill out Google Forms. It leverages Cohere AI for answer generation and implements a modular multi-agent approach for form interaction.

## Architecture Overview

The system consists of three specialized AI agents:

1. **Reasoning Agent** - Extracts questions and classifies their types
2. **Answer Generation Agent** - Generates contextually appropriate responses using Cohere AI
3. **Navigation Agent** - Handles form navigation and submission

## Features

- **Intelligent Question Extraction** - Dynamically identifies form elements and extracts questions
- **Question Type Classification** - Automatically detects text, multiple-choice, checkbox, and dropdown questions
- **AI-Powered Response Generation** - Uses Cohere AI to generate contextually relevant answers
- **Multi-Page Form Navigation** - Detects and handles multi-page forms seamlessly
- **Comprehensive Logging** - Logs all actions and responses for tracking
- **Error Handling** - Robust error recovery for browser automation issues
- **Headless Operation** - Can run invisibly for better performance

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- Cohere API key
- ChromeDriver (automatically managed)

## Installation

1. Clone this repository or download the files
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file with your Cohere API key:
   ```
   COHERE_API_KEY=your_api_key_here
   ```
2. Modify the configuration in `config.py` if needed.

## Usage

Run the script with:

```bash
python main.py --form-url "https://forms.gle/your-form-url"
```

Optional arguments:

- `--headless` - Run in headless mode (default: True)
- `--submissions` - Number of submissions to make (default: 1)
- `--debug` - Enable debug logging (default: False)

## File Structure

- `main.py` - Entry point
- `agents/` - Contains the agent implementations
  - `reasoning_agent.py` - For question extraction and classification
  - `answer_agent.py` - For generating responses using Cohere
  - `navigation_agent.py` - For form navigation
- `browser/` - Browser automation code
  - `browser_handler.py` - Selenium wrapper
- `utils/` - Utility functions
  - `logger.py` - Logging setup
  - `element_finder.py` - Helpers for finding form elements
- `config.py` - Configuration settings

## How It Works

1. The system loads the Google Form in a browser
2. The **Reasoning Agent** extracts questions and determines their types
3. For each question:
   - The **Answer Generation Agent** creates an appropriate response
   - The response is filled into the form
4. The **Navigation Agent** detects and clicks "Next" or "Submit" buttons
5. The process repeats until the form is completed and submitted

## Example

```python
from agentic_form_filler import FormFiller

# Initialize the form filler
filler = FormFiller(form_url="https://forms.gle/your-form-url")

# Fill out and submit the form
filler.run()
```
