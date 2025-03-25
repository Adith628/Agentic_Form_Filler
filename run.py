#!/usr/bin/env python
"""
Standalone launcher script for the Agentic AI Google Form Filler.
This script can be run directly from the command line.
"""

import sys
import os

# Add parent directory to path to allow importing the package
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import the main function from the package
from agentic_form_filler.main import main

if __name__ == "__main__":
    # Run the main function
    exit(main()) 