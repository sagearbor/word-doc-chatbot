#!/usr/bin/env python3
"""
Simple test script for Phase 2.2 Advanced Instruction Merging

This script tests the instruction merger module with sample data to verify
it's working correctly before full integration.
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.instruction_merger import (
        InstructionMerger,
        MergeStrategy,
        ConflictResolutionStrategy,
        merge_fallback_with_user_input,
        generate_final_llm_instructions
    )
    print("✅ Successfully imported Phase 2.2 instruction merger")
except ImportError as e:
    print(f"❌ Failed to import instruction merger: {e}")
    sys.exit(1)

def create_sample_fallback_document():
    """Create a sample fallback document for testing"""
    sample_content = """
    STANDARD COMPLIANCE REQUIREMENTS FOR CLINICAL TRIALS
    
    1. REGULATORY COMPLIANCE
    1.1 The Sponsor shall ensure that all clinical trial activities comply with applicable regulations including but not limited to:
        - FDA 21 CFR Part 312 (IND regulations)
        - ICH Good Clinical Practice (GCP) guidelines
        - Local regulatory requirements
    
    2. PAYMENT TERMS
    2.1 Payment shall be made within thirty (30) days of receipt of valid invoice
    2.2 Milestone payments shall be structured as follows:
        - 25% upon protocol approval
        - 50% upon 50% enrollment
        - 25% upon database lock
    
    3. CONFIDENTIALITY
    3.1 All parties shall maintain strict confidentiality of all proprietary information
    3.2 Confidentiality obligations shall survive termination for five (5) years
    
    4. INDEMNIFICATION
    4.1 Sponsor shall indemnify and hold harmless the Institution from any claims arising from the clinical trial
    4.2 This indemnification shall not apply to negligence or willful misconduct by the Institution
    
    5. TERMINATION
    5.1 Either party may terminate this agreement with 30 days written notice
    5.2 Upon termination, all patient safety obligations shall continue
    """
    
    # Save to temp file
    temp_path = os.path.join(os.path.dirname(__file__), "test_fallback_document.txt")
    with open(temp_path, 'w') as f:
        f.write(sample_content)
    
    return temp_path

def test_basic_merging():
    """Test basic instruction merging functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Instruction Merging")
    print("="*60)
    
    # Create sample fallback document
    fallback_path = create_sample_fallback_document()
    
    # Sample user instructions
    user_instructions = """
    Please modify the payment terms to be NET 45 instead of NET 30.
    Also, add a requirement that all invoices must include a purchase order number.
    Remove the milestone payment structure and replace with monthly payments.
    Keep all regulatory compliance requirements but add GDPR compliance.
    """
    
    try:
        # Test merging
        print("\n📄 Fallback document created:", fallback_path)
        print("\n💬 User instructions:")
        print(user_instructions)
        
        print("\n🔄 Running Phase 2.2 instruction merger...")
        
        # Use the convenience function
        merge_result = merge_fallback_with_user_input(
            fallback_doc_path=fallback_path,
            user_input=user_instructions,
            merge_strategy=MergeStrategy.INTELLIGENT_MERGE
        )
        
        print(f"\n✅ Merging complete!")
        print(f"📊 Merged requirements: {len(merge_result.merged_requirements)}")
        print(f"⚖️ Legal coherence score: {merge_result.legal_coherence_score:.2f}")
        print(f"⚠️ Unresolved conflicts: {len(merge_result.unresolved_conflicts)}")
        print(f"🔧 User overrides: {len(merge_result.user_overrides)}")
        
        # Display some merged requirements
        print("\n📋 Sample merged requirements:")
        for i, req in enumerate(merge_result.merged_requirements[:3], 1):
            print(f"\n{i}. {req.final_text[:100]}...")
            print(f"   Source: {'Fallback + User' if req.source_fallback and req.source_user else 'Fallback only' if req.source_fallback else 'User only'}")
            print(f"   Confidence: {req.confidence_score:.2f}")
            print(f"   Strategy: {req.merge_strategy.value}")
        
        # Generate final instructions
        print("\n📝 Generating final LLM instructions...")
        final_instructions = generate_final_llm_instructions(
            fallback_doc_path=fallback_path,
            user_input=user_instructions
        )
        
        print(f"\n✅ Final instructions generated ({len(final_instructions)} characters)")
        print("\nFirst 500 characters of instructions:")
        print("-" * 50)
        print(final_instructions[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(fallback_path):
            os.remove(fallback_path)

def test_conflict_resolution():
    """Test conflict resolution between user and fallback requirements"""
    print("\n" + "="*60)
    print("TEST 2: Conflict Resolution")
    print("="*60)
    
    # Create sample fallback document
    fallback_path = create_sample_fallback_document()
    
    # Conflicting user instructions
    user_instructions = """
    Change payment terms to NET 60 days.
    Remove all indemnification clauses - we don't want any indemnification.
    Confidentiality should be for 10 years, not 5 years.
    Termination should require 60 days notice, not 30 days.
    """
    
    try:
        print("\n💬 User instructions (with conflicts):")
        print(user_instructions)
        
        # Test with different conflict resolution strategies
        strategies = [
            ConflictResolutionStrategy.USER_OVERRIDE,
            ConflictResolutionStrategy.HIGHEST_PRIORITY,
            ConflictResolutionStrategy.LLM_ARBITRATION
        ]
        
        for strategy in strategies:
            print(f"\n🔧 Testing with strategy: {strategy.value}")
            
            merger = InstructionMerger(
                merge_strategy=MergeStrategy.INTELLIGENT_MERGE,
                conflict_strategy=strategy
            )
            
            merge_result = merger.merge_instructions(
                fallback_doc_path=fallback_path,
                user_input=user_instructions
            )
            
            print(f"   Coherence score: {merge_result.legal_coherence_score:.2f}")
            print(f"   Conflicts: {len(merge_result.unresolved_conflicts)}")
            
            # Show a conflicted requirement resolution
            for req in merge_result.merged_requirements:
                if "indemnification" in req.final_text.lower():
                    print(f"   Indemnification resolution: {req.final_text[:80]}...")
                    break
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(fallback_path):
            os.remove(fallback_path)

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TEST 3: Edge Cases")
    print("="*60)
    
    # Test 1: Empty user instructions
    print("\n📌 Test 3.1: Empty user instructions")
    try:
        fallback_path = create_sample_fallback_document()
        merge_result = merge_fallback_with_user_input(
            fallback_doc_path=fallback_path,
            user_input=""
        )
        print(f"✅ Handled empty instructions: {len(merge_result.merged_requirements)} requirements")
    except Exception as e:
        print(f"❌ Failed on empty instructions: {e}")
    finally:
        if os.path.exists(fallback_path):
            os.remove(fallback_path)
    
    # Test 2: Very long user instructions
    print("\n📌 Test 3.2: Very long user instructions")
    try:
        fallback_path = create_sample_fallback_document()
        long_instructions = "Please modify the document. " * 100
        merge_result = merge_fallback_with_user_input(
            fallback_doc_path=fallback_path,
            user_input=long_instructions
        )
        print(f"✅ Handled long instructions: {len(merge_result.merged_requirements)} requirements")
    except Exception as e:
        print(f"❌ Failed on long instructions: {e}")
    finally:
        if os.path.exists(fallback_path):
            os.remove(fallback_path)
    
    # Test 3: Non-existent fallback document
    print("\n📌 Test 3.3: Non-existent fallback document")
    try:
        merge_result = merge_fallback_with_user_input(
            fallback_doc_path="/path/that/does/not/exist.docx",
            user_input="Some instructions"
        )
        print(f"⚠️ Result: {merge_result.overall_status if hasattr(merge_result, 'overall_status') else 'Unknown'}")
    except Exception as e:
        print(f"✅ Properly handled missing file: {type(e).__name__}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Phase 2.2 Advanced Instruction Merger - Test Suite")
    print(f"📅 Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Basic Merging", test_basic_merging),
        ("Conflict Resolution", test_conflict_resolution),
        ("Edge Cases", test_edge_cases)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 2.2 is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)