import os
import shutil
from docx import Document # Requires python-docx

# Assuming word_processor.py is in the same directory
from word_processor import process_document_with_edits, DEFAULT_AUTHOR_NAME

# Ensure the global debug flags in word_processor.py can be controlled
# or that process_document_with_edits passes them through.
# For simplicity here, we rely on process_document_with_edits setting them.

def main():
    input_filename = "sample_input.docx"
    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, "test_output_101.docx")

    # Create a clean copy for each test run if needed, or work on the original
    # shutil.copy(input_filename, "temp_test_doc.docx")
    # current_input = "temp_test_doc.docx"
    current_input = input_filename


    print(f"--- Running Test: Change $101 to $208 ---")
    edits_101 = [
        {
            "contextual_old_text": "cost would be $101 , to a new number", # Crucially, this must match _build_visible_text_map's output for P1
            "specific_old_text": "$101",
            "specific_new_text": "$208",
            "reason_for_change": "Test: Update $101 to $208"
        }
    ]
    success, log_path, log_details, count = process_document_with_edits(
        input_docx_path=current_input,
        output_docx_path=output_filename,
        edits_to_make=edits_101,
        author_name="Test Author",
        debug_mode_flag=True,
        extended_debug_mode_flag=True,
        case_sensitive_flag=True,
        add_comments_param=True
    )
    print(f"Test 101 Success: {success}, Edits Applied: {count}, Log: {log_path}")
    if log_details:
        print("Log Details:")
        for entry in log_details:
            print(f"  - {entry}")
    print(f"Output saved to {output_filename}")

    # --- Add more tests for Bob, MrArbor etc. ---
    # Example:
    # output_filename_bob = os.path.join(output_dir, "test_output_bob.docx")
    # shutil.copy(input_filename, "temp_test_doc_bob.docx") # Use a fresh copy
    # current_input_bob = "temp_test_doc_bob.docx"

    # print(f"\n--- Running Test: Change Bob to Robert ---")
    # edits_bob = [
    #     {
    #         "contextual_old_text": "Bob started the sentence but Bob", # Example context
    #         "specific_old_text": "Bob",
    #         "specific_new_text": "Robert",
    #         "reason_for_change": "Test: Update Bob to Robert"
    #     },
    #     # Add more Bob changes if needed, targeting different contexts
    # ]
    # success_bob, _, _, count_bob = process_document_with_edits(
    #     input_docx_path=current_input_bob,
    #     output_docx_path=output_filename_bob,
    #     edits_to_make=edits_bob,
    #     # ... other params ...
    #     debug_mode_flag=True, extended_debug_mode_flag=True
    # )
    # print(f"Test Bob Success: {success_bob}, Edits Applied: {count_bob}")
    # print(f"Output saved to {output_filename_bob}")


if __name__ == "__main__":
    # You might need to adjust sys.path if word_processor is in a sub-module
    # import sys
    # sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend')) # If test_script is outside backend
    main()