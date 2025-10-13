#!/usr/bin/env python3
import copy
import datetime
import re
import json
import os # Added for path manipulation
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from typing import List, Dict, Tuple, Optional # For type hinting

# --- Global Configuration Flags ---
DEBUG_MODE = False
CASE_SENSITIVE_SEARCH = True
ADD_COMMENTS_TO_CHANGES = True
DEFAULT_AUTHOR_NAME = "LLM Editor"

# --- Constants ---
ERROR_LOG_FILENAME_BASE = "change_log"

# --- XML Helper Functions (largely unchanged) ---
def create_del_element(author="Python Program", date_time=None, del_id="0"): # id is managed by Word on load
    if date_time is None:
        date_time = datetime.datetime.now(datetime.timezone.utc)
    del_el = OxmlElement('w:del')
    del_el.set(qn('w:author'), author)
    # del_el.set(qn('w:id'), str(del_id)) # Word will manage IDs
    del_el.set(qn('w:date'), date_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return del_el

def create_ins_element(author="Python Program", date_time=None, ins_id="0"): # id is managed by Word on load
    if date_time is None:
        date_time = datetime.datetime.now(datetime.timezone.utc)
    ins_el = OxmlElement('w:ins')
    ins_el.set(qn('w:author'), author)
    # ins_el.set(qn('w:id'), str(ins_id)) # Word will manage IDs
    ins_el.set(qn('w:date'), date_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return ins_el

def create_run_element_with_text(text_content, template_run_r=None, is_del_text=False):
    new_r = OxmlElement('w:r')
    if template_run_r is not None:
        rPr = template_run_r.find(qn('w:rPr'))
        if rPr is not None:
            new_r.append(copy.deepcopy(rPr))
    text_element_tag = 'w:delText' if is_del_text else 'w:t'
    text_el = OxmlElement(text_element_tag)
    text_el.set(qn('xml:space'), 'preserve')
    text_el.text = text_content
    new_r.append(text_el)
    return new_r

def log_debug(message):
    if DEBUG_MODE:
        print(f"DEBUG (word_processor): {message}")

def _get_element_style_template_run(element_info_item, fallback_style_run):
    """Helper to get a w:r for styling, from the element itself or its first w:r child."""
    if element_info_item['el'].tag == qn('w:r'):
        return element_info_item['el']
    # For w:ins or w:hyperlink, try to find a child w:r to get style
    r_child = element_info_item['el'].find(qn('w:r'))
    if r_child is not None:
        return r_child
    return fallback_style_run


def replace_text_in_paragraph_with_tracked_change(
        paragraph_idx, paragraph,
        contextual_old_text, specific_old_text, specific_new_text, reason_for_change,
        author, case_sensitive_flag, add_comments_flag, ambiguous_or_failed_changes_log):
    log_debug(f"P{paragraph_idx+1}: Attempting to change '{specific_old_text}' to '{specific_new_text}' within context '{contextual_old_text[:30]}...'")

    elements_contributing_to_visible_text = []
    current_text_offset = 0
    for p_child_idx, p_child_element in enumerate(paragraph._p):
        text_contribution = ""
        element_type = "other" # 'r', 'ins', 'hyperlink'

        if p_child_element.tag == qn("w:r"):
            element_type = "r"
            if p_child_element.find(qn('w:delText')) is None:
                for t_node in p_child_element.findall(qn('w:t')):
                    if t_node.text: text_contribution += t_node.text
                if p_child_element.find(qn('w:tab')) is not None: text_contribution += '\t'
        elif p_child_element.tag == qn("w:ins"):
            element_type = "ins"
            for r_in_ins in p_child_element.findall(qn('w:r')):
                if r_in_ins.find(qn('w:delText')) is None: # Should not happen in a well-formed w:ins text
                    for t_in_ins in r_in_ins.findall(qn('w:t')):
                        if t_in_ins.text: text_contribution += t_in_ins.text
                    if r_in_ins.find(qn('w:tab')) is not None: text_contribution += '\t'
        elif p_child_element.tag == qn("w:hyperlink"):
            element_type = "hyperlink"
            for r_in_hyperlink in p_child_element.findall(qn('w:r')):
                if r_in_hyperlink.find(qn('w:delText')) is None:
                    for t_in_hyperlink in r_in_hyperlink.findall(qn('w:t')):
                        if t_in_hyperlink.text: text_contribution += t_in_hyperlink.text
                    if r_in_hyperlink.find(qn('w:tab')) is not None: text_contribution += '\t'
        
        if text_contribution:
            elements_contributing_to_visible_text.append({
                'el': p_child_element, 
                'text': text_contribution, 
                'p_child_idx': p_child_idx, # Index in paragraph._p
                'doc_start_offset': current_text_offset, # Start offset in visible_paragraph_text
                'type': element_type,
                'original_author': p_child_element.get(qn('w:author')) if element_type == "ins" else None,
                'original_date': p_child_element.get(qn('w:date')) if element_type == "ins" else None
            })
            current_text_offset += len(text_contribution)
    
    visible_paragraph_text_original_case = "".join(item['text'] for item in elements_contributing_to_visible_text)
    search_text_in_doc = visible_paragraph_text_original_case if case_sensitive_flag else visible_paragraph_text_original_case.lower()
    search_context_from_llm = contextual_old_text if case_sensitive_flag else contextual_old_text.lower()

    log_debug(f"P{paragraph_idx+1}: Visible text (len {len(visible_paragraph_text_original_case)}): '{visible_paragraph_text_original_case[:100]}{'...' if len(visible_paragraph_text_original_case)>100 else ''}'")

    occurrences = []
    try:
        for match in re.finditer(re.escape(search_context_from_llm), search_text_in_doc):
            occurrences.append(match)
    except re.error as e:
        # (Error logging for regex error - unchanged)
        log_message = f"P{paragraph_idx+1}: Regex error searching for context '{search_context_from_llm[:50]}...': {e}. Skipping. LLM Reason: {reason_for_change}"
        log_debug(log_message)
        ambiguous_or_failed_changes_log.append({
            "paragraph_index": paragraph_idx + 1, "visible_text_snippet": visible_paragraph_text_original_case[:100],
            "contextual_old_text": contextual_old_text, "specific_old_text": specific_old_text,
            "llm_reason": reason_for_change, "issue": f"Regex error: {e}"})
        return "REGEX_ERROR_IN_CONTEXT_SEARCH"

    if not occurrences:
        return "CONTEXT_NOT_FOUND"
    if len(occurrences) > 1:
        # (Error logging for ambiguous context - unchanged)
        log_message = (f"P{paragraph_idx+1}: Context '{contextual_old_text[:50]}...' is AMBIGUOUS. Found {len(occurrences)} times. "
                       f"Skipping change of '{specific_old_text}' to '{specific_new_text}'. LLM Reason: {reason_for_change}")
        log_debug(log_message)
        ambiguous_or_failed_changes_log.append({
            "paragraph_index": paragraph_idx + 1, "visible_text_snippet": visible_paragraph_text_original_case[:100],
            "contextual_old_text": contextual_old_text, "specific_old_text": specific_old_text,
            "specific_new_text": specific_new_text, "llm_reason": reason_for_change,
            "issue": f"Ambiguous context: Found {len(occurrences)} occurrences."})
        return "CONTEXT_AMBIGUOUS"

    match_context = occurrences[0]
    actual_context_found_in_doc = visible_paragraph_text_original_case[match_context.start() : match_context.end()]
    text_to_search_within_context = actual_context_found_in_doc if case_sensitive_flag else actual_context_found_in_doc.lower()
    specific_text_to_find_in_context = specific_old_text if case_sensitive_flag else specific_old_text.lower()

    try:
        specific_start_in_context = text_to_search_within_context.index(specific_text_to_find_in_context)
    except ValueError:
        # (Error logging for specific text not in context - unchanged)
        log_message = (f"P{paragraph_idx+1}: Specific text '{specific_old_text}' NOT FOUND within the identified unique context '{actual_context_found_in_doc}'. "
                       f"Skipping. LLM Reason: {reason_for_change}")
        log_debug(log_message)
        ambiguous_or_failed_changes_log.append({
            "paragraph_index": paragraph_idx + 1, "visible_text_snippet": visible_paragraph_text_original_case[:100],
            "contextual_old_text": contextual_old_text, "specific_old_text": specific_old_text,
            "specific_new_text": specific_new_text, "llm_reason": reason_for_change,
            "issue": "Specific text not found within unique context." })
        return "SPECIFIC_TEXT_NOT_IN_CONTEXT"
    
    actual_specific_old_text_to_delete = actual_context_found_in_doc[specific_start_in_context : specific_start_in_context + len(specific_old_text)]
    global_specific_start_offset = match_context.start() + specific_start_in_context
    global_specific_end_offset = global_specific_start_offset + len(actual_specific_old_text_to_delete)
    
    log_debug(f"P{paragraph_idx+1}: Unique context found. Specific text '{actual_specific_old_text_to_delete}' (len {len(actual_specific_old_text_to_delete)}) located for replacement with '{specific_new_text}'. Global offsets: {global_specific_start_offset}-{global_specific_end_offset}")

    # Identify all paragraph child elements (p_child_idx) involved in the specific text
    involved_element_infos = []
    first_involved_r_element_for_style = None

    for item in elements_contributing_to_visible_text:
        item_doc_end_offset = item['doc_start_offset'] + len(item['text'])
        # Check for overlap: max(start1, start2) < min(end1, end2)
        if max(item['doc_start_offset'], global_specific_start_offset) < min(item_doc_end_offset, global_specific_end_offset):
            involved_element_infos.append(item)
            if first_involved_r_element_for_style is None:
                if item['el'].tag == qn('w:r'):
                    first_involved_r_element_for_style = item['el']
                elif item['el'].tag in [qn('w:ins'), qn('w:hyperlink')]:
                    r_child = item['el'].find(qn('w:r'))
                    if r_child is not None: first_involved_r_element_for_style = r_child
    
    if not involved_element_infos:
        log_message = f"P{paragraph_idx+1}: XML_MAPPING_FAILED - Could not map specific text '{actual_specific_old_text_to_delete}' to XML elements. LLM Reason: {reason_for_change}"
        log_debug(log_message)
        ambiguous_or_failed_changes_log.append({
            "paragraph_index": paragraph_idx + 1, "issue": "XML mapping failed for specific text.", 
            "contextual_old_text": contextual_old_text, "specific_old_text": actual_specific_old_text_to_delete, 
            "llm_reason": reason_for_change, "visible_text_snippet": visible_paragraph_text_original_case[:100]
        })
        return "XML_MAPPING_FAILED"

    if first_involved_r_element_for_style is None: # Should ideally have found one
        first_involved_r_element_for_style = OxmlElement('w:r') # Create a default plain run for style
        log_debug(f"P{paragraph_idx+1}: WARNING - No template <w:r> found for styling. Using default.")


    # ----- MODIFIED LOGIC STARTS HERE (Replaces PARTIAL_MATCH_COMPLEX block) -----
    log_debug(f"P{paragraph_idx+1}: Modifying {len(involved_element_infos)} raw XML elements for the change.")

    new_xml_elements_for_paragraph = []
    
    # 1. Handle the first involved element (might have a prefix)
    first_item = involved_element_infos[0]
    # Text in this element before the part to be deleted starts
    prefix_len_in_first_item = global_specific_start_offset - first_item['doc_start_offset']
    if prefix_len_in_first_item < 0: prefix_len_in_first_item = 0 # Should not happen if logic is correct
    
    prefix_text = first_item['text'][:prefix_len_in_first_item]

    if prefix_text:
        style_run = _get_element_style_template_run(first_item, first_involved_r_element_for_style)
        if first_item['type'] == 'ins': # Preserve original insertion for prefix
            orig_ins = create_ins_element(author=first_item['original_author'], date_time=None) # Date will be parsed if needed or new date
            if first_item['original_date']: orig_ins.set(qn('w:date'), first_item['original_date'])
            orig_ins.append(create_run_element_with_text(prefix_text, style_run))
            new_xml_elements_for_paragraph.append(orig_ins)
        else: # For 'r', 'hyperlink' (hyperlink content will become plain text runs after this change)
            new_xml_elements_for_paragraph.append(create_run_element_with_text(prefix_text, style_run))
        log_debug(f"P{paragraph_idx+1}: Added prefix '{prefix_text}' from first element (type: {first_item['type']}).")

    # 2. Add the DEL and INS elements for the main change
    change_time = datetime.datetime.now(datetime.timezone.utc)
    del_obj = create_del_element(author=author, date_time=change_time)
    del_obj.append(create_run_element_with_text(actual_specific_old_text_to_delete, first_involved_r_element_for_style, is_del_text=True))
    new_xml_elements_for_paragraph.append(del_obj)
    log_debug(f"P{paragraph_idx+1}: Added <w:del> for '{actual_specific_old_text_to_delete}'.")

    if specific_new_text:
        ins_obj = create_ins_element(author=author, date_time=change_time + datetime.timedelta(seconds=1)) # Ensure ins is later
        ins_obj.append(create_run_element_with_text(specific_new_text, first_involved_r_element_for_style))
        new_xml_elements_for_paragraph.append(ins_obj)
        log_debug(f"P{paragraph_idx+1}: Added <w:ins> for '{specific_new_text}'.")

    # 3. Handle the last involved element (might have a suffix)
    last_item = involved_element_infos[-1]
    # Start of suffix in this element's text. global_specific_end_offset is end of delete_text in doc.
    # last_item['doc_start_offset'] is start of last_item's text in doc.
    suffix_start_in_last_item = global_specific_end_offset - last_item['doc_start_offset']
    
    suffix_text = ""
    if suffix_start_in_last_item < len(last_item['text']):
        suffix_text = last_item['text'][suffix_start_in_last_item:]

    if suffix_text:
        style_run = _get_element_style_template_run(last_item, first_involved_r_element_for_style)
        if last_item['type'] == 'ins': # Preserve original insertion for suffix
            orig_ins = create_ins_element(author=last_item['original_author'], date_time=None)
            if last_item['original_date']: orig_ins.set(qn('w:date'), last_item['original_date'])
            orig_ins.append(create_run_element_with_text(suffix_text, style_run))
            new_xml_elements_for_paragraph.append(orig_ins)
        else: # For 'r', 'hyperlink'
            new_xml_elements_for_paragraph.append(create_run_element_with_text(suffix_text, style_run))
        log_debug(f"P{paragraph_idx+1}: Added suffix '{suffix_text}' from last element (type: {last_item['type']}).")

    # 4. Replace the original involved child elements with the new sequence
    p_child_indices_to_remove = sorted(list(set(item['p_child_idx'] for item in involved_element_infos)), reverse=True)
    
    insertion_point_xml = p_child_indices_to_remove[-1] # Index in paragraph._p to insert before

    for p_idx_to_remove in p_child_indices_to_remove:
        try:
            el_to_remove = paragraph._p[p_idx_to_remove]
            paragraph._p.remove(el_to_remove)
            log_debug(f"P{paragraph_idx+1}: Removed original XML element at p_child_idx {p_idx_to_remove}.")
        except IndexError:
            log_message = f"P{paragraph_idx+1}: Error removing XML element at index {p_idx_to_remove}. Change aborted. LLM Reason: {reason_for_change}"
            log_debug(log_message)
            ambiguous_or_failed_changes_log.append({
                "paragraph_index": paragraph_idx + 1, "issue": f"XML element removal error at index {p_idx_to_remove}.",
                "contextual_old_text": contextual_old_text, "specific_old_text": actual_specific_old_text_to_delete,
                "llm_reason": reason_for_change
            })
            return "XML_REMOVAL_ERROR" # This change cannot be completed safely

    # Insert the newly constructed elements
    for i, new_el in enumerate(new_xml_elements_for_paragraph):
        paragraph._p.insert(insertion_point_xml + i, new_el)
    log_debug(f"P{paragraph_idx+1}: Inserted {len(new_xml_elements_for_paragraph)} new XML elements.")

    # ----- MODIFIED LOGIC ENDS HERE -----

    # Add comment (largely unchanged, but ensure it's robust)
    if add_comments_flag and reason_for_change:
        comment_text_to_add = reason_for_change
        if not specific_new_text: # Deletion only
            comment_text_to_add = f"Deleted: '{actual_specific_old_text_to_delete}'. Reason: {reason_for_change}"
        
        try:
            comment_author_name = f"{author} (LLM)"
            name_parts = [word for word in comment_author_name.replace("(", "").replace(")", "").split() if word]
            comment_initials = (name_parts[0][0] + name_parts[1][0]).upper() if len(name_parts) >= 2 else (name_parts[0][:2].upper() if name_parts else "LS")
            
            paragraph.add_comment(comment_text_to_add, author=comment_author_name, initials=comment_initials)
            log_debug(f"P{paragraph_idx+1}: Added comment: '{comment_text_to_add[:30]}...'.")
        except Exception as e:
            log_debug(f"P{paragraph_idx+1}: WARNING - Could not add comment. Error: {e}")
            ambiguous_or_failed_changes_log.append({
                "paragraph_index": paragraph_idx + 1, "issue": f"Comment addition failed: {e}",
                "contextual_old_text": contextual_old_text, "specific_old_text": actual_specific_old_text_to_delete,
                "specific_new_text": specific_new_text, "llm_reason": reason_for_change, "type": "Warning"})

    return "SUCCESS"

# The rest of the script (process_document_with_edits, __main__, etc.) remains unchanged.
# Make sure to integrate this modified replace_text_in_paragraph_with_tracked_change function
# and the new helper _get_element_style_template_run.
# Also, note the removal of w:id from create_del_element and create_ins_element, 
# as Word handles these IDs dynamically on load to ensure uniqueness.


def process_document_with_edits(
    input_docx_path: str,
    output_docx_path: str,
    edits_to_make: List[Dict],
    author_name: str = DEFAULT_AUTHOR_NAME,
    debug_mode_flag: bool = False,
    case_sensitive_flag: bool = True,
    add_comments_flag: bool = True
) -> Tuple[bool, Optional[str], List[Dict]]:
    """
    Main processing function, adapted from the original main().
    Takes input/output paths and edits as a list of dicts.
    Returns a tuple: (success_status, error_log_file_path_or_None, ambiguous_or_failed_changes_log_list)
    """
    global DEBUG_MODE, CASE_SENSITIVE_SEARCH, ADD_COMMENTS_TO_CHANGES
    DEBUG_MODE = debug_mode_flag
    CASE_SENSITIVE_SEARCH = case_sensitive_flag
    ADD_COMMENTS_TO_CHANGES = add_comments_flag

    log_debug(f"Script starting. Input: {input_docx_path}, Output: {output_docx_path}")
    log_debug(f"Debug: {DEBUG_MODE}, CaseSensitive: {CASE_SENSITIVE_SEARCH}, AddComments: {ADD_COMMENTS_TO_CHANGES}")
    log_debug(f"Author for changes: {author_name}")
    log_debug(f"Number of edits to attempt: {len(edits_to_make)}")

    if not isinstance(edits_to_make, list) or not all(isinstance(item, dict) for item in edits_to_make):
        log_debug("FATAL: Edits must be a list of dictionaries.")
        return False, None, [{"issue": "FATAL: Edits must be a list of dictionaries."}]

    ambiguous_or_failed_changes_log = []
    try:
        doc = Document(input_docx_path)
        log_debug(f"Successfully opened Word document: '{input_docx_path}'")
    except Exception as e:
        log_debug(f"FATAL: Error opening Word document '{input_docx_path}': {e}")
        return False, None, [{"issue": f"FATAL: Error opening Word document '{input_docx_path}': {e}"}]

    # Enable track changes if not already enabled (optional, but good practice)
    # settings = doc.settings
    # settings.track_revisions = True # docx.settings does not have track_revisions
    # Forcing track changes on requires deeper oxml manipulation if not already on.
    # We assume the document is already set to show tracked changes for these to be visible.

    for para_idx, paragraph in enumerate(doc.paragraphs):
        log_debug(f"\n--- Processing Paragraph {para_idx+1} ---")
        # It's important to process edits sequentially for a paragraph if text changes affect context
        # For now, we iterate through all given edits for each paragraph.
        # A more robust approach might re-evaluate paragraph text after each successful change within it.
        for edit_item_idx, edit_item in enumerate(list(edits_to_make)): # Iterate a copy if you modify list
            log_debug(f"Attempting edit item {edit_item_idx+1} in P{para_idx+1}")
            required_keys = ["contextual_old_text", "specific_old_text", "reason_for_change"] # specific_new_text can be ""
            if not all(key in edit_item for key in required_keys):
                log_message = f"P{para_idx+1}, EditItem{edit_item_idx+1}: Invalid edit item structure (missing keys): {edit_item}. Skipping this item."
                log_debug(log_message)
                ambiguous_or_failed_changes_log.append({
                    "paragraph_index": para_idx + 1, 
                    "edit_item_index": edit_item_idx +1,
                    "issue": "Invalid edit item structure.", 
                    "edit_item_snippet": str(edit_item)[:100]
                })
                continue

            specific_new_text = edit_item.get("specific_new_text", "") # Default to empty for deletions

            status = replace_text_in_paragraph_with_tracked_change(
                para_idx, paragraph,
                edit_item["contextual_old_text"],
                edit_item["specific_old_text"],
                specific_new_text,
                edit_item["reason_for_change"],
                author_name,
                CASE_SENSITIVE_SEARCH,
                ADD_COMMENTS_TO_CHANGES,
                ambiguous_or_failed_changes_log
            )
            if status == "SUCCESS":
                success_msg = f"SUCCESS: P{para_idx+1}: Applied change for context '{edit_item['contextual_old_text'][:30]}...'. Reason: {edit_item['reason_for_change']}"
                print(success_msg) 
                log_debug(success_msg)
                # If a change is made, the paragraph's XML is altered.
                # For subsequent edits in the SAME paragraph, the text and element indices might have shifted.
                # The current loop continues, but this could lead to issues if contexts overlap or shift.
                # A safer way would be to re-fetch/re-analyze paragraph text here if multiple edits per paragraph are common.
                # For now, we assume edits are distinct enough or this re-analysis is handled by caller.
                break # IMPORTANT: After a successful change, the paragraph's structure is modified.
                      # Re-processing the same paragraph with further edits from the list without
                      # re-evaluating the paragraph's new state is risky.
                      # Breaking here means only one successful edit per paragraph pass.
                      # If multiple independent edits are needed for one paragraph, the input `edits_to_make`
                      # should ideally be processed in a way that one call to this function handles one distinct edit,
                      # or this function needs to rebuild `elements_contributing_to_visible_text` after each SUCCESS.
                      # For now, breaking ensures stability for the modified element replacement logic.

            elif status not in ["CONTEXT_NOT_FOUND", "REGEX_ERROR_IN_CONTEXT_SEARCH"]: 
                info_msg = f"INFO: P{para_idx+1}: Edit for context '{edit_item['contextual_old_text'][:30]}...' resulted in status: {status}."
                print(info_msg)
                log_debug(info_msg)
    try:
        doc.save(output_docx_path)
        print(f"\nProcessed document saved to '{output_docx_path}'")
        log_debug(f"Processed document saved to '{output_docx_path}'")
    except Exception as e:
        log_debug(f"FATAL: Error saving document to '{output_docx_path}': {e}")
        ambiguous_or_failed_changes_log.append({"issue": f"FATAL: Error saving document to '{output_docx_path}': {e}"})
        return False, None, ambiguous_or_failed_changes_log

    error_log_file_path = None
    if ambiguous_or_failed_changes_log:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename_with_ts = f"{ERROR_LOG_FILENAME_BASE}_{timestamp}.txt"
        
        output_dir = os.path.dirname(output_docx_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        error_log_file_path = os.path.join(output_dir, log_filename_with_ts) if output_dir else log_filename_with_ts

        try:
            with open(error_log_file_path, "w", encoding="utf-8") as f:
                f.write(f"--- LOG OF CHANGES NOT MADE, AMBIGUITIES, OR WARNINGS ({datetime.datetime.now()}) ---\n")
                # ... (rest of log writing unchanged) ...
                f.write(f"Input DOCX: {os.path.basename(input_docx_path)}\n")
                f.write(f"Output DOCX: {os.path.basename(output_docx_path)}\n")
                f.write(f"Total Edits Attempted: {len(edits_to_make)}\n") # This might be misleading if we break early
                f.write(f"Log Items: {len(ambiguous_or_failed_changes_log)}\n\n")

                for log_entry in ambiguous_or_failed_changes_log:
                    f.write("-----------------------------------------\n")
                    f.write(f"Paragraph Index (1-based): {log_entry.get('paragraph_index', 'N/A')}\n")
                    f.write(f"Visible Text Snippet: {log_entry.get('visible_text_snippet', 'N/A')}\n")
                    f.write(f"Context Searched: '{log_entry.get('contextual_old_text', '')}'\n")
                    f.write(f"Specific Old Text: '{log_entry.get('specific_old_text', '')}'\n")
                    f.write(f"Specific New Text: '{log_entry.get('specific_new_text', 'N/A')}'\n")
                    f.write(f"LLM Reason for Change: {log_entry.get('llm_reason', 'N/A')}'\n")
                    f.write(f"Issue: {log_entry.get('issue', 'Unknown')}\n")
                    if 'text_from_elements' in log_entry:
                         f.write(f"Text from XML elements: '{log_entry.get('text_from_elements')}'\n")
                    if log_entry.get('type') == "Warning": f.write(f"Type: Warning\n")
                f.write("-----------------------------------------\n")
            print(f"Log file with details on {len(ambiguous_or_failed_changes_log)} items saved to: '{error_log_file_path}'")
            log_debug(f"Log file saved to: '{error_log_file_path}'")
        except Exception as e:
            log_debug(f"ERROR: Could not write to log file '{error_log_file_path}': {e}")
            error_log_file_path = None 
    else:
        print(f"No ambiguous changes, critical errors, or warnings logged that required file logging.")
        log_debug("No items for error log file.")

    return True, error_log_file_path, ambiguous_or_failed_changes_log

if __name__ == '__main__':
    import argparse
    # This part is for standalone script execution, not directly used by the FastAPI app
    # but useful for testing the word_processor independently.

    DEFAULT_EDITS_FILE_PATH = "edits_to_apply.json"
    DEFAULT_INPUT_DOCX_PATH = "sample_input.docx" # Provide a sample for testing
    DEFAULT_OUTPUT_DOCX_PATH = "sample_output_changed.docx"

    parser = argparse.ArgumentParser(description="Apply tracked changes to a Word document based on an edits file or direct JSON string.")
    parser.add_argument("--input", default=DEFAULT_INPUT_DOCX_PATH, help=f"Path to the input DOCX file (default: {DEFAULT_INPUT_DOCX_PATH})")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DOCX_PATH, help=f"Path for the output DOCX file (default: {DEFAULT_OUTPUT_DOCX_PATH})")
    parser.add_argument("--editsfile", default=DEFAULT_EDITS_FILE_PATH, help=f"Path to the JSON file with edits (default: {DEFAULT_EDITS_FILE_PATH})")
    parser.add_argument("--editsjson", type=str, help="JSON string containing the edits directly.")
    parser.add_argument("--author", default=DEFAULT_AUTHOR_NAME, help=f"Author name for tracked changes (default: {DEFAULT_AUTHOR_NAME}).")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for verbose console output.")
    parser.add_argument("--caseinsensitive", action="store_false", dest="case_sensitive", help="Perform case-insensitive search (default is case-sensitive).")
    parser.add_argument("--nocase", action="store_false", dest="case_sensitive", help="Alias for --caseinsensitive.") # Kept for consistency
    parser.add_argument("--nocomments", action="store_false", dest="add_comments", help="Disable adding comments to tracked changes (default is to add comments).")
    
    parser.set_defaults(case_sensitive=True, add_comments=True) # Explicitly set defaults
    args = parser.parse_args()

    edits_data = []
    if args.editsjson:
        try:
            edits_data = json.loads(args.editsjson)
            print(f"Loaded edits from --editsjson argument.")
        except json.JSONDecodeError as e:
            print(f"FATAL: Error decoding JSON from --editsjson: {e}. Exiting.")
            exit(1)
    elif args.editsfile:
        try:
            with open(args.editsfile, 'r', encoding='utf-8') as f:
                edits_data = json.load(f)
            print(f"Successfully loaded {len(edits_data)} edits from '{args.editsfile}'.")
        except FileNotFoundError:
            print(f"FATAL: Edits file '{args.editsfile}' not found. Exiting.")
            exit(1)
        except json.JSONDecodeError as e:
            print(f"FATAL: Error decoding JSON from '{args.editsfile}': {e}. Exiting.")
            exit(1)
        except Exception as e:
            print(f"FATAL: An unexpected error occurred while loading '{args.editsfile}': {e}. Exiting.")
            exit(1)
    else:
        print("FATAL: No edits provided. Use --editsfile or --editsjson. Exiting.")
        exit(1)

    if not os.path.exists(args.input):
        print(f"FATAL: Input file '{args.input}' not found. Exiting.")
        exit(1)
        # Removed dummy file creation for brevity, assuming user provides files for testing this complex logic.

    process_document_with_edits(
        args.input,
        args.output,
        edits_data,
        args.author,
        args.debug,
        args.case_sensitive,
        args.add_comments
    )