# Agentic Form Filler for Google Forms

An intelligent AI agent system that automatically fills out Google Forms using an agentic architecture.

## Features

- **Extracts questions** from Google Forms dynamically
- **Identifies question types** (text, paragraph, multiple-choice, checkbox, dropdown)
- **Generates relevant answers** using Cohere AI
- **Navigates multi-page forms** automatically
- **Handles form submission**
- **Comprehensive logging** for debugging and analysis

## Architecture

The system implements a modular agentic architecture with three specialized agents:

1. **Reasoning Agent**: Analyzes form questions, determines question types, and decides on answering strategies
2. **Answer Generation Agent**: Generates appropriate responses using Cohere AI
3. **Navigation Agent**: Handles form navigation and submission

## Requirements

- Python 3.8+
- Chrome browser
- ChromeDriver compatible with your Chrome version
- Cohere API key (optional, falls back to mock responses if not provided)

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/agentic-form-filler.git
   cd agentic-form-filler
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Set up your Cohere API key (optional):

   ```
   export COHERE_API_KEY="your-api-key-here"
   ```

   For Windows:

   ```
   set COHERE_API_KEY=your-api-key-here
   ```

## Usage

Run the form filler on a Google Form URL:

```
python main.py https://docs.google.com/forms/d/e/your-form-id/viewform
```

### Options

- By default, the system runs in non-headless mode so you can see the browser automation in action
- To run in headless mode, modify the `headless` parameter in `main.py`

## Logs

Logs are stored in the `logs` directory with timestamped filenames.

## Customization

- Modify the agents to fit your specific use cases
- Adjust the Cohere API parameters in `answer_agent.py` to generate different styles of responses
- Add additional question type detection in `reasoning_agent.py`

## License

MIT

## Disclaimer

This tool is for educational and research purposes only. Always respect websites' terms of service and robots.txt files. Do not use this tool to submit spam or inappropriate content to forms.
