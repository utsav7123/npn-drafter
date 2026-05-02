"""
Test the drafter can generate a reasonable structure.
Uses mocking to avoid LLM calls.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from agent.drafter import create_template_draft


class TestDrafter:
    
    def test_template_draft_structure(self):
        """Template draft should produce the expected JSON structure"""
        spec = {
            "product_name": "Test Vitamin D",
            "medicinal_ingredients": [
                {"name": "Cholecalciferol", "source": "from lanolin", "dose": 1000, "unit": "IU"}
            ],
            "non_medicinal_ingredients": ["Cellulose"],
            "intended_use": "Bone health"
        }
        
        monographs = {
            "vitamin_d": {
                "name": "Vitamin D",
                "allowed_claims": ["Helps in the development and maintenance of bones and teeth."],
                "duration_of_use": "Long-term use",
                "risk_information": {"cautions": ["Consult practitioner"]}
            }
        }
        
        draft = create_template_draft(spec, monographs)
        
        # Verify structure
        assert "product_name" in draft
        assert "medicinal_ingredients" in draft
        assert "claims" in draft
        assert "monographs_referenced" in draft
        assert draft["monograph_class"] in [1, 2, 3]
        
        # Verify it's JSON-serializable
        json_str = json.dumps(draft)
        assert len(json_str) > 0
    
    def test_template_draft_populates_ingredients(self):
        """Template draft should populate medicinal ingredients from spec"""
        spec = {
            "product_name": "Multi Test",
            "medicinal_ingredients": [
                {"name": "Calcium", "source": "carbonate", "dose": 500, "unit": "mg"},
                {"name": "Vitamin D", "source": "lanolin", "dose": 400, "unit": "IU"}
            ],
            "non_medicinal_ingredients": []
        }
        
        monographs = {
            "calcium": {"allowed_claims": []},
            "vitamin_d": {"allowed_claims": []}
        }
        
        draft = create_template_draft(spec, monographs)
        
        assert len(draft["medicinal_ingredients"]) == 2
        assert any("Calcium" in ing["ingredient"] for ing in draft["medicinal_ingredients"])
        assert any("Vitamin D" in ing["ingredient"] for ing in draft["medicinal_ingredients"])
    
    def test_draft_includes_metadata(self):
        """Draft should include LLM/generation metadata"""
        spec = {
            "product_name": "Test",
            "medicinal_ingredients": [{"name": "Vitamin C"}]
        }
        
        monographs = {
            "vitamin_c": {
                "allowed_claims": ["Antioxidant"]
            }
        }
        
        draft = create_template_draft(spec, monographs)
        
        # Check for metadata
        assert "_meta" in draft
        meta = draft["_meta"]
        assert "source" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
