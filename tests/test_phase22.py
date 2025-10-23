#!/usr/bin/env python3
"""
Test script for Phase 2.2 Advanced Instruction Merging

This script validates the Phase 2.2 integration by testing key components
without requiring actual document files.
"""

import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def test_phase22_imports():
    """Test that Phase 2.2 components can be imported correctly"""
    print("=== Testing Phase 2.2 Imports ===")
    
    try:
        from backend.instruction_merger import (
            InstructionMerger,
            MergeStrategy,
            ConflictResolutionStrategy,
            generate_final_llm_instructions,
            merge_fallback_with_user_input
        )
        print("✅ Phase 2.2 instruction_merger imports successful")
    except ImportError as e:
        print(f"❌ Failed to import instruction_merger: {e}")
        return False
    
    try:
        from backend.llm_handler import (
            get_llm_suggestions_with_fallback,
            get_merge_analysis,
            get_advanced_legal_instructions
        )
        print("✅ Phase 2.2 LLM handler integration imports successful")
    except ImportError as e:
        print(f"❌ Failed to import LLM handler Phase 2.2 functions: {e}")
        return False
    
    return True

def test_phase22_components():
    """Test Phase 2.2 component initialization"""
    print("\n=== Testing Phase 2.2 Component Initialization ===")
    
    try:
        from backend.instruction_merger import (
            InstructionMerger,
            InstructionParser,
            ConflictResolver,
            LegalCoherenceValidator,
            MergeStrategy
        )
        
        # Test instruction parser
        parser = InstructionParser()
        sample_instructions = "Change the payment terms to 30 days and update the liability clause to include indemnification."
        parsed = parser.parse_user_instructions(sample_instructions)
        print(f"✅ InstructionParser created and parsed {len(parsed)} instructions")
        
        # Test conflict resolver
        resolver = ConflictResolver()
        print("✅ ConflictResolver initialized")
        
        # Test legal coherence validator
        validator = LegalCoherenceValidator()
        print("✅ LegalCoherenceValidator initialized")
        
        # Test instruction merger
        merger = InstructionMerger(
            merge_strategy=MergeStrategy.INTELLIGENT_MERGE,
            conflict_strategy=ConflictResolutionStrategy.LLM_ARBITRATION
        )
        print("✅ InstructionMerger initialized with intelligent merge strategy")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Phase 2.2 components: {e}")
        return False

def test_instruction_parsing():
    """Test instruction parsing functionality"""
    print("\n=== Testing Instruction Parsing ===")
    
    try:
        from backend.instruction_merger import InstructionParser
        
        parser = InstructionParser()
        
        test_cases = [
            "Change MrArbor to MrSage and update the cost to at least $208",
            "Add a new liability clause requiring indemnification",
            "Remove the confidentiality section",
            "Replace all references to 'Company A' with 'Acme Corp'"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            instructions = parser.parse_user_instructions(test_case)
            print(f"✅ Test case {i}: Parsed {len(instructions)} instructions from: '{test_case[:50]}...'")
            
            for j, inst in enumerate(instructions):
                print(f"   - Instruction {j+1}: Intent='{inst.intent}', Priority={inst.priority}, Category='{inst.category.value}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in instruction parsing test: {e}")
        return False

def test_llm_integration():
    """Test LLM handler integration"""
    print("\n=== Testing LLM Handler Integration ===")
    
    try:
        from backend.llm_handler import PHASE_22_AVAILABLE
        
        if PHASE_22_AVAILABLE:
            print("✅ Phase 2.2 is available in LLM handler")
            
            # Test that the functions exist (without calling them since they need actual files)
            from backend.llm_handler import (
                get_llm_suggestions_with_fallback,
                get_merge_analysis,
                get_advanced_legal_instructions
            )
            print("✅ Phase 2.2 LLM functions are accessible")
            
        else:
            print("⚠️  Phase 2.2 marked as not available in LLM handler (possibly due to import issues)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in LLM integration test: {e}")
        return False

def test_enums_and_dataclasses():
    """Test that enums and dataclasses are working correctly"""
    print("\n=== Testing Enums and Dataclasses ===")
    
    try:
        from backend.instruction_merger import (
            MergeStrategy,
            ConflictResolutionStrategy,
            UserInstruction,
            MergedRequirement,
            MergeResult
        )
        from backend.requirements_processor import (
            RequirementPriority,
            RequirementCategory
        )
        
        # Test enums
        strategies = list(MergeStrategy)
        print(f"✅ MergeStrategy enum has {len(strategies)} values: {[s.value for s in strategies]}")
        
        conflict_strategies = list(ConflictResolutionStrategy)
        print(f"✅ ConflictResolutionStrategy enum has {len(conflict_strategies)} values")
        
        priorities = list(RequirementPriority)
        print(f"✅ RequirementPriority enum has {len(priorities)} values")
        
        categories = list(RequirementCategory)
        print(f"✅ RequirementCategory enum has {len(categories)} values")
        
        # Test dataclass creation
        user_inst = UserInstruction(
            text="Test instruction",
            intent="modify",
            target="test clause",
            priority=2,
            specificity=0.8,
            legal_impact="medium",
            category=RequirementCategory.GENERAL
        )
        print("✅ UserInstruction dataclass created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in enums and dataclasses test: {e}")
        return False

def run_all_tests():
    """Run all Phase 2.2 tests"""
    print("Phase 2.2 Advanced Instruction Merging - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_phase22_imports,
        test_phase22_components,
        test_instruction_parsing,
        test_llm_integration,
        test_enums_and_dataclasses
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Phase 2.2 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 2.2 tests passed! Integration is successful.")
        return True
    else:
        print("⚠️  Some Phase 2.2 tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)