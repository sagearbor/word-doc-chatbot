import sys
from pathlib import Path

# Create a simple test to invoke the get_llm_suggestions function
# Adjust the import path as necessary based on your project structure
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.llm_handler import get_llm_suggestions

def run_test():
    document_text = (
        "This is a test document. The cost would be $100. "
        "MrArbor is the author. Bob and Bobby are here."
    )
    user_instructions = (
        "Change MrArbor to MrSage and the cost should be at least $208. "
        "Also Bob goes by Robert."
    )
    filename = "test.docx"
    # Call the function
    suggestions = get_llm_suggestions(document_text, user_instructions, filename)
    # Output the suggestions
    print("Suggestions:", suggestions)

if __name__ == "__main__":
    run_test()