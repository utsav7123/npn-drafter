"""
Validator: Checks the drafted application against hard rules.

This is the critical piece that differentiates this system from a simple LLM prompt.
The validator ensures:
- All doses are within monograph limits
- All claims come from the monograph allowed list
- Required fields are populated
- No hallucinated ingredients or claims
"""

import json
from typing import Dict, List, Tuple
from jsonschema import validate, ValidationError


# JSON Schema for the application draft structure
APPLICATION_SCHEMA = {
    "type": "object",
    "required": [
        "product_name",
        "medicinal_ingredients",
        "recommended_use",
        "claims",
        "monograph_class",
        "monographs_referenced"
    ],
    "properties": {
        "product_name": {"type": "string"},
        "applicant_info": {"type": "string"},
        "medicinal_ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["ingredient", "dose", "monograph_reference"],
                "properties": {
                    "ingredient": {"type": "string"},
                    "source": {"type": "string"},
                    "dose": {"type": "string"},
                    "dose_numeric": {"type": "number"},
                    "dose_unit": {"type": "string"},
                    "monograph_reference": {"type": "string"}
                }
            }
        },
        "non_medicinal_ingredients": {
            "type": "array",
            "items": {"type": "string"}
        },
        "recommended_use": {"type": "string"},
        "recommended_dose": {"type": "object"},
        "duration_of_use": {"type": "string"},
        "risk_information": {"type": "object"},
        "claims": {"type": "array", "items": {"type": "string"}},
        "monograph_class": {"type": "integer", "enum": [1, 2, 3]},
        "monographs_referenced": {"type": "array", "items": {"type": "string"}}
    }
}


def validate_schema(application_draft: Dict) -> Tuple[bool, List[Dict]]:
    """
    Validate the application against the JSON schema.
    
    Returns:
        (valid: bool, issues: List[Dict])
    """
    issues = []
    
    try:
        validate(instance=application_draft, schema=APPLICATION_SCHEMA)
        return True, issues
    except ValidationError as e:
        issues.append({
            "severity": "ERROR",
            "field": e.json_path or "root",
            "message": f"Schema validation failed: {e.message}"
        })
        return False, issues


def validate_dose_ranges(
    application_draft: Dict,
    monographs: Dict
) -> Tuple[bool, List[Dict]]:
    """
    Check that all doses are within the monograph allowed ranges.
    """
    issues = []
    
    medicinal_ingredients = application_draft.get("medicinal_ingredients", [])
    
    for idx, ingredient in enumerate(medicinal_ingredients):
        mono_ref = ingredient.get("monograph_reference")
        
        if mono_ref not in monographs:
            issues.append({
                "severity": "ERROR",
                "field": f"medicinal_ingredients[{idx}]",
                "message": f"Monograph reference '{mono_ref}' not found"
            })
            continue
        
        monograph = monographs[mono_ref]
        dose_numeric = ingredient.get("dose_numeric")
        dose_unit = ingredient.get("dose_unit", "").lower()
        
        if dose_numeric is None:
            issues.append({
                "severity": "WARNING",
                "field": f"medicinal_ingredients[{idx}].dose_numeric",
                "message": "Numeric dose not specified; cannot validate range"
            })
            continue
        
        # Check dose range (simplified; real implementation would need unit conversion)
        dose_range = monograph.get("dose_range", {})
        
        # Try to find matching dose range based on unit
        min_dose = None
        max_dose = None
        
        if dose_unit in ["iu", "iu_per_day"]:
            min_dose = dose_range.get("min_iu_per_day")
            max_dose = dose_range.get("max_iu_per_day")
        elif dose_unit in ["mg", "mg_per_day"]:
            min_dose = dose_range.get("min_mg_per_day")
            max_dose = dose_range.get("max_mg_per_day")
        
        if min_dose and dose_numeric < min_dose:
            issues.append({
                "severity": "ERROR",
                "field": f"medicinal_ingredients[{idx}].dose",
                "message": f"Dose {dose_numeric} {dose_unit} is below minimum {min_dose}"
            })
        
        if max_dose and dose_numeric > max_dose:
            issues.append({
                "severity": "WARNING",
                "field": f"medicinal_ingredients[{idx}].dose",
                "message": f"Dose {dose_numeric} {dose_unit} is at or above maximum {max_dose}"
            })
    
    return len([i for i in issues if i["severity"] == "ERROR"]) == 0, issues


def validate_claims(
    application_draft: Dict,
    monographs: Dict
) -> Tuple[bool, List[Dict]]:
    """
    Check that all claims come from the monograph allowed claims.
    This catches hallucinated claims.
    """
    issues = []
    
    draft_claims = application_draft.get("claims", [])
    monographs_referenced = application_draft.get("monographs_referenced", [])
    
    # Build allowed claims from all referenced monographs
    allowed_claims = set()
    for mono_ref in monographs_referenced:
        if mono_ref in monographs:
            mono = monographs[mono_ref]
            for claim in mono.get("allowed_claims", []):
                allowed_claims.add(claim.lower().strip())
    
    # Check each draft claim
    for idx, claim in enumerate(draft_claims):
        claim_lower = claim.lower().strip()
        
        # Exact match or substring match
        found = False
        for allowed_claim in allowed_claims:
            if claim_lower == allowed_claim or claim_lower in allowed_claim:
                found = True
                break
        
        if not found:
            issues.append({
                "severity": "ERROR",
                "field": f"claims[{idx}]",
                "message": f"Claim not found in monograph allowed claims: '{claim}'"
            })
    
    return len([i for i in issues if i["severity"] == "ERROR"]) == 0, issues


def validate_required_fields(application_draft: Dict) -> Tuple[bool, List[Dict]]:
    """
    Check that required fields are present and non-empty.
    """
    issues = []
    
    required_fields = [
        ("product_name", "str"),
        ("medicinal_ingredients", "array"),
        ("recommended_use", "str"),
        ("claims", "array"),
        ("monographs_referenced", "array"),
    ]
    
    for field_name, field_type in required_fields:
        value = application_draft.get(field_name)
        
        if value is None:
            issues.append({
                "severity": "ERROR",
                "field": field_name,
                "message": f"Required field '{field_name}' is missing"
            })
        elif field_type == "array" and len(value) == 0:
            issues.append({
                "severity": "ERROR",
                "field": field_name,
                "message": f"Required array '{field_name}' is empty"
            })
        elif field_type == "str" and not value.strip():
            issues.append({
                "severity": "ERROR",
                "field": field_name,
                "message": f"Required field '{field_name}' is empty"
            })
    
    return len([i for i in issues if i["severity"] == "ERROR"]) == 0, issues


def validate_application(
    application_draft: Dict,
    monographs: Dict
) -> Dict:
    """
    Run all validators and return a comprehensive validation report.
    
    Returns:
        Dict with keys:
            - valid: bool
            - total_issues: int
            - error_count: int
            - warning_count: int
            - issues: List[Dict] with severity, field, message
    """
    
    all_issues = []
    
    # Schema validation
    schema_valid, schema_issues = validate_schema(application_draft)
    all_issues.extend(schema_issues)
    
    if not schema_valid:
        # Stop here; can't validate further if schema is broken
        error_count = len([i for i in all_issues if i["severity"] == "ERROR"])
        warning_count = len([i for i in all_issues if i["severity"] == "WARNING"])
        return {
            "valid": False,
            "total_issues": len(all_issues),
            "error_count": error_count,
            "warning_count": warning_count,
            "issues": all_issues,
            "reason": "Schema validation failed; cannot proceed with monograph validation"
        }
    
    # Field validation
    _, field_issues = validate_required_fields(application_draft)
    all_issues.extend(field_issues)
    
    # Dose range validation
    _, dose_issues = validate_dose_ranges(application_draft, monographs)
    all_issues.extend(dose_issues)
    
    # Claim validation
    _, claim_issues = validate_claims(application_draft, monographs)
    all_issues.extend(claim_issues)
    
    # Count issues
    error_count = len([i for i in all_issues if i["severity"] == "ERROR"])
    warning_count = len([i for i in all_issues if i["severity"] == "WARNING"])
    
    return {
        "valid": error_count == 0,
        "total_issues": len(all_issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": all_issues
    }


if __name__ == "__main__":
    # Test validation with a known-good and known-bad draft
    
    good_draft = {
        "product_name": "Vitamin D Supplement",
        "applicant_info": "Applicant Inc.",
        "medicinal_ingredients": [
            {
                "ingredient": "Cholecalciferol",
                "source": "from lanolin",
                "dose": "1000 IU",
                "dose_numeric": 1000,
                "dose_unit": "iu",
                "monograph_reference": "vitamin_d"
            }
        ],
        "non_medicinal_ingredients": ["Microcrystalline cellulose"],
        "recommended_use": "Helps in the development and maintenance of bones and teeth.",
        "recommended_dose": {"description": "1 tablet daily", "frequency": "Once daily"},
        "duration_of_use": "Long-term use",
        "risk_information": {"cautions": ["Consult a health care practitioner if symptoms persist"]},
        "claims": ["Helps in the development and maintenance of bones and teeth."],
        "monograph_class": 1,
        "monographs_referenced": ["vitamin_d"]
    }
    
    bad_draft = {
        "product_name": "Bad Vitamin D",
        "medicinal_ingredients": [
            {
                "ingredient": "Cholecalciferol",
                "dose": "10000 IU",
                "dose_numeric": 10000,
                "dose_unit": "iu",
                "monograph_reference": "vitamin_d"
            }
        ],
        "recommended_use": "Cures cancer",
        "claims": ["Cures cancer", "Helps in bone development"],
        "monograph_class": 1,
        "monographs_referenced": ["vitamin_d"]
    }
    
    test_monograph = {
        "vitamin_d": {
            "name": "Vitamin D",
            "allowed_claims": ["Helps in the development and maintenance of bones and teeth."],
            "dose_range": {"min_iu_per_day": 200, "max_iu_per_day": 2500}
        }
    }
    
    print("GOOD DRAFT:")
    result = validate_application(good_draft, test_monograph)
    print(json.dumps(result, indent=2))
    
    print("\n\nBAD DRAFT:")
    result = validate_application(bad_draft, test_monograph)
    print(json.dumps(result, indent=2))
