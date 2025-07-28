import json
import re
from typing import List, Dict, Optional, Any

from .ai_client import get_chat_response # Assuming .ai_client is in the same directory or correctly pathed

# Phase 2.2 Integration - Advanced Instruction Merging
try:
    from .instruction_merger import (
        generate_final_llm_instructions,
        merge_fallback_with_user_input,
        MergeStrategy
    )
    PHASE_22_AVAILABLE = True
    print("Phase 2.2 Advanced Instruction Merging integrated successfully")
except ImportError:
    PHASE_22_AVAILABLE = False
    print("Phase 2.2 Advanced Instruction Merging not available")

# --- Specialized Legal Document Prompts ---

def get_llm_legal_requirement_analysis(requirement_text: str, context: str = "") -> Optional[str]:
    """
    Analyze a legal requirement using specialized prompts for legal documents
    """
    prompt = f"""You are a legal document analysis expert. Please analyze the following legal requirement:

    Requirement: "{requirement_text}"
    {f"Context: {context}" if context else ""}
    
    Please provide a structured analysis covering:
    
    1. **Obligation Type**: Is this a "must", "shall", "should", or "may" requirement?
    2. **Responsible Party**: Who must comply with this requirement?
    3. **Compliance Timing**: When must this be fulfilled (immediate, ongoing, milestone-based)?
    4. **Legal Risk Level**: What are the consequences of non-compliance (critical, high, medium, low)?
    5. **Implementation Complexity**: How difficult is this to implement (simple, moderate, complex)?
    6. **Key Legal Terms**: What specific legal terminology must be preserved exactly?
    
    Keep the analysis concise but thorough for legal compliance purposes."""
    
    system_prompt = "You are a legal document analysis specialist with expertise in contract requirements, compliance obligations, and risk assessment."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = get_chat_response(messages, temperature=0.0, max_tokens=800)
        return response
    except Exception as e:
        print(f"Error getting legal requirement analysis: {e}")
        return "Legal analysis not available due to processing error."

def get_llm_fallback_instruction_generation(requirements_list: List[str], document_type: str = "legal contract") -> Optional[str]:
    """
    Generate specialized instructions for applying fallback document requirements
    """
    requirements_text = "\n".join([f"{i+1}. {req}" for i, req in enumerate(requirements_list)])
    
    prompt = f"""You are a legal document processing specialist. Please convert the following fallback document requirements into precise instructions for modifying a {document_type}.

    Fallback Requirements:
    {requirements_text}
    
    Please generate instructions that:
    
    1. **Preserve Legal Structure**: Maintain hierarchical numbering (1.1, 1.2, etc.) and section organization
    2. **Maintain Legal Language**: Keep exact legal terminology ("must", "shall", "required") without alteration
    3. **Add Tracked Changes**: All modifications must be added as tracked changes with proper attribution
    4. **Priority Handling**: Critical requirements (must/shall) take absolute precedence
    5. **Compliance Focus**: Ensure regulatory and compliance requirements are implemented exactly
    6. **Cross-Reference Preservation**: Maintain all legal cross-references and definitions
    7. **Formatting Retention**: Preserve legal formatting (bold, underline) critical for enforceability
    
    Format the instructions clearly for an AI system that will apply these changes to the document.
    
    Begin with the highest priority requirements and include implementation guidance for complex legal obligations."""
    
    system_prompt = "You are an expert in legal document modification with deep understanding of contract requirements, compliance obligations, and legal formatting preservation."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = get_chat_response(messages, temperature=0.0, max_tokens=1200)
        return response
    except Exception as e:
        print(f"Error generating fallback instructions: {e}")
        return "Fallback instruction generation failed due to processing error."

def get_llm_legal_conflict_resolution(conflicting_requirements: List[Dict], document_context: str = "") -> Optional[str]:
    """
    Get LLM assistance for resolving conflicts between legal requirements
    """
    conflicts_text = "\n".join([
        f"Requirement {i+1}: {req.get('text', 'N/A')}\nConflict: {req.get('conflict_description', 'N/A')}\n"
        for i, req in enumerate(conflicting_requirements)
    ])
    
    prompt = f"""You are a legal document expert specializing in requirement conflict resolution. Please analyze these conflicting legal requirements and provide resolution guidance:

    {f"Document Context: {document_context}" if document_context else ""}
    
    Conflicting Requirements:
    {conflicts_text}
    
    Please provide:
    
    1. **Conflict Analysis**: What exactly conflicts between these requirements?
    2. **Legal Hierarchy**: Which requirement should take precedence based on legal principles?
    3. **Resolution Strategy**: How should these conflicts be resolved while maintaining legal validity?
    4. **Implementation Guidance**: Specific steps to resolve the conflict in the document
    5. **Risk Assessment**: What are the legal risks of each resolution approach?
    
    Prioritize compliance with regulatory requirements and legal enforceability in your recommendations."""
    
    system_prompt = "You are a legal expert with expertise in contract law, requirement hierarchies, and legal conflict resolution."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = get_chat_response(messages, temperature=0.0, max_tokens=1000)
        return response
    except Exception as e:
        print(f"Error getting conflict resolution guidance: {e}")
        return "Conflict resolution guidance not available due to processing error."

# --- Phase 2.2 Advanced Instruction Merging Functions ---

def get_llm_suggestions_with_fallback(document_text: str, user_instructions: str, filename: str, 
                                    fallback_doc_path: Optional[str] = None) -> List[Dict]:
    """
    Enhanced version of get_llm_suggestions that uses Phase 2.2 advanced instruction merging
    when a fallback document is provided.
    
    Args:
        document_text: The target document text
        user_instructions: User's instructions
        filename: Name of the target document
        fallback_doc_path: Path to fallback document (optional)
    
    Returns:
        List of edit suggestions
    """
    
    if not PHASE_22_AVAILABLE or not fallback_doc_path:
        # Fall back to original method
        print("Using original get_llm_suggestions (Phase 2.2 not available or no fallback document)")
        return get_llm_suggestions(document_text, user_instructions, filename)
    
    try:
        print("Using Phase 2.2 Advanced Instruction Merging...")
        
        # Generate merged instructions using Phase 2.2
        merged_instructions = generate_final_llm_instructions(
            fallback_doc_path, 
            user_instructions, 
            MergeStrategy.INTELLIGENT_MERGE
        )
        
        print(f"Phase 2.2 generated {len(merged_instructions)} characters of merged instructions")
        print("Merged instructions preview:", merged_instructions[:200] + "..." if len(merged_instructions) > 200 else merged_instructions)
        
        # Use the merged instructions with the original document processing
        return get_llm_suggestions(document_text, merged_instructions, filename)
        
    except Exception as e:
        print(f"Error in Phase 2.2 advanced merging: {e}")
        print("Falling back to original get_llm_suggestions method")
        return get_llm_suggestions(document_text, user_instructions, filename)

def get_merge_analysis(fallback_doc_path: str, user_instructions: str) -> Dict[str, Any]:
    """
    Get detailed analysis of the Phase 2.2 merging process without applying changes.
    
    Args:
        fallback_doc_path: Path to fallback document
        user_instructions: User's instructions
    
    Returns:
        Dictionary containing merge analysis details
    """
    
    if not PHASE_22_AVAILABLE:
        return {
            "error": "Phase 2.2 Advanced Instruction Merging not available",
            "available": False
        }
    
    try:
        print("Performing Phase 2.2 merge analysis...")
        
        # Get detailed merge result
        merge_result = merge_fallback_with_user_input(
            fallback_doc_path, 
            user_instructions, 
            MergeStrategy.INTELLIGENT_MERGE
        )
        
        # Convert to serializable format
        analysis = {
            "available": True,
            "total_merged_requirements": len(merge_result.merged_requirements),
            "legal_coherence_score": merge_result.legal_coherence_score,
            "unresolved_conflicts": len(merge_result.unresolved_conflicts),
            "user_overrides": len(merge_result.user_overrides),
            "validation_warnings": len(merge_result.validation_warnings),
            "processing_summary": merge_result.processing_summary,
            "high_confidence_requirements": len([r for r in merge_result.merged_requirements if r.confidence_score >= 0.8]),
            "medium_confidence_requirements": len([r for r in merge_result.merged_requirements if 0.6 <= r.confidence_score < 0.8]),
            "low_confidence_requirements": len([r for r in merge_result.merged_requirements if r.confidence_score < 0.6]),
            "warnings": merge_result.validation_warnings[:5] if merge_result.validation_warnings else [],  # First 5 warnings
            "sample_requirements": [
                {
                    "text": req.final_text[:100] + "..." if len(req.final_text) > 100 else req.final_text,
                    "confidence": req.confidence_score,
                    "source": "fallback+user" if req.source_fallback and req.source_user else 
                             ("fallback" if req.source_fallback else "user"),
                    "strategy": req.merge_strategy.value
                }
                for req in merge_result.merged_requirements[:3]  # First 3 requirements as samples
            ]
        }
        
        print(f"Phase 2.2 merge analysis complete: {analysis['total_merged_requirements']} requirements, coherence {analysis['legal_coherence_score']:.2f}")
        return analysis
        
    except Exception as e:
        print(f"Error in Phase 2.2 merge analysis: {e}")
        return {
            "error": f"Phase 2.2 merge analysis failed: {str(e)}",
            "available": False
        }

def get_advanced_legal_instructions(fallback_doc_path: str, user_instructions: str, 
                                  merge_strategy: str = "intelligent_merge") -> str:
    """
    Generate advanced legal instructions using Phase 2.2 merging with specified strategy.
    
    Args:
        fallback_doc_path: Path to fallback document
        user_instructions: User's instructions  
        merge_strategy: Merge strategy to use ("intelligent_merge", "user_priority", "fallback_priority", "legal_hierarchy")
    
    Returns:
        Merged instructions string ready for LLM processing
    """
    
    if not PHASE_22_AVAILABLE:
        return f"Phase 2.2 Advanced Instruction Merging not available. User instructions: {user_instructions}"
    
    try:
        # Convert string strategy to enum
        strategy_map = {
            "intelligent_merge": MergeStrategy.INTELLIGENT_MERGE,
            "user_priority": MergeStrategy.USER_PRIORITY,
            "fallback_priority": MergeStrategy.FALLBACK_PRIORITY,
            "legal_hierarchy": MergeStrategy.LEGAL_HIERARCHY
        }
        
        strategy = strategy_map.get(merge_strategy, MergeStrategy.INTELLIGENT_MERGE)
        
        print(f"Generating advanced legal instructions with strategy: {merge_strategy}")
        
        merged_instructions = generate_final_llm_instructions(fallback_doc_path, user_instructions, strategy)
        
        print(f"Generated {len(merged_instructions)} characters of advanced legal instructions")
        return merged_instructions
        
    except Exception as e:
        print(f"Error generating advanced legal instructions: {e}")
        return f"Error in Phase 2.2 processing: {str(e)}. Fallback user instructions: {user_instructions}"

# --- Function for Approach 1: Summarizing a pre-parsed list of changes ---
def get_llm_analysis_from_summary(changes_summary_text: str, filename: str) -> Optional[str]:
    """
    Sends a pre-parsed summary of tracked changes to the LLM for a high-level analysis.
    """
    # Handle cases where extraction found no changes or had an error
    if changes_summary_text.startswith("No tracked insertions or deletions"):
        return "The document analysis indicates that no tracked changes (insertions or deletions) were found to summarize."
    if changes_summary_text.startswith("Error_Internal:"): # Pass through internal errors from word_processor
        return changes_summary_text # e.g., "Error_Internal: Could not open document..."

    prompt = (
        f"You are an expert editor. Below is a summary of tracked changes (insertions and deletions) "
        f"extracted from the Word document named '{filename}'.\n\n"
        "Your task is to provide a concise, high-level textual summary of what these changes "
        "collectively suggest or aim to achieve. For example, are the changes mostly stylistic, "
        "correcting typos, updating specific information (like names, dates, or figures), "
        "rephrasing for clarity, adding new sections, or deleting obsolete content?\n\n"
        "Focus on the overall themes, patterns, or main purposes of the edits as indicated by the provided summary of changes.\n\n"
        "Summary of Tracked Changes:\n"
        "---------------------------\n"
        f"{changes_summary_text}\n"
        "---------------------------\n\n"
        "Please return only your high-level summary of these changes in plain text."
    )
    system_prompt = "You are an AI assistant specialized in summarizing the purpose and themes of tracked changes in a document, based on an input list of those changes."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        response = get_chat_response(messages, temperature=0.0, max_tokens=800) # Max output tokens
        return response
    except Exception as e:
        print(f"An error occurred while calling AI provider for analysis of changes summary: {e}")
        return "Error_AI: The AI service could not provide an analysis for the tracked changes summary at this time."

# --- Function for Approach 2: Analyzing raw document.xml content ---
def get_llm_analysis_from_raw_xml(document_xml_content: str, filename: str) -> Optional[str]:
    """
    Sends the raw word/document.xml content to the LLM for it to find and summarize changes.
    """
    if document_xml_content.startswith("Error_Internal:"): # Pass through internal errors from word_processor
        return document_xml_content

    # Heuristic: if the content is extremely short, it's likely not valid XML or an error occurred
    if len(document_xml_content) < 200: # Arbitrary short length, <w:document> itself is ~100
         print(f"[LLM_HANDLER_DEBUG] Raw XML content for '{filename}' seems too short ({len(document_xml_content)} chars). Passing to LLM but might indicate issue.")
         # Could return "Error_Input: The provided XML content from the document seems too short or invalid to process."

    # Truncate very long XML for the prompt to avoid excessive token usage *in the prompt itself*.
    # The LLM's ability to process very long *inputs* (even if truncated in prompt) depends on its context window.
    MAX_XML_CHARS_IN_PROMPT = 30000  # Approx 7.5k tokens, adjust based on your LLM's limits for the prompt
    xml_for_prompt_display = document_xml_content
    if len(document_xml_content) > MAX_XML_CHARS_IN_PROMPT:
        xml_for_prompt_display = document_xml_content[:MAX_XML_CHARS_IN_PROMPT] + \
                                 f"\n... [XML CONTENT TRUNCATED IN PROMPT - Original length: {len(document_xml_content)} characters] ..."
        print(f"[LLM_HANDLER_DEBUG] Raw XML content for '{filename}' was truncated in the prompt display.")

    prompt = (
        f"You are an AI assistant highly skilled in parsing WordProcessingML XML from Microsoft Word documents.\n"
        f"The following is the content of the 'word/document.xml' file from a .docx document named '{filename}'. "
        f"This XML may be very long and complex.\n\n"
        "--- XML CONTENT START ---\n"
        f"{xml_for_prompt_display}\n" # Use the potentially truncated version for display in prompt
        "--- XML CONTENT END ---\n\n"
        "Please carefully analyze this XML content. Your primary goal is to identify all tracked changes. "
        "Look for <w:ins> (insertion) elements and <w:del> (deletion) elements. For each, try to determine "
        "the inserted text (from <w:t> within <w:ins>) or deleted text (from <w:delText> within <w:del>). "
        "Also, note the 'w:author' and 'w:date' attributes if available for these changes.\n"
        "Based on all the insertions and deletions you can identify from this raw XML, provide a concise, "
        "high-level textual summary of what these changes collectively achieve or suggest. "
        "For example, are they stylistic, correcting typos, updating specific information, etc.?\n\n"
        "If the XML is too complex or seems truncated, and you cannot reliably identify changes, please state that clearly.\n"
        "Return only your high-level summary of these identified changes in plain text."
    )
    system_prompt = "You are an AI assistant that parses raw WordProcessingML XML to find and summarize tracked changes."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        # For raw XML, the LLM might need a larger context window and more output tokens if it tries to quote things.
        response = get_chat_response(messages, temperature=0.0, max_tokens=1000) # Max output tokens
        return response
    except Exception as e:
        print(f"An error occurred while calling AI provider for raw XML analysis: {e}")
        return "Error_AI: The AI service could not provide an analysis from the raw XML at this time."


def get_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> List[Dict]:
    """
    Generate LLM suggestions for document edits.
    
    This function now respects the global LLM configuration settings:
    - If LLM mode is enabled, uses intelligent document analysis
    - If regex mode is enabled, uses the original approach
    """
    
    # Check if we should use intelligent LLM-based processing
    try:
        from .legal_document_processor import USE_LLM_INSTRUCTIONS
        if USE_LLM_INSTRUCTIONS:
            print("🧠 Using intelligent LLM-based instruction processing for manual input")
            return _get_intelligent_llm_suggestions(document_text, user_instructions, filename)
        else:
            print("📝 Using original pattern-based processing for manual input")
            return _get_original_llm_suggestions(document_text, user_instructions, filename)
    except ImportError:
        print("⚠️ Could not import LLM configuration, using original approach")
        return _get_original_llm_suggestions(document_text, user_instructions, filename)

def _get_intelligent_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> List[Dict]:
    """
    Intelligent LLM-based approach that understands document context and user intent
    """
    
    # Truncate document if needed
    max_doc_snippet_len = 7500
    doc_snippet = document_text
    if len(document_text) > max_doc_snippet_len:
        doc_snippet = document_text[:max_doc_snippet_len] + "\n... [DOCUMENT TRUNCATED] ..."
    
    print(f"🧠 Intelligent LLM processing for document '{filename}' ({len(doc_snippet)} chars)")
    print(f"📝 User instructions ({len(user_instructions)} chars): {user_instructions[:200]}{'...' if len(user_instructions) > 200 else ''}")
    print(f"📝 Full user instructions: {user_instructions}")  # Debug: see full instructions
    
    # Enhanced prompt with clear document distinction
    prompt = f"""You are an intelligent document editor. You have analysis instructions derived from a fallback document that specify what changes should be made to the main document.

MAIN DOCUMENT TO EDIT (the document you must find and modify text in):
Document: "{filename}"
Content: {doc_snippet}

ANALYSIS INSTRUCTIONS (derived from fallback document requirements):
{user_instructions}

CRITICAL UNDERSTANDING:
- The ANALYSIS INSTRUCTIONS came from a fallback document (different from main document)
- You must find text that ACTUALLY EXISTS in the MAIN DOCUMENT above
- DO NOT look for text from the fallback document in the main document
- Only suggest changes for text you can actually see in the main document content

YOUR APPROACH:
1. **Read each analysis instruction carefully**
2. **Look ONLY in the main document content** for relevant text to modify
3. **For missing requirements**: Look for the closest related text in the main document to enhance
4. **For existing text**: Find exact matches in the main document to improve

EXAMPLES OF CORRECT ANALYSIS:

❌ WRONG: Looking for fallback document text in main document
Instruction: "Ensure phrase 'ICF and HIPAA Authorization grants Sponsor rights' is present"
Wrong approach: Look for exact fallback text in main document (won't exist)

✅ CORRECT: Find related main document text to enhance
Instruction: "Ensure phrase 'ICF and HIPAA Authorization grants Sponsor rights' is present"  
Correct approach: Look for related ICF/consent language in main document and enhance it

❌ WRONG: Vague text matching
Old Text: "the obligations will continue"

✅ CORRECT: Exact text from main document
Old Text: "The obligations set forth in this Section 5.1"

CRITICAL REQUIREMENTS FOR REPRODUCIBILITY:
1. **EXACT TEXT MATCHING**: Your "specific_old_text" MUST be copied word-for-word from the main document above
2. **NO PARAPHRASING**: Do not rephrase or summarize text - copy it exactly as written
3. **SUFFICIENT LENGTH**: Use text snippets of at least 10-15 words to ensure uniqueness
4. **AVOID VAGUE PHRASES**: Never use short, generic phrases like "the obligations will continue"
5. **COPY-PASTE VERIFICATION**: Mentally copy-paste your "specific_old_text" from the main document

VALIDATION REQUIREMENTS:
- "specific_old_text" must be EXACT text that exists in the main document content above
- Use Ctrl+F mentality: your text should be findable with exact search
- Include enough context to make the match unique (full sentences preferred)
- If you cannot find a substantial, unique text snippet, skip that instruction

PRECISION GUIDELINES:
- ✅ GOOD: "Study Site agrees to conduct this Study in strict accordance with the Protocol"
- ❌ BAD: "the obligations will continue" (too vague)
- ✅ GOOD: "Payment Administrator will administer such funds and shall make all payments to Study Site"
- ❌ BAD: "payment terms" (too generic)

OUTPUT FORMAT:
Return a JSON array of edit objects:
- "contextual_old_text": 50+ character surrounding text from main document
- "specific_old_text": EXACT text from main document (minimum 10 words when possible)
- "specific_new_text": Improved text based on analysis instructions  
- "reason_for_change": Why this change fulfills the analysis instruction

CONSISTENCY ENFORCEMENT:
- Generate the SAME suggestions each time for the same document
- Use deterministic text selection (choose the longest, most specific match)
- Prioritize full sentences over partial phrases

Example: [{{"contextual_old_text": "longer surrounding text from main doc for context", "specific_old_text": "exact complete sentence or substantial phrase from main doc", "specific_new_text": "improved text", "reason_for_change": "fulfills instruction X"}}]

If no exact substantial text matches can be found, return: []
"""

    messages = [{"role": "user", "content": prompt}]
    
    try:
        content = get_chat_response(messages, temperature=0.0, seed=42, response_format={"type": "json_object"})
        if not content:
            print("❌ LLM returned empty content for intelligent suggestions")
            return []
        
        print("✅ Intelligent LLM response received")
        print(f"📊 Response length: {len(content)} characters")
        
        # Parse the response
        edits = _parse_llm_response(content)
        print(f"🎯 Generated {len(edits)} intelligent suggestions")
        
        # Enhanced debugging: Show all suggestions before validation
        print("\n" + "="*80)
        print("📋 DETAILED LLM SUGGESTIONS ANALYSIS")
        print("="*80)
        for i, edit in enumerate(edits, 1):
            print(f"\n📝 SUGGESTION {i}:")
            print(f"   Context: {edit.get('contextual_old_text', 'N/A')[:100]}...")
            print(f"   Old Text: '{edit.get('specific_old_text', 'N/A')}'")
            print(f"   New Text: '{edit.get('specific_new_text', 'N/A')[:100]}{'...' if len(str(edit.get('specific_new_text', ''))) > 100 else ''}'")
            print(f"   Reason: {edit.get('reason_for_change', 'N/A')}")
        print("="*80)
        
        validated_edits = _validate_edits(edits)
        
        if len(validated_edits) != len(edits):
            print(f"⚠️  VALIDATION: {len(edits)} suggestions → {len(validated_edits)} valid (dropped {len(edits) - len(validated_edits)})")
        
        return validated_edits
        
    except Exception as e:
        print(f"❌ Error in intelligent LLM processing: {e}")
        print("🔄 Falling back to original approach...")
        return _get_original_llm_suggestions(document_text, user_instructions, filename)

def _validate_edits(edits: List[Dict]) -> List[Dict]:
    """
    Validate edit suggestions to ensure they have required fields and proper types
    """
    valid_edits = []
    required_keys = {"contextual_old_text", "specific_old_text", "reason_for_change"}
    
    print("\n🔍 VALIDATION RESULTS:")
    for i, edit_item in enumerate(edits, 1):
        if isinstance(edit_item, dict) and required_keys.issubset(edit_item.keys()):
            if all(isinstance(edit_item.get(key), str) for key in ["contextual_old_text", "specific_old_text", "reason_for_change"]) and \
               (edit_item.get("specific_new_text") is None or isinstance(edit_item.get("specific_new_text"), str)):
                valid_edits.append(edit_item)
                print(f"   ✅ Edit {i}: VALID - '{edit_item.get('specific_old_text', 'N/A')[:50]}{'...' if len(str(edit_item.get('specific_old_text', ''))) > 50 else ''}'")
            else:
                print(f"   ❌ Edit {i}: INVALID DATA TYPES - {edit_item.get('specific_old_text', 'N/A')[:50]}")
        else:
            print(f"   ❌ Edit {i}: MISSING KEYS - Required: {required_keys}")
    
    print(f"📊 VALIDATION SUMMARY: {len(valid_edits)}/{len(edits)} edits passed validation\n")
    return valid_edits

def _get_original_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> List[Dict]:
    """
    Original approach - detailed prompting with strict pattern matching
    """
    max_doc_snippet_len = 7500 
    doc_snippet = document_text
    if len(document_text) > max_doc_snippet_len:
        doc_snippet = document_text[:max_doc_snippet_len] + "\n... [DOCUMENT TRUNCATED] ..."
    print("\n[LLM_HANDLER_DEBUG] Document snippet being sent to LLM for suggestions:")
    print(doc_snippet[:1000] + "..." if len(doc_snippet) > 1000 else doc_snippet)
    print(f"(Total snippet length: {len(doc_snippet)})")
    print("[LLM_HANDLER_DEBUG] End of document snippet for suggestions.\n")
    
    print("\n[LLM_HANDLER_DEBUG] User instructions being sent to LLM:")
    print("=" * 50)
    print(user_instructions[:800] + "..." if len(user_instructions) > 800 else user_instructions)
    print("=" * 50)
    print(f"(Total instructions length: {len(user_instructions)})")
    
    # Quick check for our key phrases
    if "You MUST generate" in user_instructions:
        print("✅ FOUND: Simplified direct instructions detected")
    elif "CRITICAL: You must make MULTIPLE" in user_instructions:
        print("✅ FOUND: Alternative simplified instructions detected")
    elif "requirements found" in user_instructions.lower():
        print("❌ ERROR: Getting error message instead of requirements")
    else:
        print("❓ UNKNOWN: Instruction format not recognized")
    
    print("[LLM_HANDLER_DEBUG] End of user instructions.\n")
    prompt = f"""You are an AI assistant that suggests specific textual changes for a Word document based on user instructions.
Your goal is to identify the exact text to be replaced (`specific_old_text`), provide enough surrounding text for unique identification in the document (`contextual_old_text`), the new text (`specific_new_text`), and a reason for the change.
**CRITICAL: The user's instructions contain MULTIPLE separate requirements. You are REQUIRED to generate MULTIPLE separate edits - one for each requirement. Do NOT combine requirements into a single edit. Do NOT generate only one edit when multiple are requested. You MUST provide separate JSON objects for EACH requirement listed.**
User instructions for changes: {user_instructions}
**Critical Instructions for Defining `specific_old_text`:**
1.  **Target Complete Semantic Units:**
    * You *must* ensure `specific_old_text` represents the entire, complete semantic unit in the document that needs changing.
    * **Numbers and Currency:** If a numerical value like "USD150.25" or "75%" needs modification, `specific_old_text` must be the *entire value* (e.g., "USD150.25", not just "150"; "75%", not just "75"). If the document says "cost is $101" and the intent is to change this amount, `specific_old_text` must be "$101". Do *not* suggest changing only a part like "$10" if it's found within a larger number like "$101".
    * **Words and Proper Nouns:** `specific_old_text` must capture the whole word or relevant multi-word proper noun/phrase. For example, if changing "inter-disciplinary approach", `specific_old_text` should be "inter-disciplinary approach". Avoid partial word selections like "disciplinary" from "inter-disciplinary".
2.  **Boundary Adherence for `specific_old_text`:**
    * The processing script will verify that your chosen `specific_old_text`, when found in the document, is appropriately bounded. This means:
        * The character immediately *before* your `specific_old_text` in the document should be whitespace (space, tab, etc.) or it should be the beginning of a paragraph.
        * The character immediately *after* your `specific_old_text` in the document should be whitespace, or one of the following punctuation marks: comma (,), period (.), semicolon (;), or it should be the end of a paragraph.
    * **Your primary task is to select the correct full token that also meets these boundary conditions in the original text.** For instance, if `specific_old_text` is "item" and the document text is "item.", this selection is valid. If `specific_old_text` is "item" and the document text is "items", this selection is invalid because "s" is not an allowed boundary character.
3.  **Examples of Correct `specific_old_text` Identification:**
    * Document Text: "...the initial fee was EUR75.50 and..."
        LLM Goal: Change the fee to EUR90.
        Correct `specific_old_text`: "EUR75.50"
    * Document Text: "...for all client-focused initiatives..."
        LLM Goal: Change "client-focused" to "customer-centric".
        Correct `specific_old_text`: "client-focused"
    * Document Text: "The item, a widget, was blue."
        LLM Goal: Change "widget" to "gadget".
        Correct `specific_old_text`: "widget"
**Output Format Instructions:**
Return your suggestions *only* as a valid JSON structure. This structure **MUST be a flat JSON array of objects**, where each object has the keys: "contextual_old_text", "specific_old_text", "specific_new_text", "reason_for_change".
Example of correct flat array: `[ {{"contextual_old_text": "...", "specific_old_text": "...", "specific_new_text": "...", "reason_for_change": "..."}}, {{"contextual_old_text": "...", "specific_old_text": "...", "specific_new_text": "...", "reason_for_change": "..."}} ]`
If only one change is suggested, you **MUST still return it as an array with one object**: `[ {{"contextual_old_text": "...", "specific_old_text": "...", "specific_new_text": "...", "reason_for_change": "..."}} ]`
If no changes are needed based on the user instructions and the document, or if no changes can be identified that meet all the above criteria, return an empty JSON list: `[]`.
**DO NOT return a list containing another list, a single JSON object that is not an array, or a list containing null values. The top-level response MUST be a JSON array `[...]`.**
Document (`{filename}`), snippet if long:
{doc_snippet}
"""
    messages = [{"role": "user", "content": prompt}]
    content: Optional[str] = None
    try:
        content = get_chat_response(messages, temperature=0.0, response_format={"type": "json_object"})
        if not content:
            print("LLM returned empty content for suggestions.")
            return [] 
        
        print("\n[LLM_HANDLER_DEBUG] RAW LLM RESPONSE:")
        print("=" * 60)
        print(content[:2000] + "..." if len(content) > 2000 else content)
        print("=" * 60)
        print("[LLM_HANDLER_DEBUG] End of raw LLM response.\n")
        
    except Exception as e:
        print(f"LLM call for suggestions failed: {e}")
        return [] 
    edits: List[Dict] = []
    try:
        edits = _parse_llm_response(content) 
    except Exception as e_parse:
        print(f"Critical error during _parse_llm_response after LLM call: {e_parse}")
        print(f"Content given to _parse_llm_response (snippet): {content[:500] if content else 'None'}")
        return []
    
    return _validate_edits(edits)

def _parse_llm_response(content: str) -> List[Dict]:
    # ... (keep existing _parse_llm_response) ...
    if not content or not content.strip():
        print("LLM response content is empty.")
        return []
    json_str_to_parse: Optional[str] = None
    try:
        json_array_match = re.search(r'\[.*\]', content, re.DOTALL | re.MULTILINE)
        json_object_match = re.search(r'\{.*\}', content, re.DOTALL | re.MULTILINE)
        if json_array_match: json_str_to_parse = json_array_match.group(0)
        elif json_object_match: json_str_to_parse = json_object_match.group(0)
        if not json_str_to_parse:
            if content.strip().startswith(('[', '{')) and content.strip().endswith((']', '}')):
                json_str_to_parse = content.strip()
            else:
                print(f"Could not find a clear JSON array or object structure in LLM response. Content: {content[:500]}")
                return []
        data: Any = json.loads(json_str_to_parse)
        if isinstance(data, list):
            if data and isinstance(data[0], list):
                potential_edits = [item for item in data[0] if isinstance(item, dict)]
                if potential_edits:
                    print(f"LLM returned a nested list; extracted {len(potential_edits)} edits from the inner list.")
                    return potential_edits
                else:
                    print("LLM returned a nested list, but the inner list was empty or had no dictionaries.")
                    return []
            elif all(isinstance(item, dict) for item in data): return data
            else:
                print(f"LLM returned a list, but not all items are dictionaries, nor is it a list of a list of dictionaries: {str(data)[:300]}")
                return []
        elif isinstance(data, dict):
            required_keys = {"contextual_old_text", "specific_old_text", "reason_for_change"}
            if required_keys.issubset(data.keys()): return [data] 
            for key in data:
                if isinstance(data[key], list):
                    if all(isinstance(item, dict) for item in data[key]): return data[key]
            print(f"LLM response was a dict, but not a single edit and no list of edits found within it: {str(data)[:300]}")
            return []
        else:
            print(f"LLM response could not be parsed into a list or dictionary of edits. Parsed data type: {type(data)}")
            return []
    except json.JSONDecodeError as exc:
        parsed_str_snippet = json_str_to_parse[:500] if json_str_to_parse else "N/A (json_str_to_parse was None)"
        print(f"Could not decode JSON from LLM response. Error: {exc}\nString attempted to parse: '{parsed_str_snippet}...' \nOriginal content snippet: '{content[:500]}...'")
    except Exception as e:
        print(f"An unexpected error occurred during LLM response parsing: {type(e).__name__}: {e}\nContent snippet: {content[:500]}")
    return []


if __name__ == "__main__":
    # ... (keep existing __main__ block for testing if desired) ...
    sample_doc_text = (
        "This document outlines the project plan. The deadline for Phase 1 is 2024-07-15. "
        "The primary contact is Mr. Smitherson. Budget allocation is $10100. " 
        "We need to ensure quality control throughout the process. The final report is due on 2024-09-30."
        "Also, the old policy reference X123 needs updating."
        "The cost would be $101 , to a new number."
        "MrArbor is the author. Bob and another Bob are here."
    )
    user_instructions_test = (
        "Change Mr. Smitherson to Ms. Jones. Update the budget from $10100 to $12000. "
        "The deadline for Phase 1 should be 2024-08-01. Ensure 'quality control' is changed to 'quality assurance'. "
        "Replace policy X123 with Y456."
        "Change $101 to $208. Change MrArbor to MrSage. Change all Bob to Robert."
    )
    print("Requesting LLM suggestions (simulated - actual call commented out for safety)...")
    print("\n--- Testing _parse_llm_response with problematic input ---")
    problematic_llm_content = """
    ```json
    [
      [
        {
          "contextual_old_text": "the cost would be $101",
          "specific_old_text": "$101",
          "specific_new_text": "$208",
          "reason_for_change": "The cost should be at least $208."
        },
        {
          "contextual_old_text": "last edited by MrArbor",
          "specific_old_text": "MrArbor",
          "specific_new_text": "MrSage",
          "reason_for_change": "Change MrArbor to MrSage."
        }
      ], null, [ {"contextual_old_text": "another item", "specific_old_text": "item", "specific_new_text": "thing", "reason_for_change": "just because"} ]
    ]
    ```
    """
    parsed_problematic = _parse_llm_response(problematic_llm_content)
    print("Parsed problematic content:")
    print(json.dumps(parsed_problematic, indent=2) if parsed_problematic else "Failed to parse problematic content or got empty list.")
    print("\n--- Testing _parse_llm_response with a good flat list ---")
    good_llm_content = """
    ```json
    [ {"contextual_old_text": "the cost would be $101", "specific_old_text": "$101", "specific_new_text": "$208", "reason_for_change": "The cost should be at least $208."} ]
    ```
    """
    parsed_good = _parse_llm_response(good_llm_content)
    print("Parsed good content:")
    print(json.dumps(parsed_good, indent=2) if parsed_good else "Failed to parse good content.")
    print("\nNote: Actual LLM call is commented out in __main__ to prevent unintended API calls during simple script run.")