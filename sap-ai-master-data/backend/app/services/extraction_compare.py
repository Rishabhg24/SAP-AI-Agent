"""
Extraction Comparison and Consensus Engine.
Compares JSON results from Extractor 1, 2, and 3.
Calculates field-level agreement, flags conflicts, and calculates overall confidence.
"""
from typing import Any, Dict, List, Optional
from app.models.extraction import (
    ConflictStatus,
    ExtractionComparisonResult,
    FieldComparison,
    MasterDataType,
    SingleExtractorOutput
)
from app.utils.logging import logger

class ExtractionComparator:
    @staticmethod
    def compare_extractions(
        outputs: List[SingleExtractorOutput],
        user_corrections: Optional[Dict[str, Any]] = None
    ) -> ExtractionComparisonResult:
        """
        Compare outputs of 3 extraction methods.
        Field-by-field consensus logic:
        - If all non-null extracted values match -> AGREED
        - If values differ -> CONFLICT
        - If only 1 extractor found a value -> PARTIAL / AGREED (with confidence penalty)
        - If user provided a correction -> RESOLVED
        """
        user_corrections = user_corrections or {}
        
        # Collect all active methods
        successful_outputs = [o for o in outputs if o.success]
        if not successful_outputs:
            return ExtractionComparisonResult(
                status=ConflictStatus.CONFLICT,
                master_type=MasterDataType.UNKNOWN,
                overall_confidence=0.0
            )

        # Detect dominant master_type
        type_votes = [o.master_type for o in successful_outputs if o.master_type != MasterDataType.UNKNOWN]
        dominant_type = max(set(type_votes), key=type_votes.count) if type_votes else MasterDataType.ITEM

        # Aggregate all unique field keys across extractors
        all_fields = set()
        for o in successful_outputs:
            all_fields.update(o.data.keys())

        field_comparisons: Dict[str, FieldComparison] = {}
        agreed_data: Dict[str, Any] = {}
        conflicts: List[FieldComparison] = []
        extra_fields: Dict[str, Any] = {}

        total_checked_fields = 0
        agreed_count = 0

        for field in sorted(all_fields):
            extracted_map: Dict[str, Any] = {}
            for o in successful_outputs:
                if field in o.data and o.data[field] is not None:
                    extracted_map[o.method] = o.data[field]

            # Get distinct values
            distinct_values = []
            for v in extracted_map.values():
                if v not in distinct_values:
                    distinct_values.append(v)

            total_checked_fields += 1

            # Check if user already provided a manual resolution for this field
            if field in user_corrections:
                resolved_val = user_corrections[field]
                fc = FieldComparison(
                    field_name=field,
                    status=ConflictStatus.AGREED,
                    agreed_value=resolved_val,
                    extracted_values=extracted_map,
                    distinct_values=distinct_values,
                    resolved_value=resolved_val,
                    is_resolved=True
                )
                field_comparisons[field] = fc
                agreed_data[field] = resolved_val
                agreed_count += 1
                continue

            if len(distinct_values) == 0:
                continue
            elif len(distinct_values) == 1:
                # All extractors agree
                consensus_val = distinct_values[0]
                fc = FieldComparison(
                    field_name=field,
                    status=ConflictStatus.AGREED,
                    agreed_value=consensus_val,
                    extracted_values=extracted_map,
                    distinct_values=distinct_values,
                    resolved_value=consensus_val,
                    is_resolved=True
                )
                field_comparisons[field] = fc
                agreed_data[field] = consensus_val
                agreed_count += 1
            else:
                # Disagreement detected!
                fc = FieldComparison(
                    field_name=field,
                    status=ConflictStatus.CONFLICT,
                    agreed_value=None,
                    extracted_values=extracted_map,
                    distinct_values=distinct_values,
                    resolved_value=None,
                    is_resolved=False
                )
                field_comparisons[field] = fc
                conflicts.append(fc)
                logger.warning(f"Extraction conflict on field '{field}': {distinct_values}")

        # Calculate overall confidence
        confidence = (agreed_count / max(1, total_checked_fields)) if total_checked_fields > 0 else 1.0
        overall_status = ConflictStatus.CONFLICT if conflicts else ConflictStatus.AGREED

        # Collect extracted records from methods (e.g. from tabular extraction)
        all_records = []
        for o in successful_outputs:
            if o.records and len(o.records) > len(all_records):
                all_records = o.records

        total_records = len(all_records) if all_records else 1

        return ExtractionComparisonResult(
            status=overall_status,
            master_type=dominant_type,
            overall_confidence=round(confidence, 2),
            field_comparisons=field_comparisons,
            agreed_data=agreed_data,
            conflicts=conflicts,
            extra_fields=extra_fields,
            all_records=all_records,
            total_records=total_records
        )

extraction_comparator = ExtractionComparator()
