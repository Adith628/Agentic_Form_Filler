"""
Basic tests for the Agentic AI Google Form Filler.
"""
import unittest
from agentic_form_filler import FormFiller

class TestFormFiller(unittest.TestCase):
    """Test the FormFiller class."""
    
    def test_import(self):
        """Test that the FormFiller class can be imported."""
        self.assertIsNotNone(FormFiller)
    
    def test_initialization(self):
        """Test that the FormFiller class can be initialized."""
        # This test just checks that initialization doesn't crash
        # It doesn't actually use the Cohere API or Selenium
        try:
            # Use a fake URL and API key
            filler = FormFiller(
                form_url="https://example.com/form",
                cohere_api_key="fake_api_key",
                # Don't initialize the browser
                headless=True
            )
            self.assertIsNotNone(filler)
        except Exception as e:
            # Make sure the error isn't related to initialization
            self.fail(f"FormFiller initialization raised an exception: {e}")

if __name__ == "__main__":
    unittest.main() 