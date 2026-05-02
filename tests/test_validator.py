"""
Test the validator catches known bad inputs.
"""

import pytest
from agent.validator import validate_application


class TestValidator:
    
    def test_valid_draft_passes(self):
        """A well-formed draft should pass validation"""
        draft = {
            "product_name": "Vitamin D",
            "applicant_info": "Applicant",
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
            "non_medicinal_ingredients": ["Cellulose"],
            "recommended_use": "Supports bone health",
            "recommended_dose": {"description": "1 tablet daily"},
            "duration_of_use": "Long-term",
            "risk_information": {"cautions": ["Consult practitioner"]},
            "claims": ["Helps in the development and maintenance of bones and teeth."],
            "monograph_class": 1,
            "monographs_referenced": ["vitamin_d"]
        }
        
        monographs = {
            "vitamin_d": {
                "name": "Vitamin D",
                "allowed_claims": ["Helps in the development and maintenance of bones and teeth."],
                "dose_range": {"min_iu_per_day": 200, "max_iu_per_day": 2500}
            }
        }
        
        result = validate_application(draft, monographs)
        assert result["valid"] is True
        assert result["error_count"] == 0
    
    def test_dose_exceeds_max(self):
        """Validator should catch dose above maximum"""
        draft = {
            "product_name": "Too Strong Vitamin D",
            "medicinal_ingredients": [
                {
                    "ingredient": "Cholecalciferol",
                    "dose": "5000 IU",
                    "dose_numeric": 5000,
                    "dose_unit": "iu",
                    "monograph_reference": "vitamin_d"
                }
            ],
            "recommended_use": "Bone health",
            "claims": ["Helps in the development and maintenance of bones and teeth."],
            "monograph_class": 1,
            "monographs_referenced": ["vitamin_d"]
        }
        
        monographs = {
            "vitamin_d": {
                "allowed_claims": ["Helps in the development and maintenance of bones and teeth."],
                "dose_range": {"min_iu_per_day": 200, "max_iu_per_day": 2500}
            }
        }
        
        result = validate_application(draft, monographs)
        assert result["valid"] is False
        assert any(i["severity"] == "WARNING" and "above maximum" in i["message"] for i in result["issues"])
    
    def test_hallucinated_claim(self):
        """Validator should catch claims not in monograph"""
        draft = {
            "product_name": "Bad Claims",
            "medicinal_ingredients": [
                {
                    "ingredient": "Cholecalciferol",
                    "dose": "1000 IU",
                    "dose_numeric": 1000,
                    "dose_unit": "iu",
                    "monograph_reference": "vitamin_d"
                }
            ],
            "recommended_use": "Bone health",
            "claims": [
                "Helps in the development and maintenance of bones and teeth.",
                "Cures bone cancer",  # HALLUCINATED
                "Makes you run faster"  # HALLUCINATED
            ],
            "monograph_class": 1,
            "monographs_referenced": ["vitamin_d"]
        }
        
        monographs = {
            "vitamin_d": {
                "allowed_claims": ["Helps in the development and maintenance of bones and teeth."]
            }
        }
        
        result = validate_application(draft, monographs)
        assert result["valid"] is False
        assert result["error_count"] >= 2
        assert any("not found in monograph" in i["message"] for i in result["issues"])
    
    def test_missing_required_fields(self):
        """Validator should catch missing required fields"""
        draft = {
            "product_name": "Incomplete",
            "medicinal_ingredients": [
                {"ingredient": "Vitamin D", "dose": "1000 IU"}
            ]
            # Missing: recommended_use, claims, monographs_referenced, etc.
        }
        
        result = validate_application(draft, {})
        assert result["valid"] is False
        assert any("Required field" in i["message"] for i in result["issues"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
