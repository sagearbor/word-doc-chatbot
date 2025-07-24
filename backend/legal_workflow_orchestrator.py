"""
Legal Workflow Orchestrator - Phase 4.1

End-to-end orchestrator for legal document processing that integrates:
- Phase 1.1: Legal Document Parser
- Phase 2.1: LLM-Based Requirements Extraction  
- Phase 2.2: Advanced Instruction Merging
- Document Processing and Validation

This orchestrator provides a seamless workflow for processing legal documents
with fallback requirements, comprehensive error handling, audit logging,
and production-ready validation.
"""

import os
import json
import shutil
import tempfile
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Import all Phase 2.x components
try:
    from .legal_document_processor import (
        parse_legal_document,
        extract_fallback_requirements,
        LegalDocumentStructure,
        LegalRequirement
    )
    from .requirements_processor import (
        RequirementsProcessor,
        process_fallback_document_requirements,
        ProcessedRequirement,
        RequirementPriority,
        RequirementCategory
    )
    from .instruction_merger import (
        InstructionMerger,
        MergeStrategy,
        ConflictResolutionStrategy,
        MergeResult,
        generate_final_llm_instructions
    )
    from .word_processor import process_document_with_edits, DEFAULT_AUTHOR_NAME
    from .llm_handler import get_llm_suggestions
    PHASE_COMPONENTS_AVAILABLE = True
    print("Phase 4.1: All Phase 2.x components imported successfully")
except ImportError as e:
    print(f"Phase 4.1: Warning - Some Phase 2.x components not available: {e}")
    PHASE_COMPONENTS_AVAILABLE = False

class WorkflowStage(Enum):
    """Stages in the legal document processing workflow"""
    INITIALIZATION = "initialization"
    DOCUMENT_ANALYSIS = "document_analysis"
    FALLBACK_PROCESSING = "fallback_processing"
    INSTRUCTION_MERGING = "instruction_merging"
    LLM_PROCESSING = "llm_processing"
    DOCUMENT_MODIFICATION = "document_modification"
    VALIDATION = "validation"
    FINALIZATION = "finalization"

class ProcessingStatus(Enum):
    """Status of workflow processing"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStageResult:
    """Result from a single workflow stage"""
    stage: WorkflowStage
    status: ProcessingStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    success: bool
    data: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]

@dataclass
class LegalDocumentWorkflowResult:
    """Complete result from legal document workflow processing"""
    workflow_id: str
    input_document_path: str
    fallback_document_path: Optional[str]
    output_document_path: Optional[str]
    user_instructions: str
    processing_settings: Dict[str, Any]
    
    # Stage results
    stage_results: List[WorkflowStageResult]
    
    # Overall results
    overall_status: ProcessingStatus
    total_duration_seconds: float
    start_time: datetime
    end_time: Optional[datetime]
    
    # Processing metrics
    requirements_extracted: int
    requirements_merged: int
    edits_suggested: int
    edits_applied: int
    legal_coherence_score: float
    
    # Audit and validation
    validation_results: Dict[str, Any]
    audit_log_path: Optional[str]
    backup_paths: List[str]
    
    # Final outputs
    processed_filename: str
    log_content: str
    status_message: str
    issues_count: int

class LegalDocumentProcessor:
    """Production-ready legal document processing orchestrator"""
    
    def __init__(self, 
                 temp_dir: Optional[str] = None,
                 enable_audit_logging: bool = True,
                 enable_backup: bool = True,
                 enable_validation: bool = True,
                 performance_mode: str = "balanced"):  # "fast", "balanced", "thorough"
        """
        Initialize the legal document processor
        
        Args:
            temp_dir: Directory for temporary files
            enable_audit_logging: Enable comprehensive audit logging
            enable_backup: Enable document backup and recovery
            enable_validation: Enable legal meaning preservation validation
            performance_mode: Processing mode for optimization
        """
        
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="legal_workflow_")
        self.enable_audit_logging = enable_audit_logging
        self.enable_backup = enable_backup
        self.enable_validation = enable_validation
        self.performance_mode = performance_mode
        
        # Initialize components if available
        if PHASE_COMPONENTS_AVAILABLE:
            self.requirements_processor = RequirementsProcessor()
            self.instruction_merger = InstructionMerger(
                merge_strategy=MergeStrategy.INTELLIGENT_MERGE,
                conflict_strategy=ConflictResolutionStrategy.LLM_ARBITRATION
            )
        else:
            self.requirements_processor = None
            self.instruction_merger = None
        
        print(f"Legal Document Processor initialized - Temp dir: {self.temp_dir}")
        print(f"Settings: Audit={enable_audit_logging}, Backup={enable_backup}, Validation={enable_validation}")
    
    def process_legal_document(self,
                             input_document_path: str,
                             user_instructions: str,
                             fallback_document_path: Optional[str] = None,
                             author_name: Optional[str] = None,
                             processing_settings: Optional[Dict[str, Any]] = None) -> LegalDocumentWorkflowResult:
        """
        Main entry point for end-to-end legal document processing
        
        Args:
            input_document_path: Path to input document to be processed
            user_instructions: User's instructions for modifications
            fallback_document_path: Optional path to fallback document with requirements
            author_name: Author name for tracked changes
            processing_settings: Additional processing settings
            
        Returns:
            Complete workflow result with all processing details
        """
        
        workflow_id = f"legal_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(input_document_path) % 10000}"
        start_time = datetime.now()
        
        # Determine workflow type for backward compatibility
        workflow_type = "ENHANCED_WITH_FALLBACK" if fallback_document_path else "SIMPLE_ORIGINAL"
        
        print(f"Starting legal document workflow: {workflow_id}")
        print(f"Workflow type: {workflow_type}")
        print(f"Input: {os.path.basename(input_document_path)}")
        print(f"Fallback: {os.path.basename(fallback_document_path) if fallback_document_path else 'None (using original simple workflow)'}")
        print(f"Instructions length: {len(user_instructions)} characters")
        
        # Initialize result structure
        result = LegalDocumentWorkflowResult(
            workflow_id=workflow_id,
            input_document_path=input_document_path,
            fallback_document_path=fallback_document_path,
            output_document_path=None,
            user_instructions=user_instructions,
            processing_settings=processing_settings or {},
            stage_results=[],
            overall_status=ProcessingStatus.IN_PROGRESS,
            total_duration_seconds=0.0,
            start_time=start_time,
            end_time=None,
            requirements_extracted=0,
            requirements_merged=0,
            edits_suggested=0,
            edits_applied=0,
            legal_coherence_score=0.0,
            validation_results={},
            audit_log_path=None,
            backup_paths=[],
            processed_filename="",
            log_content="",
            status_message="",
            issues_count=0
        )
        
        # Create audit log if enabled
        if self.enable_audit_logging:
            result.audit_log_path = self._create_audit_log(workflow_id)
            self._log_audit_event(result.audit_log_path, "WORKFLOW_START", {
                "workflow_id": workflow_id,
                "input_document": input_document_path,
                "fallback_document": fallback_document_path,
                "user_instructions_length": len(user_instructions)
            })
        
        try:
            # Stage 1: Initialization and Validation
            stage_result = self._run_initialization_stage(result)
            result.stage_results.append(stage_result)
            
            if not stage_result.success:
                result.overall_status = ProcessingStatus.FAILED
                return self._finalize_result(result)
            
            # Stage 2: Document Analysis
            stage_result = self._run_document_analysis_stage(result)
            result.stage_results.append(stage_result)
            
            if not stage_result.success:
                result.overall_status = ProcessingStatus.FAILED
                return self._finalize_result(result)
            
            # Stage 3: Fallback Processing (ONLY if fallback document provided)
            # This preserves backward compatibility - original workflow skips this entirely
            if fallback_document_path:
                print("=== ENHANCED WORKFLOW: Processing fallback document ===")
                stage_result = self._run_fallback_processing_stage(result)
                result.stage_results.append(stage_result)
                
                if stage_result.success:
                    # Stage 4: Advanced Instruction Merging (Phase 2.2)
                    print("=== ENHANCED WORKFLOW: Advanced instruction merging ===")
                    stage_result = self._run_instruction_merging_stage(result)
                    result.stage_results.append(stage_result)
                else:
                    print("Fallback processing failed - reverting to original simple workflow")
            else:
                print("=== ORIGINAL WORKFLOW: No fallback document - using simple user instructions only ===")
            
            # Stage 5: LLM Processing
            stage_result = self._run_llm_processing_stage(result)
            result.stage_results.append(stage_result)
            
            if not stage_result.success:
                result.overall_status = ProcessingStatus.FAILED
                return self._finalize_result(result)
            
            # Stage 6: Document Modification
            stage_result = self._run_document_modification_stage(result)
            result.stage_results.append(stage_result)
            
            if not stage_result.success:
                result.overall_status = ProcessingStatus.FAILED
                return self._finalize_result(result)
            
            # Stage 7: Validation
            if self.enable_validation:
                stage_result = self._run_validation_stage(result)
                result.stage_results.append(stage_result)
            
            # Stage 8: Finalization
            stage_result = self._run_finalization_stage(result)
            result.stage_results.append(stage_result)
            
            result.overall_status = ProcessingStatus.COMPLETED
            
        except Exception as e:
            error_msg = f"Critical error in legal document workflow: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            
            if result.audit_log_path:
                self._log_audit_event(result.audit_log_path, "WORKFLOW_ERROR", {
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                })
            
            result.overall_status = ProcessingStatus.FAILED
            result.status_message = error_msg
        
        return self._finalize_result(result)
    
    def _run_initialization_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Initialize and validate inputs"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.INITIALIZATION,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        try:
            # Validate input document exists
            if not os.path.exists(result.input_document_path):
                stage_result.errors.append(f"Input document not found: {result.input_document_path}")
                return self._finalize_stage_result(stage_result)
            
            # Validate fallback document if provided
            if result.fallback_document_path and not os.path.exists(result.fallback_document_path):
                stage_result.errors.append(f"Fallback document not found: {result.fallback_document_path}")
                return self._finalize_stage_result(stage_result)
            
            # Create output path
            base_name = os.path.basename(result.input_document_path)
            name, ext = os.path.splitext(base_name)
            output_name = f"{name}_processed_{result.workflow_id}{ext}"
            result.output_document_path = os.path.join(self.temp_dir, output_name)
            result.processed_filename = output_name
            
            # Create backup if enabled
            if self.enable_backup:
                backup_path = os.path.join(self.temp_dir, f"{name}_backup_{result.workflow_id}{ext}")
                shutil.copy2(result.input_document_path, backup_path)
                result.backup_paths.append(backup_path)
                stage_result.data["backup_created"] = backup_path
            
            # Validate Phase 2.x components
            if not PHASE_COMPONENTS_AVAILABLE:
                stage_result.warnings.append("Phase 2.x components not fully available - using fallback processing")
            
            stage_result.success = True
            stage_result.data.update({
                "input_validated": True,
                "output_path_created": result.output_document_path,
                "components_available": PHASE_COMPONENTS_AVAILABLE,
                "backup_enabled": self.enable_backup,
                "audit_enabled": self.enable_audit_logging
            })
            
        except Exception as e:
            stage_result.errors.append(f"Initialization error: {str(e)}")
        
        return self._finalize_stage_result(stage_result)
    
    def _run_document_analysis_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Analyze input document structure and content"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.DOCUMENT_ANALYSIS,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        try:
            # Basic document analysis
            doc_size = os.path.getsize(result.input_document_path)
            stage_result.metrics["document_size_bytes"] = doc_size
            
            # If Phase 1.1 components available, do detailed analysis
            if PHASE_COMPONENTS_AVAILABLE:
                try:
                    from .word_processor import extract_text_for_llm
                    
                    # Extract document text
                    doc_text = extract_text_for_llm(result.input_document_path)
                    stage_result.data["document_text_length"] = len(doc_text)
                    stage_result.data["document_paragraphs_estimated"] = doc_text.count('\n') + 1
                    
                    # Legal document structure analysis if available
                    try:
                        doc_structure = parse_legal_document(result.input_document_path)
                        stage_result.data["legal_structure"] = {
                            "title": doc_structure.title,
                            "sections_count": len(doc_structure.sections),
                            "requirements_count": len(doc_structure.requirements),
                            "authors_count": len(doc_structure.authors),
                            "whereas_clauses_count": len(doc_structure.whereas_clauses)
                        }
                        stage_result.metrics["legal_requirements_found"] = len(doc_structure.requirements)
                        
                    except Exception as e:
                        stage_result.warnings.append(f"Legal structure analysis failed: {str(e)}")
                        
                except Exception as e:
                    stage_result.warnings.append(f"Document text extraction failed: {str(e)}")
            
            # Performance assessment
            if doc_size > 5 * 1024 * 1024:  # 5MB
                stage_result.warnings.append("Large document detected - processing may take longer")
                
            estimated_paragraphs = stage_result.data.get("document_paragraphs_estimated", 0)
            if estimated_paragraphs > 300:
                stage_result.warnings.append(f"Complex document with {estimated_paragraphs} paragraphs - enabling performance optimizations")
            
            stage_result.success = True
            
        except Exception as e:
            stage_result.errors.append(f"Document analysis error: {str(e)}")
        
        return self._finalize_stage_result(stage_result)
    
    def _run_fallback_processing_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Process fallback document requirements using Phase 2.1"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.FALLBACK_PROCESSING,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        if not result.fallback_document_path or not PHASE_COMPONENTS_AVAILABLE:
            stage_result.status = ProcessingStatus.SKIPPED
            stage_result.success = True
            return self._finalize_stage_result(stage_result)
        
        try:
            print("Processing fallback document requirements...")
            
            # Extract fallback requirements using Phase 2.1
            processed_requirements = self.requirements_processor.process_fallback_requirements(
                result.fallback_document_path
            )
            
            result.requirements_extracted = len(processed_requirements)
            stage_result.data["processed_requirements"] = processed_requirements
            stage_result.metrics["requirements_extracted"] = len(processed_requirements)
            
            # Categorize requirements
            categories = {}
            priorities = {}
            
            for req in processed_requirements:
                category = req.category.value
                priority = req.priority_level.name
                
                categories[category] = categories.get(category, 0) + 1
                priorities[priority] = priorities.get(priority, 0) + 1
            
            stage_result.data["requirement_categories"] = categories
            stage_result.data["requirement_priorities"] = priorities
            stage_result.metrics["critical_high_requirements"] = priorities.get("CRITICAL", 0) + priorities.get("HIGH", 0)
            
            # Check for conflicts
            conflicts = sum(1 for req in processed_requirements if req.conflicts)
            stage_result.metrics["requirements_with_conflicts"] = conflicts
            
            if conflicts > 0:
                stage_result.warnings.append(f"Found {conflicts} requirements with conflicts - will be resolved in merging stage")
            
            print(f"Fallback processing complete: {len(processed_requirements)} requirements extracted")
            stage_result.success = True
            
        except Exception as e:
            error_msg = f"Fallback processing error: {str(e)}"
            print(error_msg)
            stage_result.errors.append(error_msg)
        
        return self._finalize_stage_result(stage_result)
    
    def _run_instruction_merging_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Advanced instruction merging using Phase 2.2"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.INSTRUCTION_MERGING,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        if not result.fallback_document_path or not PHASE_COMPONENTS_AVAILABLE:
            stage_result.status = ProcessingStatus.SKIPPED
            stage_result.success = True
            return self._finalize_stage_result(stage_result)
        
        try:
            print("Starting advanced instruction merging (Phase 2.2)...")
            
            # Use Phase 2.2 advanced merging
            merge_result = self.instruction_merger.merge_instructions(
                result.fallback_document_path,
                result.user_instructions
            )
            
            result.requirements_merged = len(merge_result.merged_requirements)
            result.legal_coherence_score = merge_result.legal_coherence_score
            
            stage_result.data["merge_result"] = merge_result
            stage_result.metrics.update({
                "merged_requirements": len(merge_result.merged_requirements),
                "unresolved_conflicts": len(merge_result.unresolved_conflicts),
                "user_overrides": len(merge_result.user_overrides),
                "validation_warnings": len(merge_result.validation_warnings),
                "legal_coherence_score": merge_result.legal_coherence_score
            })
            
            # Generate final instructions for LLM
            final_instructions = self.instruction_merger.generate_merged_instructions_for_llm(merge_result)
            stage_result.data["final_instructions"] = final_instructions
            stage_result.data["final_instructions_length"] = len(final_instructions)
            
            # Quality assessment
            high_confidence = len([r for r in merge_result.merged_requirements if r.confidence_score >= 0.8])
            low_confidence = len([r for r in merge_result.merged_requirements if r.confidence_score < 0.6])
            
            stage_result.metrics["high_confidence_requirements"] = high_confidence
            stage_result.metrics["low_confidence_requirements"] = low_confidence
            
            if merge_result.legal_coherence_score < 0.7:
                stage_result.warnings.append(f"Low legal coherence score: {merge_result.legal_coherence_score:.2f}")
            
            if len(merge_result.unresolved_conflicts) > 0:
                stage_result.warnings.append(f"{len(merge_result.unresolved_conflicts)} unresolved conflicts remain")
            
            print(f"Instruction merging complete: {len(merge_result.merged_requirements)} requirements merged")
            print(f"Legal coherence score: {merge_result.legal_coherence_score:.2f}")
            
            stage_result.success = True
            
        except Exception as e:
            error_msg = f"Instruction merging error: {str(e)}"
            print(error_msg)
            stage_result.errors.append(error_msg)
        
        return self._finalize_stage_result(stage_result)
    
    def _run_llm_processing_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Generate LLM suggestions from final instructions"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.LLM_PROCESSING,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        try:
            from .word_processor import extract_text_for_llm
            
            # Extract document text
            doc_text = extract_text_for_llm(result.input_document_path)
            
            # Determine instructions to use
            instructions_to_use = result.user_instructions
            
            # Check if we have merged instructions from Phase 2.2 (fallback workflow)
            for stage_res in result.stage_results:
                if stage_res.stage == WorkflowStage.INSTRUCTION_MERGING and stage_res.success:
                    merged_instructions = stage_res.data.get("final_instructions")
                    if merged_instructions:
                        instructions_to_use = merged_instructions
                        stage_result.data["using_merged_instructions"] = True
                        print("✅ ENHANCED WORKFLOW: Using Phase 2.2 merged instructions (fallback + user)")
                        print(f"   Merged instructions length: {len(merged_instructions)} characters")
                        break
            
            if not stage_result.data.get("using_merged_instructions"):
                stage_result.data["using_merged_instructions"] = False
                print("✅ ORIGINAL WORKFLOW: Using simple user instructions only (backward compatible)")
                print(f"   User instructions length: {len(instructions_to_use)} characters")
            
            # Get LLM suggestions
            print("Requesting LLM suggestions...")
            edits = get_llm_suggestions(
                doc_text, 
                instructions_to_use, 
                os.path.basename(result.input_document_path)
            )
            
            if edits is None:
                stage_result.errors.append("LLM returned None for suggestions")
                return self._finalize_stage_result(stage_result)
            
            result.edits_suggested = len(edits)
            stage_result.data["edits"] = edits
            stage_result.metrics["edits_suggested"] = len(edits)
            stage_result.data["instructions_length"] = len(instructions_to_use)
            
            # Analyze edit types
            edit_types = {}
            for edit in edits:
                edit_type = "replacement" if edit.get("specific_new_text") else "deletion"
                edit_types[edit_type] = edit_types.get(edit_type, 0) + 1
            
            stage_result.data["edit_types"] = edit_types
            
            print(f"LLM processing complete: {len(edits)} suggestions generated")
            stage_result.success = True
            
        except Exception as e:
            error_msg = f"LLM processing error: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            stage_result.errors.append(error_msg)
        
        return self._finalize_stage_result(stage_result)
    
    def _run_document_modification_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Apply edits to document using word processor"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.DOCUMENT_MODIFICATION,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        try:
            # Get edits from LLM processing stage
            edits = None
            for stage_res in result.stage_results:
                if stage_res.stage == WorkflowStage.LLM_PROCESSING and stage_res.success:
                    edits = stage_res.data.get("edits")
                    break
            
            if not edits:
                stage_result.errors.append("No edits available from LLM processing")
                return self._finalize_stage_result(stage_result)
            
            # Apply edits using word processor
            print(f"Applying {len(edits)} edits to document...")
            
            wp_success, log_file_path, log_details, processed_edits_count = process_document_with_edits(
                input_docx_path=result.input_document_path,
                output_docx_path=result.output_document_path,
                edits_to_make=edits,
                author_name=result.processing_settings.get("author_name", DEFAULT_AUTHOR_NAME),
                debug_mode_flag=False,
                extended_debug_mode_flag=False,
                case_sensitive_flag=True,
                add_comments_param=True
            )
            
            result.edits_applied = processed_edits_count
            
            stage_result.data.update({
                "word_processor_success": wp_success,
                "log_file_path": log_file_path,
                "log_details": log_details,
                "edits_applied": processed_edits_count,
                "edits_suggested": len(edits)
            })
            
            stage_result.metrics.update({
                "edits_applied": processed_edits_count,
                "application_success_rate": processed_edits_count / len(edits) if edits else 0,
                "processing_issues": len(log_details) if log_details else 0
            })
            
            # Read log content
            log_content = ""
            if log_file_path and os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    log_content = f.read()
            elif log_details:
                log_content = "\n".join(
                    f"Type: {d.get('type', 'Log')}, Issue: {d.get('issue', 'N/A')}"
                    for d in log_details
                )
            
            result.log_content = log_content
            result.issues_count = len(log_details) if log_details else 0
            
            if not wp_success:
                stage_result.errors.append("Word processor reported failure")
                return self._finalize_stage_result(stage_result)
            
            # Verify output file was created
            if not os.path.exists(result.output_document_path):
                stage_result.errors.append("Output document was not created")
                return self._finalize_stage_result(stage_result)
            
            print(f"Document modification complete: {processed_edits_count}/{len(edits)} edits applied")
            stage_result.success = True
            
        except Exception as e:
            error_msg = f"Document modification error: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            stage_result.errors.append(error_msg)
        
        return self._finalize_stage_result(stage_result)
    
    def _run_validation_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Validate processed document for legal meaning preservation"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.VALIDATION,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        try:
            validation_results = {}
            
            # Basic file validation
            if os.path.exists(result.output_document_path):
                output_size = os.path.getsize(result.output_document_path)
                input_size = os.path.getsize(result.input_document_path)
                
                size_change_percent = ((output_size - input_size) / input_size) * 100
                validation_results["file_size_change_percent"] = size_change_percent
                
                if abs(size_change_percent) > 50:
                    stage_result.warnings.append(f"Large file size change: {size_change_percent:.1f}%")
            else:
                stage_result.errors.append("Output document not found for validation")
                return self._finalize_stage_result(stage_result)
            
            # Legal coherence validation from Phase 2.2
            coherence_score = result.legal_coherence_score
            validation_results["legal_coherence_score"] = coherence_score
            
            if coherence_score > 0:
                if coherence_score >= 0.8:
                    validation_results["legal_coherence_status"] = "high"
                elif coherence_score >= 0.6:
                    validation_results["legal_coherence_status"] = "medium"
                    stage_result.warnings.append(f"Medium legal coherence: {coherence_score:.2f}")
                else:
                    validation_results["legal_coherence_status"] = "low"
                    stage_result.warnings.append(f"Low legal coherence: {coherence_score:.2f}")
            
            # Edit application validation
            if result.edits_suggested > 0:
                application_rate = result.edits_applied / result.edits_suggested
                validation_results["edit_application_rate"] = application_rate
                
                if application_rate < 0.7:
                    stage_result.warnings.append(f"Low edit application rate: {application_rate:.1%}")
            
            # Processing issues validation
            if result.issues_count > 0:
                validation_results["processing_issues_count"] = result.issues_count
                if result.issues_count > 5:
                    stage_result.warnings.append(f"High number of processing issues: {result.issues_count}")
            
            result.validation_results = validation_results
            stage_result.data["validation_results"] = validation_results
            
            print(f"Validation complete: {len(stage_result.warnings)} warnings")
            stage_result.success = True
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            print(error_msg)
            stage_result.errors.append(error_msg)
        
        return self._finalize_stage_result(stage_result)
    
    def _run_finalization_stage(self, result: LegalDocumentWorkflowResult) -> WorkflowStageResult:
        """Finalize workflow with status message and cleanup"""
        
        stage_start = datetime.now()
        stage_result = WorkflowStageResult(
            stage=WorkflowStage.FINALIZATION,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=stage_start,
            end_time=None,
            duration_seconds=0.0,
            success=False,
            data={},
            errors=[],
            warnings=[],
            metrics={}
        )
        
        try:
            # Generate status message
            if result.edits_suggested == 0:
                result.status_message = "Processing complete. No changes were suggested."
            elif result.edits_applied == result.edits_suggested:
                result.status_message = f"Processing complete. All {result.edits_applied} suggested changes were successfully applied."
                if result.fallback_document_path:
                    result.status_message += f" (Using Phase 2.2 advanced merging with coherence score: {result.legal_coherence_score:.2f})"
            else:
                result.status_message = f"Processing complete. {result.edits_applied} out of {result.edits_suggested} suggested changes were applied."
                if result.issues_count > 0:
                    result.status_message += f" {result.issues_count} issues encountered."
            
            # Final audit log entry
            if result.audit_log_path:
                self._log_audit_event(result.audit_log_path, "WORKFLOW_COMPLETE", {
                    "overall_status": result.overall_status.value,
                    "requirements_extracted": result.requirements_extracted,
                    "requirements_merged": result.requirements_merged,
                    "edits_suggested": result.edits_suggested,
                    "edits_applied": result.edits_applied,
                    "legal_coherence_score": result.legal_coherence_score,
                    "issues_count": result.issues_count
                })
            
            stage_result.data["status_message"] = result.status_message
            stage_result.success = True
            
            print(f"Workflow finalization complete: {result.status_message}")
            
        except Exception as e:
            error_msg = f"Finalization error: {str(e)}"
            print(error_msg)
            stage_result.errors.append(error_msg)
        
        return self._finalize_stage_result(stage_result)
    
    def _finalize_stage_result(self, stage_result: WorkflowStageResult) -> WorkflowStageResult:
        """Finalize a stage result with timing and status"""
        stage_result.end_time = datetime.now()
        stage_result.duration_seconds = (stage_result.end_time - stage_result.start_time).total_seconds()
        
        if stage_result.success and not stage_result.errors:
            stage_result.status = ProcessingStatus.COMPLETED
        elif stage_result.errors:
            stage_result.status = ProcessingStatus.FAILED
        
        return stage_result
    
    def _finalize_result(self, result: LegalDocumentWorkflowResult) -> LegalDocumentWorkflowResult:
        """Finalize the complete workflow result"""
        result.end_time = datetime.now()
        result.total_duration_seconds = (result.end_time - result.start_time).total_seconds()
        
        print(f"Legal document workflow complete: {result.workflow_id}")
        print(f"Total duration: {result.total_duration_seconds:.1f} seconds")
        print(f"Final status: {result.overall_status.value}")
        
        return result
    
    def _create_audit_log(self, workflow_id: str) -> str:
        """Create audit log file for workflow"""
        audit_log_path = os.path.join(self.temp_dir, f"audit_log_{workflow_id}.json")
        
        initial_log = {
            "workflow_id": workflow_id,
            "created_at": datetime.now().isoformat(),
            "events": []
        }
        
        with open(audit_log_path, 'w') as f:
            json.dump(initial_log, f, indent=2)
        
        return audit_log_path
    
    def _log_audit_event(self, audit_log_path: str, event_type: str, event_data: Dict[str, Any]):
        """Add event to audit log"""
        if not os.path.exists(audit_log_path):
            return
        
        try:
            with open(audit_log_path, 'r') as f:
                log_data = json.load(f)
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": event_data
            }
            
            log_data["events"].append(event)
            
            with open(audit_log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"Error writing audit log: {e}")

# Convenience function for integration
def process_legal_document_workflow(input_document_path: str,
                                  user_instructions: str,
                                  fallback_document_path: Optional[str] = None,
                                  author_name: Optional[str] = None,
                                  enable_audit_logging: bool = True,
                                  enable_backup: bool = True,
                                  enable_validation: bool = True) -> LegalDocumentWorkflowResult:
    """
    Convenience function for end-to-end legal document processing
    
    Args:
        input_document_path: Path to input document
        user_instructions: User's modification instructions
        fallback_document_path: Optional fallback document path
        author_name: Author name for tracked changes
        enable_audit_logging: Enable comprehensive audit logging
        enable_backup: Enable document backup
        enable_validation: Enable legal validation
        
    Returns:
        Complete workflow result
    """
    
    processor = LegalDocumentProcessor(
        enable_audit_logging=enable_audit_logging,
        enable_backup=enable_backup,
        enable_validation=enable_validation
    )
    
    return processor.process_legal_document(
        input_document_path=input_document_path,
        user_instructions=user_instructions,
        fallback_document_path=fallback_document_path,
        author_name=author_name
    )

if __name__ == "__main__":
    # Test the workflow orchestrator
    print("Phase 4.1 Legal Workflow Orchestrator - Test Mode")
    print("This module provides end-to-end legal document processing with comprehensive validation.")
    print("Use process_legal_document_workflow() function for complete processing.")