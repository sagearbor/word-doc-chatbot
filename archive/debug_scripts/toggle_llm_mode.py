#!/usr/bin/env python3
"""
Script to toggle between LLM and regex modes for legal document processing
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.legal_document_processor import (
    enable_full_llm_mode,
    disable_full_llm_mode,
    enable_llm_extraction,
    disable_llm_extraction,
    enable_llm_instructions,
    disable_llm_instructions,
    get_current_mode,
    USE_LLM_EXTRACTION,
    USE_LLM_INSTRUCTIONS
)

def show_status():
    """Show current configuration status"""
    print("=" * 50)
    print("LEGAL DOCUMENT PROCESSOR - CONFIGURATION")
    print("=" * 50)
    print(f"Current mode: {get_current_mode()}")
    print()
    print("Components:")
    print(f"  📊 Requirement Extraction: {'LLM-based' if USE_LLM_EXTRACTION else 'Regex-based'}")
    print(f"  📝 Instruction Generation: {'LLM-based' if USE_LLM_INSTRUCTIONS else 'Hardcoded patterns'}")
    print()

def show_menu():
    """Show configuration menu"""
    print("Configuration Options:")
    print("1. Enable full LLM mode (recommended)")
    print("2. Disable full LLM mode (use regex/hardcoded)")
    print("3. Enable LLM extraction only")
    print("4. Enable LLM instructions only")
    print("5. Disable LLM extraction only")
    print("6. Disable LLM instructions only")
    print("7. Show current status")
    print("8. Exit")
    print()

def main():
    show_status()
    
    while True:
        show_menu()
        try:
            choice = input("Select option (1-8): ").strip()
            print()
            
            if choice == '1':
                enable_full_llm_mode()
                print("✅ Full LLM mode enabled - AI will understand documents intelligently")
            elif choice == '2':
                disable_full_llm_mode()
                print("✅ Full LLM mode disabled - using regex/hardcoded patterns")
            elif choice == '3':
                enable_llm_extraction()
                print("✅ LLM extraction enabled - AI will extract requirements intelligently")
            elif choice == '4':
                enable_llm_instructions()
                print("✅ LLM instructions enabled - AI will generate smart instructions")
            elif choice == '5':
                disable_llm_extraction()
                print("✅ LLM extraction disabled - using regex patterns")
            elif choice == '6':
                disable_llm_instructions()
                print("✅ LLM instructions disabled - using hardcoded patterns")
            elif choice == '7':
                show_status()
                continue
            elif choice == '8':
                print("Configuration complete!")
                break
            else:
                print("❌ Invalid choice. Please select 1-8.")
                continue
            
            print()
            show_status()
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Legal Document Processor Configuration Tool")
    print()
    main()