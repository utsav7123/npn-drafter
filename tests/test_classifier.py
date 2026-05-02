"""
Test the classifier with known test cases.
"""

import pytest
from agent.classifier import classify_product


class TestClassifier:
    
    def test_class1_simple_vitamin_d(self):
        """Single ingredient, single monograph = Class 1"""
        spec = {
            "product_name": "Vitamin D3",
            "medicinal_ingredients": [
                {"name": "Cholecalciferol", "dose": 1000, "unit": "IU"}
            ]
        }
        result = classify_product(spec)
        assert result["class"] == 1
        assert "vitamin_d" in result["matched_monographs"]
        assert len(result["unmatched_ingredients"]) == 0
    
    def test_class1_calcium(self):
        """Single ingredient, single monograph = Class 1"""
        spec = {
            "product_name": "Calcium Supplement",
            "medicinal_ingredients": [
                {"name": "Calcium carbonate", "dose": 500, "unit": "mg"}
            ]
        }
        result = classify_product(spec)
        assert result["class"] == 1
        assert "calcium" in result["matched_monographs"]
    
    def test_class2_calcium_and_d(self):
        """Two ingredients, two monographs = Class 2"""
        spec = {
            "product_name": "Calcium + D3",
            "medicinal_ingredients": [
                {"name": "Calcium carbonate", "dose": 500, "unit": "mg"},
                {"name": "Cholecalciferol", "dose": 400, "unit": "IU"}
            ]
        }
        result = classify_product(spec)
        assert result["class"] == 2
        assert "calcium" in result["matched_monographs"]
        assert "vitamin_d" in result["matched_monographs"]
        assert len(result["matched_monographs"]) == 2
    
    def test_class3_unmatched_ingredient(self):
        """Unknown ingredient = Class 3"""
        spec = {
            "product_name": "Novel Product",
            "medicinal_ingredients": [
                {"name": "Novel botanical extract XYZ", "dose": 100, "unit": "mg"}
            ]
        }
        result = classify_product(spec)
        assert result["class"] == 3
        assert len(result["unmatched_ingredients"]) > 0
        assert "xyzunmatched" in result["reasoning"].lower() or "unmatched" in result["reasoning"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
