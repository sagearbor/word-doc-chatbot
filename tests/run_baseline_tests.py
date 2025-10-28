#!/usr/bin/env python3
"""
Run baseline tests for all test cases and document results
"""

import requests
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path for word_processor functions
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from word_processor import extract_tracked_changes_structured

BASE_URL = "http://127.0.0.1:8888"
TEST_CASES_DIR = Path(__file__).parent / "test_cases"

def test_case_01():
    """Test Case 01: Service Agreement Tightening"""
    print("\n" + "="*80)
    print("TEST CASE 01: Service Agreement Tightening")
    print("="*80)

    case_dir = TEST_CASES_DIR / "case_01_service_agreement"
    input_file = case_dir / "input" / "case_01_input_service_agreement.docx"
    fallback_file = case_dir / "fallback" / "case_01_fallback_requirements.docx"

    print(f"\n📄 Input: {input_file.name}")
    print(f"📋 Fallback: {fallback_file.name}")

    # Process document
    try:
        with open(input_file, 'rb') as f_input, open(fallback_file, 'rb') as f_fallback:
            files = {
                'input_file': (input_file.name, f_input, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                'fallback_file': (fallback_file.name, f_fallback, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            data = {
                'author_name': 'AI Assistant',
                'case_sensitive': 'true',
                'add_comments': 'true',
                'debug_mode': 'true',
                'extended_debug_mode': 'true'
            }

            print("\n🔄 Processing document...")
            response = requests.post(f"{BASE_URL}/process-document-with-fallback/", files=files, data=data, timeout=300)

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Processing successful!")
            print(f"   Status: {result.get('status_message', 'N/A')}")
            print(f"   Edits suggested: {result.get('edits_suggested_count', 0)}")
            print(f"   Edits applied: {result.get('edits_applied_count', 0)}")
            print(f"   Edits failed: {result.get('edits_failed_count', 0)}")

            # Save output file
            if 'processed_file' in result:
                output_path = case_dir / "expected" / f"case_01_baseline_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                import base64
                with open(output_path, 'wb') as f:
                    f.write(base64.b64decode(result['processed_file']))
                print(f"\n💾 Saved output: {output_path}")

                # Analyze output
                changes = extract_tracked_changes_structured(str(output_path))
                print(f"\n📊 Tracked changes in output: {len(changes)}")
                for i, change in enumerate(changes[:5], 1):
                    print(f"   {i}. {change.change_type}: \"{change.old_text[:40]}...\" → \"{change.new_text[:40]}...\"")
                if len(changes) > 5:
                    print(f"   ... and {len(changes) - 5} more")

            # Compare against expected (10 changes)
            expected_count = 10
            actual_count = result.get('edits_applied_count', 0)
            success_rate = actual_count / expected_count if expected_count > 0 else 0

            print(f"\n📈 RESULTS:")
            print(f"   Expected changes: {expected_count}")
            print(f"   Actual changes: {actual_count}")
            print(f"   Success rate: {success_rate:.1%}")
            print(f"   Missed changes: {expected_count - actual_count}")

            return {
                "test_case_id": "case_01",
                "status": "completed",
                "date": datetime.now().isoformat(),
                "expected_changes": expected_count,
                "changes_applied": actual_count,
                "changes_missed": expected_count - actual_count,
                "success_rate": success_rate,
                "details": result
            }
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            print(f"   {response.text[:500]}")
            return {"test_case_id": "case_01", "status": "failed", "error": response.text}

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return {"test_case_id": "case_01", "status": "error", "error": str(e)}

def test_case_02():
    """Test Case 02: Complex Contract Editing"""
    print("\n" + "="*80)
    print("TEST CASE 02: Complex Contract Editing")
    print("="*80)

    case_dir = TEST_CASES_DIR / "case_02_contract_editing"
    input_file = case_dir / "input" / "case_02_input_service_agreement.docx"
    fallback_file = case_dir / "fallback" / "case_02_fallback_comprehensive_guidelines.docx"

    print(f"\n📄 Input: {input_file.name}")
    print(f"📋 Fallback: {fallback_file.name}")

    try:
        with open(input_file, 'rb') as f_input, open(fallback_file, 'rb') as f_fallback:
            files = {
                'input_file': (input_file.name, f_input, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                'fallback_file': (fallback_file.name, f_fallback, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            data = {
                'author_name': 'AI Assistant',
                'case_sensitive': 'true',
                'add_comments': 'true',
                'debug_mode': 'true',
                'extended_debug_mode': 'true'
            }

            print("\n🔄 Processing document...")
            response = requests.post(f"{BASE_URL}/process-document-with-fallback/", files=files, data=data, timeout=300)

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Processing successful!")
            print(f"   Status: {result.get('status_message', 'N/A')}")
            print(f"   Edits suggested: {result.get('edits_suggested_count', 0)}")
            print(f"   Edits applied: {result.get('edits_applied_count', 0)}")
            print(f"   Edits failed: {result.get('edits_failed_count', 0)}")

            # Save output file
            if 'processed_file' in result:
                output_path = case_dir / "expected" / f"case_02_baseline_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                import base64
                with open(output_path, 'wb') as f:
                    f.write(base64.b64decode(result['processed_file']))
                print(f"\n💾 Saved output: {output_path}")

                # Analyze output
                changes = extract_tracked_changes_structured(str(output_path))
                print(f"\n📊 Tracked changes in output: {len(changes)}")
                for i, change in enumerate(changes[:5], 1):
                    print(f"   {i}. {change.change_type}: \"{change.old_text[:40]}...\" → \"{change.new_text[:40]}...\"")
                if len(changes) > 5:
                    print(f"   ... and {len(changes) - 5} more")

            expected_count = 9
            actual_count = result.get('edits_applied_count', 0)
            success_rate = actual_count / expected_count if expected_count > 0 else 0

            print(f"\n📈 RESULTS:")
            print(f"   Expected changes: {expected_count}")
            print(f"   Actual changes: {actual_count}")
            print(f"   Success rate: {success_rate:.1%}")
            print(f"   Missed changes: {expected_count - actual_count}")

            return {
                "test_case_id": "case_02",
                "status": "completed",
                "date": datetime.now().isoformat(),
                "expected_changes": expected_count,
                "changes_applied": actual_count,
                "changes_missed": expected_count - actual_count,
                "success_rate": success_rate,
                "details": result
            }
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            print(f"   {response.text[:500]}")
            return {"test_case_id": "case_02", "status": "failed", "error": response.text}

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return {"test_case_id": "case_02", "status": "error", "error": str(e)}

def test_case_03():
    """Test Case 03: Existing Tracked Changes Preservation"""
    print("\n" + "="*80)
    print("TEST CASE 03: Existing Tracked Changes Preservation (CRITICAL)")
    print("="*80)

    case_dir = TEST_CASES_DIR / "case_03_existing_changes"
    input_file = case_dir / "input" / "case_03_input_with_existing_changes.docx"
    prompt_file = case_dir / "prompts" / "case_03_prompt_additional_edits.txt"

    print(f"\n📄 Input: {input_file.name}")
    print(f"📝 Prompt: {prompt_file.name}")

    # First, analyze existing changes
    print("\n🔍 Analyzing existing tracked changes...")
    original_changes = extract_tracked_changes_structured(str(input_file))
    print(f"   Found {len(original_changes)} existing tracked changes")
    for i, change in enumerate(original_changes[:3], 1):
        print(f"   {i}. {change.change_type}: \"{change.old_text[:30]}...\" → \"{change.new_text[:30]}...\"")
    if len(original_changes) > 3:
        print(f"   ... and {len(original_changes) - 3} more")

    # Read prompt
    with open(prompt_file, 'r') as f:
        user_instructions = f.read()

    try:
        with open(input_file, 'rb') as f_input:
            files = {
                'file': (input_file.name, f_input, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            data = {
                'instructions': user_instructions,
                'author_name': 'AI Assistant',
                'case_sensitive': 'true',
                'add_comments': 'true',
                'debug_mode': 'true',
                'extended_debug_mode': 'true'
            }

            print("\n🔄 Processing document with prompt...")
            response = requests.post(f"{BASE_URL}/process-document/", files=files, data=data, timeout=300)

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Processing successful!")
            print(f"   Status: {result.get('status_message', 'N/A')}")
            print(f"   Edits suggested: {result.get('edits_suggested_count', 0)}")
            print(f"   Edits applied: {result.get('edits_applied_count', 0)}")

            # Save output and analyze
            if 'processed_file' in result:
                output_path = case_dir / "expected" / f"case_03_baseline_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                import base64
                with open(output_path, 'wb') as f:
                    f.write(base64.b64decode(result['processed_file']))
                print(f"\n💾 Saved output: {output_path}")

                # Analyze output changes
                final_changes = extract_tracked_changes_structured(str(output_path))
                print(f"\n📊 Tracked changes in output: {len(final_changes)}")
                for i, change in enumerate(final_changes[:8], 1):
                    print(f"   {i}. {change.change_type}: \"{change.old_text[:30]}...\" → \"{change.new_text[:30]}...\"")
                if len(final_changes) > 8:
                    print(f"   ... and {len(final_changes) - 8} more")

                # CRITICAL CHECK: Verify original changes preserved
                original_count = len(original_changes)
                new_changes_expected = 4
                total_expected = original_count + new_changes_expected
                actual_total = len(final_changes)

                original_preserved = actual_total >= original_count

                print(f"\n📈 CRITICAL RESULTS:")
                print(f"   Original changes: {original_count}")
                print(f"   Expected new changes: {new_changes_expected}")
                print(f"   Total expected: {total_expected}")
                print(f"   Actual total changes: {actual_total}")
                print(f"   Original preserved: {'✅ YES' if original_preserved else '❌ NO - CRITICAL FAILURE'}")

                if not original_preserved:
                    print(f"\n❌ CRITICAL FAILURE: Original changes were lost!")
                    print(f"   Lost changes: {original_count - actual_total}")

                new_changes_applied = max(0, actual_total - original_count)
                success_rate = new_changes_applied / new_changes_expected if new_changes_expected > 0 else 0

                print(f"   New changes applied: {new_changes_applied}/{new_changes_expected}")
                print(f"   New changes success rate: {success_rate:.1%}")

                return {
                    "test_case_id": "case_03",
                    "status": "completed",
                    "date": datetime.now().isoformat(),
                    "original_changes_count": original_count,
                    "expected_new_changes": new_changes_expected,
                    "actual_total_changes": actual_total,
                    "original_changes_preserved": original_preserved,
                    "new_changes_applied": new_changes_applied,
                    "success_rate": success_rate,
                    "critical_test_passed": original_preserved,
                    "details": result
                }
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            print(f"   {response.text[:500]}")
            return {"test_case_id": "case_03", "status": "failed", "error": response.text}

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return {"test_case_id": "case_03", "status": "error", "error": str(e)}

def main():
    """Run all tests and generate report"""
    print("\n" + "="*80)
    print("BASELINE TEST SUITE - Word Document Chatbot")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Cases Directory: {TEST_CASES_DIR}")
    print(f"Backend URL: {BASE_URL}")

    # Run all tests
    results = []

    result_01 = test_case_01()
    results.append(result_01)

    result_02 = test_case_02()
    results.append(result_02)

    result_03 = test_case_03()
    results.append(result_03)

    # Generate summary
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)

    for result in results:
        if result['status'] == 'completed':
            print(f"\n{result['test_case_id'].upper()}:")
            if 'success_rate' in result:
                print(f"  Success Rate: {result['success_rate']:.1%}")
                print(f"  Changes: {result.get('changes_applied', 0)}/{result.get('expected_changes', 0)}")
            if 'critical_test_passed' in result:
                print(f"  Original Changes Preserved: {'✅ PASS' if result['critical_test_passed'] else '❌ FAIL'}")
        else:
            print(f"\n{result['test_case_id'].upper()}: {result['status'].upper()}")

    # Save results
    results_file = TEST_CASES_DIR / f"baseline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")

    print("\n" + "="*80)
    print("BASELINE TESTING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
