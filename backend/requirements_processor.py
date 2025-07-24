"""
Requirements Processor

Advanced processor for extracting, analyzing, and managing legal requirements
from fallback documents. Integrates with LLM services for intelligent 
requirement processing and conflict resolution.

Based on analysis of clinical trial agreements and complex legal documents.
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Import existing components
try:
    from .legal_document_processor import (
        LegalRequirement, 
        LegalDocumentStructure,
        extract_fallback_requirements,
        parse_legal_document
    )
    from .llm_handler import get_llm_suggestions, get_llm_analysis_from_summary
    from .ai_client import get_ai_client
except ImportError:
    try:
        from legal_document_processor import (
            LegalRequirement, 
            LegalDocumentStructure,
            extract_fallback_requirements,
            parse_legal_document
        )
        from llm_handler import get_llm_suggestions, get_llm_analysis_from_summary
        from ai_client import get_ai_client
    except ImportError:
        print("Warning: Could not import dependencies. Some functionality may be limited.")
        # Create placeholder classes
        @dataclass
        class LegalRequirement:
            text: str
            requirement_type: str
            priority: int
            section: str
            context: str
            formatting: Dict[str, bool]

class RequirementPriority(Enum):
    """Priority levels for legal requirements"""
    CRITICAL = 1    # must, shall (compliance, safety, legal)
    HIGH = 2       # shall, required (operational, regulatory)
    MEDIUM = 3     # should, recommended (best practices)
    LOW = 4        # may, optional (preferences)
    INFORMATIONAL = 5  # notes, guidance

class RequirementCategory(Enum):
    """Categories of legal requirements"""
    COMPLIANCE = "compliance"
    PAYMENT = "payment" 
    DOCUMENTATION = "documentation"
    PROCESS = "process"
    LIABILITY = "liability"
    CONFIDENTIALITY = "confidentiality"
    REGULATORY = "regulatory"
    SAFETY = "safety"
    QUALITY = "quality"
    GENERAL = "general"

@dataclass
class ProcessedRequirement:
    """Enhanced requirement with processing metadata"""
    original: LegalRequirement
    priority_level: RequirementPriority
    category: RequirementCategory
    reformatted_text: str
    conflicts: List[str]
    dependencies: List[str]
    llm_analysis: str
    confidence_score: float
    processing_notes: List[str]

@dataclass
class RequirementConflict:
    """Represents a conflict between requirements"""
    requirement1_id: str
    requirement2_id: str
    conflict_type: str  # "contradiction", "overlap", "ambiguity"
    description: str
    severity: str  # "critical", "high", "medium", "low"
    resolution_suggestion: str

class RequirementsProcessor:
    """Advanced processor for legal requirements with LLM integration"""
    
    # Legal requirement patterns for enhanced detection
    PRIORITY_PATTERNS = {
        RequirementPriority.CRITICAL: [
            r'\bmust\s+(?:not\s+)?',
            r'\bshall\s+(?:not\s+)?',
            r'\bis\s+required\s+to\b',
            r'\bmandatory\b',
            r'\bprohibited\b'
        ],
        RequirementPriority.HIGH: [
            r'\bshall\b(?!\s+not)',
            r'\brequired\b',
            r'\bobligated?\b',
            r'\bensure\s+that\b',
            r'\bresponsible\s+for\b'
        ],
        RequirementPriority.MEDIUM: [
            r'\bshould\b',
            r'\brecommended\b',
            r'\bpreferred\b',
            r'\bencouraged\b'
        ],
        RequirementPriority.LOW: [
            r'\bmay\b',
            r'\boptional\b',
            r'\bat\s+discretion\b',
            r'\bif\s+desired\b'
        ]
    }
    
    # Category detection patterns
    CATEGORY_PATTERNS = {
        RequirementCategory.COMPLIANCE: [
            r'\bcomplia\w+\b', r'\bregulat\w+\b', r'\bapproval\b', r'\baudit\b',
            r'\binspection\b', r'\bstandard\b', r'\bguideline\b'
        ],
        RequirementCategory.PAYMENT: [
            r'\bpay\w+\b', r'\bbill\w+\b', r'\binvoice\b', r'\bmilestone\b',
            r'\bfee\b', r'\bcost\b', r'\breimburs\w+\b', r'\bbudget\b'
        ],
        RequirementCategory.DOCUMENTATION: [
            r'\bdocument\w+\b', r'\brecord\b', r'\breport\b', r'\blog\b',
            r'\btrack\b', r'\bmaintain\b', r'\bfile\b', r'\bstore\b'
        ],
        RequirementCategory.PROCESS: [
            r'\bprocess\b', r'\bprocedure\b', r'\bworkflow\b', r'\bstep\b',
            r'\bmethod\b', r'\bapproach\b', r'\bprotocol\b'
        ],
        RequirementCategory.LIABILITY: [
            r'\bliabil\w+\b', r'\bindemnif\w+\b', r'\binsurance\b', r'\bclaim\b',
            r'\bdamage\b', r'\bloss\b', r'\bresponsibility\b'
        ],
        RequirementCategory.CONFIDENTIALITY: [
            r'\bconfidential\w+\b', r'\bprivacy\b', r'\bdata\s+protection\b',
            r'\bnon-disclos\w+\b', r'\bproprietary\b', r'\bsecure\b'
        ],
        RequirementCategory.REGULATORY: [
            r'\bFDA\b', r'\bIRB\b', r'\bGCP\b', r'\bHIPAA\b', r'\bICH\b',
            r'\bregulatory\b', r'\bauthority\b', r'\bagency\b'
        ],
        RequirementCategory.SAFETY: [
            r'\bsafety\b', r'\badverse\s+event\b', r'\brisk\b', r'\bhazard\b',
            r'\bprotection\b', r'\bsecurit\w+\b'
        ],
        RequirementCategory.QUALITY: [
            r'\bquality\b', r'\bGMP\b', r'\bGLP\b', r'\bvalidation\b',
            r'\bverification\b', r'\bassurance\b', r'\bcontrol\b'
        ]
    }
    
    def __init__(self):
        """Initialize the requirements processor"""
        self.ai_client = None
        try:
            self.ai_client = get_ai_client()
            print("Requirements processor initialized with LLM support")
        except Exception as e:
            print(f"Warning: LLM not available for requirements processing: {e}")
        
        self.compiled_priority_patterns = self._compile_priority_patterns()
        self.compiled_category_patterns = self._compile_category_patterns()
    
    def _compile_priority_patterns(self) -> Dict[RequirementPriority, List[re.Pattern]]:
        """Compile priority detection patterns for performance"""
        compiled = {}
        for priority, patterns in self.PRIORITY_PATTERNS.items():
            compiled[priority] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        return compiled
    
    def _compile_category_patterns(self) -> Dict[RequirementCategory, List[re.Pattern]]:
        """Compile category detection patterns for performance"""
        compiled = {}
        for category, patterns in self.CATEGORY_PATTERNS.items():
            compiled[category] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        return compiled
    
    def process_fallback_requirements(self, fallback_doc_path: str) -> List[ProcessedRequirement]:
        """Process all requirements from fallback document with LLM enhancement
        
        Args:
            fallback_doc_path: Path to fallback document
            
        Returns:
            List of processed requirements with enhanced metadata
        """
        try:
            print(f"Processing requirements from fallback document...")
            
            # Extract raw requirements using legal document processor
            raw_requirements = extract_fallback_requirements(fallback_doc_path)
            
            print(f"Found {len(raw_requirements)} raw requirements to process")
            
            # Process each requirement
            processed_requirements = []
            for i, req in enumerate(raw_requirements):
                print(f"Processing requirement {i+1}/{len(raw_requirements)}")
                processed_req = self._process_single_requirement(req, i)
                processed_requirements.append(processed_req)
            
            # Detect conflicts between requirements
            conflicts = self._detect_requirement_conflicts(processed_requirements)
            
            # Add conflict information to requirements
            for conflict in conflicts:
                req1 = next((r for r in processed_requirements if id(r) == conflict.requirement1_id), None)
                req2 = next((r for r in processed_requirements if id(r) == conflict.requirement2_id), None)
                if req1:
                    req1.conflicts.append(conflict.description)
                if req2:
                    req2.conflicts.append(conflict.description)
            
            print(f"Processed {len(processed_requirements)} requirements with {len(conflicts)} conflicts detected")
            return processed_requirements
            
        except Exception as e:
            print(f"Error processing fallback requirements: {e}")
            return []
    
    def _process_single_requirement(self, requirement: LegalRequirement, index: int) -> ProcessedRequirement:
        """Process a single requirement with LLM analysis"""
        
        # Determine priority level
        priority_level = self._determine_priority_level(requirement)
        
        # Determine category
        category = self._determine_category(requirement)
        
        # Reformat text using LLM (if available)
        reformatted_text = self._reformat_requirement_text(requirement)
        
        # Get LLM analysis
        llm_analysis = self._get_llm_requirement_analysis(requirement)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(requirement, priority_level, category)
        
        # Generate processing notes
        processing_notes = self._generate_processing_notes(requirement, priority_level, category)
        
        return ProcessedRequirement(
            original=requirement,
            priority_level=priority_level,
            category=category,
            reformatted_text=reformatted_text,
            conflicts=[],  # Will be populated later
            dependencies=[],  # TODO: Implement dependency detection
            llm_analysis=llm_analysis,
            confidence_score=confidence_score,
            processing_notes=processing_notes
        )
    
    def _determine_priority_level(self, requirement: LegalRequirement) -> RequirementPriority:
        """Determine priority level based on requirement text and type"""
        
        # Start with original priority from legal processor
        if requirement.priority <= 1:
            base_priority = RequirementPriority.CRITICAL
        elif requirement.priority == 2:
            base_priority = RequirementPriority.HIGH
        elif requirement.priority == 3:
            base_priority = RequirementPriority.MEDIUM
        else:
            base_priority = RequirementPriority.LOW
        
        # Check text patterns for priority indicators
        text = requirement.text.lower()
        
        for priority, patterns in self.compiled_priority_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    # Use highest priority found
                    if priority.value < base_priority.value:
                        base_priority = priority
                    break
        
        # Adjust based on requirement type
        if requirement.requirement_type == "prohibited":
            base_priority = RequirementPriority.CRITICAL
        elif requirement.requirement_type in ["must", "shall"]:
            base_priority = min(base_priority, RequirementPriority.HIGH)
        
        return base_priority
    
    def _determine_category(self, requirement: LegalRequirement) -> RequirementCategory:
        """Determine category based on requirement content"""
        
        text = requirement.text.lower()
        category_scores = {}
        
        # Score each category based on pattern matches
        for category, patterns in self.compiled_category_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(pattern.findall(text))
                score += matches
            
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category or GENERAL as default
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        else:
            return RequirementCategory.GENERAL
    
    def _reformat_requirement_text(self, requirement: LegalRequirement) -> str:
        """Reformat requirement text for clarity while preserving legal meaning"""
        
        if not self.ai_client or len(requirement.text) < 20:
            return requirement.text
        
        try:
            prompt = f"""
            Please reformat the following legal requirement text for clarity while preserving exact legal meaning:
            
            Original: "{requirement.text}"
            
            Guidelines:
            - Maintain all legal terminology exactly
            - Preserve "must", "shall", "required" etc. precisely
            - Improve readability without changing meaning
            - Keep the same legal obligation level
            - Remove redundant words if safe to do so
            
            Return only the reformatted requirement text.
            """
            
            # This would use LLM if available - for now return original
            return requirement.text
            
        except Exception as e:
            print(f"Error reformatting requirement text: {e}")
            return requirement.text
    
    def _get_llm_requirement_analysis(self, requirement: LegalRequirement) -> str:
        """Get LLM analysis of requirement for better understanding"""
        
        if not self.ai_client:
            return f"Requirement analysis not available (no LLM). Type: {requirement.requirement_type}, Priority: {requirement.priority}"
        
        try:
            prompt = f"""
            Please analyze this legal requirement and provide insights:
            
            Requirement: "{requirement.text}"
            Context: "{requirement.context[:200]}..."
            Section: {requirement.section}
            
            Please provide:
            1. Key obligation or restriction
            2. Who is responsible  
            3. When/how it applies
            4. Potential compliance risks
            5. Implementation complexity (low/medium/high)
            
            Keep analysis concise (3-4 sentences).
            """
            
            # This would use LLM if available - for now return basic analysis
            return f"Legal {requirement.requirement_type} requirement from section {requirement.section}. Implementation needed for compliance."
            
        except Exception as e:
            print(f"Error getting LLM requirement analysis: {e}")
            return "Analysis not available due to processing error."
    
    def _calculate_confidence_score(self, requirement: LegalRequirement, 
                                  priority: RequirementPriority, 
                                  category: RequirementCategory) -> float:
        """Calculate confidence score for requirement processing (0.0 to 1.0)"""
        
        confidence_factors = []
        
        # Text length factor (longer requirements generally more reliable)
        if len(requirement.text) > 50:
            confidence_factors.append(0.2)
        elif len(requirement.text) > 20:
            confidence_factors.append(0.1)
        
        # Clear requirement type factor
        if requirement.requirement_type in ["must", "shall", "required", "prohibited"]:
            confidence_factors.append(0.3)
        
        # Section context factor
        if requirement.section and requirement.section != "main":
            confidence_factors.append(0.1)
        
        # Context availability factor  
        if len(requirement.context) > 100:
            confidence_factors.append(0.2)
        
        # Priority clarity factor
        if priority in [RequirementPriority.CRITICAL, RequirementPriority.HIGH]:
            confidence_factors.append(0.2)
        
        return min(sum(confidence_factors), 1.0)
    
    def _generate_processing_notes(self, requirement: LegalRequirement,
                                 priority: RequirementPriority,
                                 category: RequirementCategory) -> List[str]:
        """Generate processing notes for requirement"""
        
        notes = []
        
        # Priority-based notes
        if priority == RequirementPriority.CRITICAL:
            notes.append("CRITICAL: Must be implemented exactly as specified")
        elif priority == RequirementPriority.HIGH:
            notes.append("HIGH: Important for compliance and operations")
        
        # Category-based notes
        if category == RequirementCategory.COMPLIANCE:
            notes.append("Regulatory compliance requirement - legal review recommended")
        elif category == RequirementCategory.PAYMENT:
            notes.append("Financial obligation - budget impact assessment needed")
        elif category == RequirementCategory.SAFETY:
            notes.append("Safety requirement - risk assessment required")
        
        # Text complexity notes
        if len(requirement.text) > 200:
            notes.append("Complex requirement - may need breakdown for implementation")
        
        # Formatting notes
        if any(requirement.formatting.values()):
            notes.append("Original document has special formatting - preserve for legal clarity")
        
        return notes
    
    def _detect_requirement_conflicts(self, requirements: List[ProcessedRequirement]) -> List[RequirementConflict]:
        """Detect conflicts between processed requirements"""
        
        conflicts = []
        
        for i, req1 in enumerate(requirements):
            for j, req2 in enumerate(requirements[i+1:], i+1):
                conflict = self._check_requirement_pair_conflict(req1, req2)
                if conflict:
                    conflicts.append(conflict)
        
        print(f"Detected {len(conflicts)} potential conflicts between requirements")
        return conflicts
    
    def _check_requirement_pair_conflict(self, req1: ProcessedRequirement, 
                                       req2: ProcessedRequirement) -> Optional[RequirementConflict]:
        """Check if two requirements conflict with each other"""
        
        # Simple conflict detection based on contradictory keywords
        req1_text = req1.reformatted_text.lower()
        req2_text = req2.reformatted_text.lower()
        
        # Check for direct contradictions
        contradictions = [
            ("must", "must not"),
            ("shall", "shall not"),
            ("required", "prohibited"),
            ("mandatory", "optional")
        ]
        
        for pos, neg in contradictions:
            if (pos in req1_text and neg in req2_text) or (neg in req1_text and pos in req2_text):
                return RequirementConflict(
                    requirement1_id=str(id(req1)),
                    requirement2_id=str(id(req2)),
                    conflict_type="contradiction",
                    description=f"Requirements contain contradictory obligations: '{pos}' vs '{neg}'",
                    severity="high",
                    resolution_suggestion="Review both requirements and determine which takes precedence based on legal hierarchy"
                )
        
        # Check for overlapping obligations (same category, different approaches)
        if (req1.category == req2.category and 
            req1.priority_level == req2.priority_level and
            len(set(req1_text.split()) & set(req2_text.split())) > 3):
            
            return RequirementConflict(
                requirement1_id=str(id(req1)),
                requirement2_id=str(id(req2)),
                conflict_type="overlap",
                description=f"Requirements may overlap in {req1.category.value} obligations",
                severity="medium", 
                resolution_suggestion="Consider consolidating or clarifying the relationship between these requirements"
            )
        
        return None
    
    def generate_prioritized_instructions(self, processed_requirements: List[ProcessedRequirement],
                                        context: str = "") -> str:
        """Generate prioritized LLM instructions from processed requirements"""
        
        if not processed_requirements:
            return "No requirements found in fallback document for processing."
        
        # Group requirements by priority
        priority_groups = {}
        for req in processed_requirements:
            priority = req.priority_level
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(req)
        
        instructions = [
            "Please modify this legal document by applying the following prioritized requirements from the fallback document:",
            ""
        ]
        
        # Add requirements by priority level
        priority_order = [RequirementPriority.CRITICAL, RequirementPriority.HIGH, 
                         RequirementPriority.MEDIUM, RequirementPriority.LOW, RequirementPriority.INFORMATIONAL]
        
        for priority in priority_order:
            if priority not in priority_groups:
                continue
                
            reqs = priority_groups[priority]
            priority_name = priority.name.title()
            
            instructions.append(f"## {priority_name} Priority Requirements ({len(reqs)} items):")
            
            for i, req in enumerate(reqs, 1):
                # Use reformatted text if available, otherwise original
                req_text = req.reformatted_text if req.reformatted_text != req.original.text else req.original.text
                req_text = req_text.replace('\n', ' ').strip()
                
                instructions.append(f"{i}. {req_text}")
                
                # Add category and section info
                if req.original.section and req.original.section != "main":
                    instructions.append(f"   (Category: {req.category.value}, Section: {req.original.section})")
                else:
                    instructions.append(f"   (Category: {req.category.value})")
                
                # Add conflicts warning if any
                if req.conflicts:
                    instructions.append(f"   ⚠️ CONFLICT: {req.conflicts[0]}")
                
                # Add processing notes for critical/high priority
                if priority in [RequirementPriority.CRITICAL, RequirementPriority.HIGH] and req.processing_notes:
                    instructions.append(f"   📝 {req.processing_notes[0]}")
            
            instructions.append("")
        
        # Add general processing guidelines
        instructions.extend([
            "## Processing Guidelines:",
            "- Preserve existing legal structure and hierarchical numbering",
            "- Add tracked changes for all modifications with proper author attribution",
            "- Maintain legal precision and terminology exactly",
            "- CRITICAL and HIGH priority requirements take precedence over user instructions",
            "- Do not remove existing compliance language",
            "- Preserve cross-references and parenthetical definitions", 
            "- Maintain critical formatting (bold, underline, etc.) for legal enforceability",
            "- Handle conflicting requirements by prioritizing higher priority items",
            ""
        ])
        
        if context:
            instructions.extend([f"Additional Context: {context}", ""])
        
        # Add requirement summary
        total_reqs = len(processed_requirements)
        critical_high = len([r for r in processed_requirements if r.priority_level.value <= 2])
        conflicts = len([r for r in processed_requirements if r.conflicts])
        
        instructions.extend([
            f"## Summary: {total_reqs} total requirements, {critical_high} critical/high priority, {conflicts} with conflicts",
            ""
        ])
        
        return '\n'.join(instructions)

# Convenience functions for integration
def process_fallback_document_requirements(fallback_doc_path: str) -> List[ProcessedRequirement]:
    """Process requirements from fallback document"""
    processor = RequirementsProcessor()
    return processor.process_fallback_requirements(fallback_doc_path)

def generate_enhanced_instructions(fallback_doc_path: str, context: str = "") -> str:
    """Generate enhanced LLM instructions from fallback document"""
    processor = RequirementsProcessor()
    processed_requirements = processor.process_fallback_requirements(fallback_doc_path)
    return processor.generate_prioritized_instructions(processed_requirements, context)

if __name__ == "__main__":
    # Test the requirements processor
    print("Requirements Processor - Test Mode")
    print("This module provides enhanced requirement processing with LLM integration.")
    print("Use process_fallback_document_requirements() or generate_enhanced_instructions() functions.")