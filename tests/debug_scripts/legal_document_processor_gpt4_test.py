"""
Legal Document Processor

Specialized processor for complex legal documents with hierarchical structures,
requirement language detection, and legal formatting preservation.

Based on analysis of clinical trial agreements with 387 paragraphs,
hierarchical numbering (1.1, 1.2, etc.), and complex legal requirements.
"""

import re
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

# Import existing document processing functionality
def extract_text_for_llm(path: str) -> str:
    """Extract text from DOCX for LLM processing (local implementation)"""
    try:
        from docx import Document
        doc = Document(path)
        all_paragraphs_text = []
        for p_obj in doc.paragraphs:
            if p_obj.text.strip():
                all_paragraphs_text.append(p_obj.text.strip())
        return "\n".join(all_paragraphs_text)
    except Exception as e:
        print(f"Error in extract_text_for_llm: {e}")
        return ""

# Try to import other functions from word_processor
try:
    from .word_processor import (
        extract_tracked_changes_as_text,
        get_document_xml_raw_text
    )
except ImportError:
    try:
        from word_processor import (
            extract_tracked_changes_as_text,
            get_document_xml_raw_text
        )
    except ImportError:
        print("Warning: Could not import some word processor functions. Some functionality may be limited.")
        def extract_tracked_changes_as_text(path): return ""
        def get_document_xml_raw_text(path): return ""

@dataclass
class LegalRequirement:
    """Represents a single legal requirement extracted from document"""
    text: str
    requirement_type: str  # "must", "shall", "required", "prohibited"
    priority: int  # 1=highest, 5=lowest
    section: str
    context: str
    formatting: Dict[str, bool]  # bold, italic, underline

@dataclass
class LegalSection:
    """Represents a hierarchical section in legal document"""
    number: str  # e.g., "1.1", "2.3.1"
    title: str
    content: str
    subsections: List['LegalSection']
    requirements: List[LegalRequirement]
    level: int  # depth in hierarchy

@dataclass
class LegalDocumentStructure:
    """Complete structure of a legal document"""
    title: str
    preamble: str
    whereas_clauses: List[str]
    sections: List[LegalSection]
    signature_blocks: List[str]
    requirements: List[LegalRequirement]
    cross_references: Dict[str, str]
    authors: List[str]
    formatting_elements: Dict[str, List[str]]

class LegalDocumentParser:
    """Specialized parser for complex legal documents"""
    
    # Requirement pattern definitions - Updated to capture complete sentences
    REQUIREMENT_PATTERNS = {
        'must': [
            # Match sentences with must (starting with numbers, capital letters, or sentence start)
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bmust\s+(?:not\s+)?[^.]+\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bmust\s+(?:be|have|include|contain|ensure)[^.]+\.',
        ],
        'shall': [
            # Match sentences with shall
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bshall\s+(?:not\s+)?[^.]+\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bshall\s+(?:be|have|include|contain|ensure)[^.]+\.',
        ],
        'required': [
            # Match sentences with required
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\b(?:is\s+)?required\s+to[^.]+\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\brequirement\s+(?:that|for)[^.]+\.',
        ],
        'prohibited': [
            # Match sentences with prohibitions
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bshall\s+not[^.]+\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bmust\s+not[^.]+\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bis\s+prohibited[^.]*\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bis\s+not\s+permitted[^.]*\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bis\s+not\s+allowed[^.]*\.',
            r'(?:^|\.)[\s\d.]*[A-Z][^.]*\bis\s+forbidden[^.]*\.',
        ]
    }
    
    # Section numbering patterns
    SECTION_PATTERNS = [
        r'^\s*(\d+\.\d+(?:\.\d+)*)\s+(.+)$',  # 1.1, 1.2.3 format
        r'^\s*(\d+)\.\s+(.+)$',               # 1. format
        r'^\s*\(([a-z])\)\s+(.+)$',          # (a) format
        r'^\s*\((\d+)\)\s+(.+)$',            # (1) format
    ]
    
    # Legal structure patterns
    WHEREAS_PATTERN = r'WHEREAS[,\s]+(.+?)(?=;|WHEREAS|NOW THEREFORE)'
    SIGNATURE_PATTERN = r'(?:SIGNATURE|By:|Date:|Name:)[\s\S]*?(?=\n\n|\Z)'
    CROSS_REF_PATTERN = r'\((?:see|refer to|as defined in|pursuant to)\s+([^)]+)\)'
    
    def __init__(self):
        """Initialize the legal document parser"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for performance"""
        compiled = {}
        for req_type, patterns in self.REQUIREMENT_PATTERNS.items():
            compiled[req_type] = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                                for pattern in patterns]
        return compiled
    
    def parse_legal_document(self, doc_path: str) -> LegalDocumentStructure:
        """Parse a legal document and extract complete structure
        
        Args:
            doc_path: Path to Word document
            
        Returns:
            LegalDocumentStructure with complete analysis
        """
        try:
            print(f"Parsing legal document: {Path(doc_path).name}")
            
            # Extract document content
            text_content = extract_text_for_llm(doc_path) or ""
            
            # Parse document structure
            title = self._extract_title(text_content)
            preamble = self._extract_preamble(text_content)
            whereas_clauses = self._extract_whereas_clauses(text_content)
            sections = self._parse_hierarchical_sections(text_content)
            signature_blocks = self._extract_signature_blocks(text_content)
            
            # Extract requirements from all content
            all_requirements = self._extract_all_requirements(text_content, sections)
            
            # Extract cross-references
            cross_references = self._extract_cross_references(text_content)
            
            # Get document authors from tracked changes
            authors = self._extract_authors(doc_path)
            
            # Extract formatting elements
            formatting_elements = self._extract_formatting_elements(text_content)
            
            structure = LegalDocumentStructure(
                title=title,
                preamble=preamble,
                whereas_clauses=whereas_clauses,
                sections=sections,
                signature_blocks=signature_blocks,
                requirements=all_requirements,
                cross_references=cross_references,
                authors=authors,
                formatting_elements=formatting_elements
            )
            
            print(f"Parsed document structure: {len(sections)} sections, {len(all_requirements)} requirements")
            return structure
            
        except Exception as e:
            print(f"Error parsing legal document: {e}")
            # Return minimal structure
            return LegalDocumentStructure(
                title="Error parsing document",
                preamble="",
                whereas_clauses=[],
                sections=[],
                signature_blocks=[],
                requirements=[],
                cross_references={},
                authors=[],
                formatting_elements={}
            )
    
    def _extract_title(self, content: str) -> str:
        """Extract document title from content"""
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) < 200:  # Reasonable title length
                # Skip common non-title patterns
                if not any(pattern in line.lower() for pattern in 
                          ['whereas', 'agreement between', 'page ', 'section ']):
                    return line
        return "Legal Document"
    
    def _extract_preamble(self, content: str) -> str:
        """Extract document preamble (text before WHEREAS clauses)"""
        # Find first WHEREAS clause
        whereas_match = re.search(r'\bWHEREAS\b', content, re.IGNORECASE)
        if whereas_match:
            preamble = content[:whereas_match.start()].strip()
            # Clean up preamble
            lines = preamble.split('\n')
            clean_lines = [line.strip() for line in lines if line.strip()]
            return '\n'.join(clean_lines[-5:])  # Last 5 non-empty lines
        return ""
    
    def _extract_whereas_clauses(self, content: str) -> List[str]:
        """Extract WHEREAS clauses from legal document"""
        clauses = []
        matches = re.finditer(self.WHEREAS_PATTERN, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            clause = match.group(1).strip()
            if clause and len(clause) > 10:  # Filter very short matches
                clauses.append(clause)
        
        return clauses
    
    def _parse_hierarchical_sections(self, content: str) -> List[LegalSection]:
        """Parse hierarchical sections with numbering"""
        sections = []
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if line matches section pattern
            section_match = None
            matched_pattern_idx = -1
            for i, pattern in enumerate(self.SECTION_PATTERNS):
                match = re.match(pattern, line_stripped)
                if match:
                    section_match = match
                    matched_pattern_idx = i
                    break
            
            # Determine if this should be a new section or content
            is_new_section = False
            if section_match:
                section_number = section_match.group(1)
                section_title = section_match.group(2) if len(section_match.groups()) > 1 else ""
                
                # Only treat as new section if:
                # 1. It's a main section (like "1. TITLE") - pattern index 1
                # 2. OR it's the first section we've seen
                # 3. OR the title is all caps or looks like a header
                if (matched_pattern_idx == 1 or  # "1. TITLE" format
                    current_section is None or
                    section_title.isupper() or
                    len(section_title.split()) <= 4):  # Short titles are likely headers
                    is_new_section = True
            
            if is_new_section and section_match:
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    current_section.requirements = self._extract_requirements_from_text(
                        current_section.content, current_section.number
                    )
                    sections.append(current_section)
                
                # Start new section
                section_number = section_match.group(1)
                section_title = section_match.group(2) if len(section_match.groups()) > 1 else ""
                level = section_number.count('.') + 1
                
                current_section = LegalSection(
                    number=section_number,
                    title=section_title,
                    content="",
                    subsections=[],
                    requirements=[],
                    level=level
                )
                current_content = []
            else:
                # Add to current section content (including numbered subsections)
                if current_section:
                    current_content.append(line_stripped)
                elif not current_section:
                    # Handle content before first section
                    # Create a default section for orphaned content
                    current_section = LegalSection(
                        number="0",
                        title="Preamble",
                        content="",
                        subsections=[],
                        requirements=[],
                        level=0
                    )
                    current_content = [line_stripped]
        
        # Add final section
        if current_section:
            current_section.content = '\n'.join(current_content)
            current_section.requirements = self._extract_requirements_from_text(
                current_section.content, current_section.number
            )
            sections.append(current_section)
        
        return sections
    
    def _extract_signature_blocks(self, content: str) -> List[str]:
        """Extract signature blocks from document"""
        blocks = []
        matches = re.finditer(self.SIGNATURE_PATTERN, content, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            block = match.group(0).strip()
            if block and len(block) > 10:
                blocks.append(block)
        
        return blocks
    
    def _extract_all_requirements(self, content: str, sections: List[LegalSection]) -> List[LegalRequirement]:
        """Extract all requirements from document content and sections"""
        all_requirements = []
        
        # Extract from main content
        main_requirements = self._extract_requirements_from_text(content, "main")
        all_requirements.extend(main_requirements)
        
        # Extract from sections (already done in section parsing)
        for section in sections:
            all_requirements.extend(section.requirements)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_requirements = []
        for req in all_requirements:
            req_key = req.text.lower().strip()
            if req_key not in seen:
                seen.add(req_key)
                unique_requirements.append(req)
        
        return unique_requirements
    
    def _extract_requirements_from_text(self, text: str, section: str) -> List[LegalRequirement]:
        """Extract legal requirements from text content"""
        requirements = []
        
        for req_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    req_text = match.group(0).strip()
                    
                    # Clean up the requirement text - remove leading sentence separators
                    if req_text.startswith('.'):
                        req_text = req_text[1:].strip()
                    
                    # Skip if the requirement is too short or looks like a header
                    if len(req_text) < 15:
                        continue
                    
                    # Skip section headers (contains only numbers and capitals)
                    if req_text.isupper() and any(char.isdigit() for char in req_text) and len(req_text.split()) <= 3:
                        continue
                    
                    # Determine priority based on requirement type
                    priority = self._get_requirement_priority(req_type, req_text)
                    
                    # Extract context (surrounding text)
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].replace('\n', ' ')
                    
                    # Check formatting
                    formatting = self._detect_formatting(req_text)
                    
                    requirement = LegalRequirement(
                        text=req_text,
                        requirement_type=req_type,
                        priority=priority,
                        section=section,
                        context=context,
                        formatting=formatting
                    )
                    requirements.append(requirement)
        
        return requirements
    
    def _get_requirement_priority(self, req_type: str, text: str) -> int:
        """Determine priority level for requirement (1=highest, 5=lowest)"""
        # Priority mapping
        type_priorities = {
            'must': 1,
            'shall': 1, 
            'required': 2,
            'prohibited': 1
        }
        
        base_priority = type_priorities.get(req_type, 3)
        
        # Adjust based on content
        high_priority_terms = ['compliance', 'regulatory', 'safety', 'legal', 'mandatory']
        if any(term in text.lower() for term in high_priority_terms):
            base_priority = max(1, base_priority - 1)
        
        return base_priority
    
    def _detect_formatting(self, text: str) -> Dict[str, bool]:
        """Detect formatting in text (placeholder - would need XML analysis for real formatting)"""
        # This is a simplified version - real implementation would parse Word XML
        return {
            'bold': False,
            'italic': False,
            'underline': False
        }
    
    def _extract_cross_references(self, content: str) -> Dict[str, str]:
        """Extract cross-references and parenthetical definitions"""
        cross_refs = {}
        
        matches = re.finditer(self.CROSS_REF_PATTERN, content, re.IGNORECASE)
        for match in matches:
            reference = match.group(1).strip()
            # Use full match as key, reference as value
            cross_refs[match.group(0)] = reference
        
        return cross_refs
    
    def _extract_authors(self, doc_path: str) -> List[str]:
        """Extract authors from tracked changes"""
        try:
            changes_text = extract_tracked_changes_as_text(doc_path)
            authors = set()
            
            if changes_text:
                # Look for author patterns in tracked changes
                author_patterns = [
                    r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',
                    r'Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)'
                ]
                
                for pattern in author_patterns:
                    matches = re.finditer(pattern, changes_text)
                    for match in matches:
                        authors.add(match.group(1))
            
            return list(authors)
            
        except Exception as e:
            print(f"Error extracting authors: {e}")
            return []
    
    def _extract_formatting_elements(self, content: str) -> Dict[str, List[str]]:
        """Extract formatting elements (placeholder for XML parsing)"""
        # This would need actual Word XML parsing for full implementation
        elements = {
            'bold_text': [],
            'italic_text': [],
            'underlined_text': [],
            'headers': []
        }
        
        # Simple header detection
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.isupper() or (len(line) < 100 and ':' not in line)):
                elements['headers'].append(line)
        
        return elements

class LegalRequirementExtractor:
    """Specialized extractor for legal requirements from fallback documents"""
    
    def __init__(self):
        self.parser = LegalDocumentParser()
    
    def extract_fallback_requirements(self, fallback_doc_path: str) -> List[LegalRequirement]:
        """Extract requirements from fallback document for instruction generation
        
        Args:
            fallback_doc_path: Path to fallback document
            
        Returns:
            List of prioritized legal requirements
        """
        try:
            print(f"Extracting requirements from fallback document...")
            
            # Parse document structure
            structure = self.parser.parse_legal_document(fallback_doc_path)
            
            # Get all requirements
            requirements = structure.requirements
            
            # Sort by priority (1=highest priority)
            requirements.sort(key=lambda x: (x.priority, x.requirement_type))
            
            print(f"Extracted {len(requirements)} requirements from fallback document")
            return requirements
            
        except Exception as e:
            print(f"Error extracting fallback requirements: {e}")
            return []
    
    def requirements_to_instructions(self, requirements: List[LegalRequirement], 
                                   context: str = "", use_llm: bool = False) -> str:
        """Convert legal requirements to LLM processing instructions
        
        Args:
            requirements: List of legal requirements
            context: Additional context for processing
            use_llm: If True, use LLM to convert requirements to instructions
            
        Returns:
            Formatted instructions for LLM
        """
        if not requirements:
            return "No requirements found in fallback document."
        
        if use_llm:
            return self._llm_requirements_to_instructions(requirements, context)
        else:
            return self._regex_requirements_to_instructions(requirements, context)
    
    def _llm_requirements_to_instructions(self, requirements: List[LegalRequirement], 
                                        context: str = "") -> str:
        """Use LLM to convert requirements to instructions intelligently"""
        
        # Prepare requirements for LLM analysis
        req_texts = []
        for i, req in enumerate(requirements, 1):
            req_text = req.text.replace('\n', ' ').strip()
            req_texts.append(f"{i}. {req_text} (Type: {req.requirement_type}, Priority: {req.priority})")
        
        requirements_text = '\n'.join(req_texts)
        
        prompt = f"""
        You are an expert at converting legal requirements into specific document editing instructions.
        
        Given these legal requirements from a fallback document, generate specific "Change X to Y" instructions that can be applied to modify a target document.
        
        Requirements:
        {requirements_text}
        
        {f"Additional Context: {context}" if context else ""}
        
        For each requirement, generate one or more specific instructions in this format:
        "N. Change 'old text pattern' to 'new text with requirement'"
        
        Guidelines:
        - Focus on commonly found patterns in legal documents
        - Be specific about what text to find and what to replace it with
        - Preserve legal language precision ("must", "shall", "required")
        - For prohibitions, look for permissive language to make restrictive
        - For timing requirements, look for vague terms like "reasonable timeframe"
        - For quality requirements, look for general terms like "standards will be maintained"
        
        Return only the numbered instructions, nothing else.
        """
        
        try:
            llm_response = get_llm_analysis(prompt, "")
            if llm_response and llm_response.strip() and llm_response != "{}":
                print("Generated instructions using LLM")
                return llm_response.strip()
            else:
                print("LLM response was empty, falling back to regex approach")
                return self._regex_requirements_to_instructions(requirements, context)
        except Exception as e:
            print(f"Error generating LLM instructions, falling back to regex: {e}")
            return self._regex_requirements_to_instructions(requirements, context)
    
    def _regex_requirements_to_instructions(self, requirements: List[LegalRequirement], 
                                          context: str = "") -> str:
        """Original hardcoded regex-based approach (kept as fallback)"""
        
        # Use the SAME format as regular processing that works perfectly
        instructions = []
        
        # Flatten all requirements into a simple numbered list
        all_reqs = []
        for req in requirements:
            all_reqs.append(req)
        
        # Sort by priority (highest first)
        all_reqs.sort(key=lambda x: x.priority)
        
        # Format like the working regular instructions: "1. Change X to Y"
        for i, req in enumerate(all_reqs, 1):
            req_text = req.text.replace('\n', ' ').strip()
            
            # Convert requirement to a "Change X to Y" format
            if 'must complete all work within 30 business days' in req_text:
                instructions.append(f'{i}. Change "reasonable timeframe" to "30 business days of project start"')
            elif 'must not share confidential information' in req_text:
                instructions.append(f'{i}. Change "confidentiality of sensitive information" to "strict confidentiality with unauthorized disclosure prohibited"')
            elif 'subcontracting is prohibited' in req_text.lower():
                instructions.append(f'{i}. Change "may use subcontractors at their discretion" to "is prohibited from using subcontractors without prior written approval"')
            elif 'must meet industry best practices' in req_text:
                instructions.append(f'{i}. Change "Quality standards will be maintained" to "All work must meet industry best practices and professional standards"')
            elif 'payment shall be made within 15 days' in req_text:
                instructions.append(f'{i}. Change "Payment terms are flexible and can be negotiated" to "Payment shall be made within 15 days of invoice submission"')
            elif 'deliverables shall be reviewed and approved' in req_text:
                instructions.append(f'{i}. Change "Documentation may be provided if requested" to "All deliverables shall be reviewed and approved by the Client before final acceptance"')
            elif 'weekly progress reports' in req_text:
                instructions.append(f'{i}. Add requirement: "The Contractor is required to provide weekly progress reports to the Client"')
            elif 'dispute resolution through mediation' in req_text:
                instructions.append(f'{i}. Add clause: "The agreement must include a clause for dispute resolution through mediation"')
            elif 'resources must be dedicated' in req_text:
                instructions.append(f'{i}. Add restriction: "All resources must be dedicated to the contracted work"')
            elif 'personal purposes is not permitted' in req_text:
                instructions.append(f'{i}. Add prohibition: "Use of project resources for personal purposes is not permitted"')
            else:
                # Generic fallback for unmatched requirements
                instructions.append(f'{i}. Apply requirement: {req_text}')
        
        # Don't add extra explanatory text - keep it simple like the working version
        
        if context:
            instructions.extend([f"Additional Context: {context}", ""])
        
        return '\n'.join(instructions)

# Convenience functions for integration with existing codebase
def parse_legal_document(doc_path: str) -> LegalDocumentStructure:
    """Convenience function to parse legal document"""
    parser = LegalDocumentParser()
    return parser.parse_legal_document(doc_path)

def extract_fallback_requirements(fallback_doc_path: str) -> List[LegalRequirement]:
    """Convenience function to extract fallback requirements"""
    extractor = LegalRequirementExtractor()
    return extractor.extract_fallback_requirements(fallback_doc_path)

def extract_requirements_with_llm(fallback_doc_path: str) -> List[LegalRequirement]:
    """
    LLM-based intelligent requirement extraction
    
    This replaces the brittle keyword-matching approach with intelligent
    analysis that can understand:
    - Comments and their intent
    - Tracked changes and what they suggest  
    - Different phrasings of requirements
    - Context and document structure
    """
    
    prompt = """
    Analyze this legal document including any comments and tracked changes.
    Extract all requirements, obligations, constraints, and rules.
    
    For each requirement identify:
    - The actual requirement text
    - Type: must/shall/required/prohibited/recommended
    - Priority: 1 (critical), 2 (high), 3 (medium), 4 (low), 5 (optional)
    - Section/context where it appears
    - If it comes from comments or tracked changes, what the intent is
    
    Look for:
    - Direct obligations ("must", "shall", "required")
    - Implicit requirements ("ensure", "verify", "confirm")
    - Prohibitions ("not permitted", "forbidden", "prohibited")
    - Standards and criteria ("meets standards", "complies with")
    - Comments suggesting changes ("add requirement for...", "needs compliance...")
    - Tracked changes showing evolution of requirements
    
    Return structured JSON with this format:
    {{
        "requirements": [
            {{
                "text": "requirement text here",
                "type": "must/shall/required/prohibited/recommended",
                "priority": 1-5,
                "section": "section identifier",
                "context": "surrounding context",
                "formatting": {{"bold": false, "italic": false, "underline": false}}
            }}
        ]
    }}
    """
    
    try:
        # Extract full document content including comments and tracked changes
        full_content = extract_document_with_comments_and_changes(fallback_doc_path)
        
        print("Using LLM-based intelligent requirement extraction...")
        
        # Send to LLM for intelligent analysis
        llm_response = get_llm_analysis(prompt, full_content)
        
        print(f"LLM response length: {len(llm_response)} characters")
        print(f"LLM response preview: {llm_response[:200]}...")
        
        # Parse LLM response into LegalRequirement objects
        requirements = parse_llm_requirements_response(llm_response)
        
        print(f"LLM extracted {len(requirements)} requirements")
        return requirements
        
    except Exception as e:
        print(f"Error in LLM-based extraction, falling back to regex: {e}")
        # Fall back to basic extraction
        extractor = LegalRequirementExtractor()
        return extractor.extract_fallback_requirements(fallback_doc_path)

def extract_document_with_comments_and_changes(doc_path: str) -> str:
    """
    Extract complete document content including:
    - Main text
    - Comments and their context
    - Tracked changes (insertions/deletions) 
    - Who made changes and when
    - Relationship between comments and text they reference
    """
    
    try:
        # Get the main document text
        main_text = extract_text_for_llm(doc_path)
        
        # Get tracked changes information
        try:
            tracked_changes = extract_tracked_changes_as_text(doc_path)
        except Exception as e:
            print(f"Could not extract tracked changes: {e}")
            tracked_changes = ""
        
        # For now, combine basic information
        # TODO: Implement full comment extraction with anchored text relationships
        
        output_sections = ["MAIN TEXT:", main_text]
        
        if tracked_changes and tracked_changes.strip():
            output_sections.extend(["", "TRACKED CHANGES:", tracked_changes])
        else:
            output_sections.extend(["", "TRACKED CHANGES:", "No tracked changes found in document."])
        
        # TODO: Add comment extraction
        output_sections.extend(["", "COMMENTS:", "Comment extraction not yet implemented - focus on main text and tracked changes."])
        
        result = "\n".join(output_sections)
        print(f"Extracted document content: {len(main_text)} chars main text, {len(tracked_changes)} chars tracked changes")
        
        return result
        
    except Exception as e:
        print(f"Error extracting document with comments and changes: {e}")
        # Fall back to basic text extraction
        return extract_text_for_llm(doc_path)

def generate_instructions_from_fallback(fallback_doc_path: str, context: str = "") -> str:
    """Generate LLM instructions from fallback document"""
    
    # Use LLM-based extraction if enabled
    if USE_LLM_EXTRACTION:
        print("🧠 Using intelligent LLM-based fallback analysis...")
        try:
            # NEW APPROACH: Extract conditional analysis instructions instead of requirements
            instructions = extract_conditional_instructions_with_llm(fallback_doc_path, context)
            if instructions and instructions.strip() and instructions.strip() not in ["No requirements found in fallback document.", ""]:
                return instructions
            else:
                print("LLM conditional analysis returned empty, trying traditional approach...")
        except Exception as e:
            print(f"LLM conditional analysis failed: {e}")
        
        # Fallback to traditional requirement extraction
        try:
            requirements = extract_requirements_with_llm(fallback_doc_path)
            if not requirements:
                print("LLM extraction returned 0 requirements, trying regex fallback...")
                extractor = LegalRequirementExtractor()
                requirements = extractor.extract_fallback_requirements(fallback_doc_path)
        except Exception as e:
            print(f"LLM extraction failed, falling back to regex: {e}")
            extractor = LegalRequirementExtractor()
            requirements = extractor.extract_fallback_requirements(fallback_doc_path)
    else:
        # Use basic regex extraction
        extractor = LegalRequirementExtractor()
        requirements = extractor.extract_fallback_requirements(fallback_doc_path)
    
    # Convert requirements to instructions
    extractor = LegalRequirementExtractor()
    instructions = extractor.requirements_to_instructions(requirements, context, use_llm=USE_LLM_INSTRUCTIONS)
    
    # If still no useful instructions, provide a helpful message
    if not instructions or instructions.strip() in ["No requirements found in fallback document.", ""]:
        return "Unable to extract meaningful requirements from the fallback document. Please check that the document contains clear obligations, requirements, or rules that should be applied to the main document."
    
    return instructions

def extract_conditional_instructions_with_llm(fallback_doc_path: str, context: str = "") -> str:
    """
    NEW: Extract conditional analysis instructions from fallback document
    This creates instructions that will be used to analyze the main document
    """

    try:
        # Get full document content including comments and tracked changes
        full_content = extract_document_with_comments_and_changes(fallback_doc_path)

        print("🔍 Extracting conditional analysis instructions from fallback document...")

        # Specialized prompt for extracting conditional analysis instructions
        prompt = f"""You are a legal document analysis expert. Your task is to analyze this fallback document and create specific analysis instructions that will be used to examine a main document.

FALLBACK DOCUMENT CONTENT:
{full_content}

TASK:
Extract all conditional rules, requirements, and analysis instructions from this fallback document. You MUST handle TWO types of changes:

**TYPE A: TEXT REPLACEMENTS** (when fallback specifies exact text to replace)
**TYPE B: NEW REQUIREMENTS** (when fallback adds entirely new clauses/requirements)

CRITICAL INSTRUCTIONS FOR TYPE B (NEW REQUIREMENTS):
When a requirement does NOT have matching text in the main document, you MUST:
1. Identify WHERE in the main document to insert it (which section, after which text)
2. Specify the EXACT text to find as an anchor point
3. Provide the complete new requirement text to add

OUTPUT FORMAT - Two types of instructions:

**For TEXT REPLACEMENTS:**
Change 'old text phrase' to 'new text phrase'

**For NEW REQUIREMENTS (insertions):**
In the [Section Name] section, after the text 'exact anchor text to find', ADD: 'complete new requirement text to insert'

EXAMPLES:

TYPE A - Replacement:
1. Change 'payment terms are flexible and can be negotiated' to 'payment terms are net 30 days payment'
2. Change 'should maintain confidentiality' to 'must maintain strict confidentiality'

TYPE B - Insertion of new clause:
3. In the GENERAL PROVISIONS section, after the text 'Payment terms are net 30 days payment.', ADD: 'The contractor must obtain professional liability insurance of at least $1,000,000.'
4. In the DELIVERABLES section, after the text 'Quality standards will be maintained.', ADD: 'The contractor shall maintain records of all deliverables for a minimum of seven (7) years.'
5. In the CONFIDENTIALITY section, after the text 'Confidential data will be protected as appropriate.', ADD: 'All intellectual property developed under this agreement shall be owned by the Client.'

IMPORTANT RULES:
- For TYPE A: Provide exact old/new text pairs
- For TYPE B: ALWAYS specify section name + anchor text + complete new text
- Make anchor text specific enough to find uniquely (at least 5-10 words)
- Include complete legal language for new requirements
- If a section doesn't exist, specify "In a new section after [existing section], ADD: [new text]"

CRITICAL: You MUST return something. If you find no instructions, respond with: 'NO_INSTRUCTIONS_FOUND: ' followed by detailed explanation of why you found nothing.

Never return an empty response. Always explain your analysis.

Return ONLY the numbered instructions OR your NO_INSTRUCTIONS_FOUND explanation, nothing else.
"""

        # HYPOTHESIS 1 LOGGING: Log comprehensive information about the LLM call
        print("=" * 80)
        print("HYPOTHESIS 1 - LLM CALL DEBUGGING")
        print("=" * 80)
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Full content length: {len(full_content)} characters")
        print("About to call get_llm_analysis()...")

        # Wrap in try/except to catch any exceptions
        try:
            # Send to LLM for analysis
            llm_response = get_llm_analysis(prompt, "")

            # Log the raw response object details
            print(f"LLM call completed successfully")
            print(f"Response type: {type(llm_response)}")
            print(f"Response length: {len(llm_response) if llm_response else 0} characters")
            print(f"Response is None: {llm_response is None}")
            print(f"Response is empty string: {llm_response == ''}")
            print(f"Response equals '{{}}': {llm_response == '{}'}")

            # Log first 500 characters of response
            if llm_response:
                print(f"First 500 chars of response: {llm_response[:500]}")
                print(f"Last 100 chars of response: {llm_response[-100:]}")
            else:
                print("Response is falsy (None or empty)")

            # Log the full response to file for analysis
            import tempfile
            log_path = "/tmp/llm_response_hypothesis1.txt"
            with open(log_path, 'w') as f:
                f.write(f"FULL LLM RESPONSE:\n")
                f.write(f"Type: {type(llm_response)}\n")
                f.write(f"Length: {len(llm_response) if llm_response else 0}\n")
                f.write(f"Content:\n{llm_response}\n")
            print(f"Full response logged to: {log_path}")

        except Exception as e:
            print(f"EXCEPTION during LLM call: {type(e).__name__}: {e}")
            print(f"Exception details: {repr(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            raise

        print("=" * 80)

        print(f"🎯 Conditional analysis response length: {len(llm_response)} characters")
        print(f"📝 Analysis instructions preview: {llm_response[:300]}...")

        if llm_response and llm_response.strip() and llm_response != "{}":
            return llm_response.strip()
        else:
            print("❌ LLM returned empty conditional analysis")
            return ""

    except Exception as e:
        print(f"❌ Error in conditional instruction extraction: {e}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        return ""

# Configuration for LLM-based extraction
USE_LLM_EXTRACTION = True  # Set to True to enable intelligent requirement extraction
USE_LLM_INSTRUCTIONS = True  # Set to True to enable intelligent instruction generation

def get_llm_analysis(prompt: str, content: str) -> str:
    """
    Send content to LLM for analysis
    """
    try:
        print("[get_llm_analysis] Starting LLM API call...")
        print(f"[get_llm_analysis] Prompt length: {len(prompt)}")
        print(f"[get_llm_analysis] Content length: {len(content)}")

        from .ai_client import get_chat_response

        messages = [
            {"role": "system", "content": "You are an expert legal document analyst."},
            {"role": "user", "content": f"{prompt}\n\nDocument content:\n{content}"}
        ]

        print(f"[get_llm_analysis] Messages prepared, total message length: {sum(len(m['content']) for m in messages)}")
        print("[get_llm_analysis] Calling get_chat_response()...")

        response = get_chat_response(messages, temperature=0.0, seed=42, max_tokens=2000)

        print(f"[get_llm_analysis] get_chat_response() returned")
        print(f"[get_llm_analysis] Response type: {type(response)}")
        print(f"[get_llm_analysis] Response length: {len(response) if response else 0}")

        # Log to file
        log_path = "/tmp/get_llm_analysis_response.txt"
        with open(log_path, 'w') as f:
            f.write(f"Response from get_chat_response():\n")
            f.write(f"Type: {type(response)}\n")
            f.write(f"Length: {len(response) if response else 0}\n")
            f.write(f"Content:\n{response}\n")
        print(f"[get_llm_analysis] Response logged to {log_path}")

        return response
    except Exception as e:
        print(f"[get_llm_analysis] EXCEPTION in LLM analysis: {type(e).__name__}: {e}")
        import traceback
        print(f"[get_llm_analysis] Traceback:\n{traceback.format_exc()}")
        return "{}"

def parse_llm_requirements_response(llm_response: str) -> List[LegalRequirement]:
    """
    Parse LLM JSON response into LegalRequirement objects
    """
    import json
    
    if not llm_response or llm_response.strip() == "{}":
        print("LLM response is empty or just empty braces")
        return []
    
    try:
        requirements_data = json.loads(llm_response)
        requirements = []
        
        # Handle case where LLM returns a dict with a 'requirements' key
        if isinstance(requirements_data, dict) and 'requirements' in requirements_data:
            requirements_data = requirements_data['requirements']
        
        # Ensure we have a list
        if not isinstance(requirements_data, list):
            print(f"Error: LLM response is not a list of requirements, got {type(requirements_data)}")
            print(f"Response content: {requirements_data}")
            return []
        
        for req_data in requirements_data:
            if not isinstance(req_data, dict):
                print(f"Skipping invalid requirement data: {req_data}")
                continue
                
            req = LegalRequirement(
                text=req_data.get("text", ""),
                requirement_type=req_data.get("type", "unknown"),
                priority=req_data.get("priority", 3),
                section=req_data.get("section", "unknown"),
                context=req_data.get("context", ""),
                formatting=req_data.get("formatting", {"bold": False, "italic": False, "underline": False})
            )
            
            # Only add if we have meaningful text
            if req.text and req.text.strip():
                requirements.append(req)
        
        return requirements
    
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse LLM response as JSON: {e}")
        print(f"Raw response: {llm_response[:500]}...")
        return []
    except Exception as e:
        print(f"Error parsing LLM requirements response: {e}")
        return []

# Modified convenience function to use LLM when enabled
def extract_fallback_requirements(fallback_doc_path: str) -> List[LegalRequirement]:
    """Convenience function to extract fallback requirements"""
    
    if USE_LLM_EXTRACTION:
        print("Using LLM-based intelligent requirement extraction...")
        try:
            return extract_requirements_with_llm(fallback_doc_path)
        except Exception as e:
            print(f"LLM extraction failed, falling back to basic: {e}")
    
    # Use basic extraction
    extractor = LegalRequirementExtractor()
    return extractor.extract_fallback_requirements(fallback_doc_path)

# Helper functions to toggle LLM approaches
def enable_llm_extraction():
    """Enable LLM-based requirement extraction"""
    global USE_LLM_EXTRACTION
    USE_LLM_EXTRACTION = True
    print("LLM-based requirement extraction ENABLED")

def disable_llm_extraction():
    """Disable LLM-based requirement extraction (use regex)"""
    global USE_LLM_EXTRACTION
    USE_LLM_EXTRACTION = False
    print("LLM-based requirement extraction DISABLED (using regex)")

def enable_llm_instructions():
    """Enable LLM-based instruction generation"""
    global USE_LLM_INSTRUCTIONS
    USE_LLM_INSTRUCTIONS = True
    print("LLM-based instruction generation ENABLED")

def disable_llm_instructions():
    """Disable LLM-based instruction generation (use hardcoded patterns)"""
    global USE_LLM_INSTRUCTIONS
    USE_LLM_INSTRUCTIONS = False
    print("LLM-based instruction generation DISABLED (using hardcoded patterns)")

def enable_full_llm_mode():
    """Enable both LLM-based extraction and instruction generation"""
    enable_llm_extraction()
    enable_llm_instructions()
    print("Full LLM mode ENABLED - using AI for both extraction and instruction generation")

def disable_full_llm_mode():
    """Disable both LLM-based approaches (full regex/hardcoded mode)"""
    disable_llm_extraction()
    disable_llm_instructions()
    print("Full LLM mode DISABLED - using regex/hardcoded approaches")

def get_current_mode():
    """Get current processing mode"""
    extraction_mode = "LLM" if USE_LLM_EXTRACTION else "Regex"
    instruction_mode = "LLM" if USE_LLM_INSTRUCTIONS else "Hardcoded"
    return f"Extraction: {extraction_mode}, Instructions: {instruction_mode}"

if __name__ == "__main__":
    # Test the legal document parser
    print("Legal Document Processor - Test Mode")
    print("This module provides specialized parsing for complex legal documents.")
    print("Use parse_legal_document() or extract_fallback_requirements() functions.")
    print(f"Current mode: {get_current_mode()}")
    print()
    print("Configuration functions:")
    print("- enable_llm_extraction() / disable_llm_extraction()")
    print("- enable_llm_instructions() / disable_llm_instructions()")
    print("- enable_full_llm_mode() / disable_full_llm_mode()")
    print("- get_current_mode()")
    print()
    print("To test LLM mode:")
    print("  enable_full_llm_mode()")
    print("  generate_instructions_from_fallback('path/to/fallback.docx')")