"""
Classifier: Determines if a product qualifies as Class 1, 2, or 3.

Class 1: All ingredients are covered by a SINGLE monograph.
Class 2: All ingredients are covered but ACROSS MULTIPLE monographs.
Class 3: Some ingredients are not covered by any monograph (require novel evidence).
"""

import os
import json
from typing import Dict, List
from anthropic import Anthropic


def load_available_monographs() -> List[str]:
    """Load list of available monograph IDs."""
    monograph_dir = "monographs"
    monographs = []
    if os.path.exists(monograph_dir):
        for filename in os.listdir(monograph_dir):
            if filename.endswith(".json"):
                monographs.append(filename.replace(".json", ""))
    return monographs


def classify_product(product_spec: Dict) -> Dict:
    """
    Classify a product as Class 1, 2, or 3 based on ingredient monograph coverage.
    
    Args:
        product_spec: Dict with keys like:
            - product_name: str
            - medicinal_ingredients: List[Dict] with 'name', 'dose', 'unit'
            - non_medicinal_ingredients: List[str]
            - intended_use: str
    
    Returns:
        Dict with keys:
            - class: int (1, 2, or 3)
            - reasoning: str
            - matched_monographs: List[str]
            - unmatched_ingredients: List[str]
    """
    
    available_monographs = load_available_monographs()
    medicinal_ingredients = [ing.get("name", "").lower() for ing in product_spec.get("medicinal_ingredients", [])]
    
    matched_ingredients = {}  # ingredient -> monograph_id
    unmatched = []
    
    # Simple rule-based matching: look for substring matches and known aliases
    ingredient_to_monograph = {
        "vitamin d": "vitamin_d",
        "cholecalciferol": "vitamin_d",
        "ergocalciferol": "vitamin_d",
        "d3": "vitamin_d",
        "d2": "vitamin_d",
        
        "calcium": "calcium",
        
        "vitamin c": "vitamin_c",
        "ascorbic acid": "vitamin_c",
        "ascorbate": "vitamin_c",
        
        "magnesium": "magnesium",
        
        "multi-vitamin": "multi_vitamin_mineral",
        "multivitamin": "multi_vitamin_mineral",
    }
    
    for ingredient in medicinal_ingredients:
        matched = False
        for key, monograph_id in ingredient_to_monograph.items():
            if key in ingredient.lower():
                matched_ingredients[ingredient] = monograph_id
                matched = True
                break
        
        if not matched:
            unmatched.append(ingredient)
    
    # Determine classification
    if unmatched:
        return {
            "class": 3,
            "reasoning": f"Unmatched ingredients require novel evidence: {', '.join(unmatched)}",
            "matched_monographs": list(set(matched_ingredients.values())),
            "unmatched_ingredients": unmatched,
        }
    
    matched_monographs = list(set(matched_ingredients.values()))
    
    if len(matched_monographs) == 1:
        return {
            "class": 1,
            "reasoning": f"All ingredients covered by single monograph: {matched_monographs[0]}",
            "matched_monographs": matched_monographs,
            "unmatched_ingredients": [],
        }
    else:
        return {
            "class": 2,
            "reasoning": f"All ingredients covered but across multiple monographs: {', '.join(matched_monographs)}",
            "matched_monographs": matched_monographs,
            "unmatched_ingredients": [],
        }


def classify_with_llm_backup(product_spec: Dict, api_key: str) -> Dict:
    """
    Use LLM as backup for complex cases where rules are ambiguous.
    Falls back to LLM if rules-based classification is not confident.
    """
    
    # First try rules-based
    rules_result = classify_product(product_spec)
    
    # Use LLM only if Class 2 or 3 (more ambiguous cases)
    if rules_result["class"] in [2, 3]:
        try:
            client = Anthropic(api_key=api_key)
            
            available_monographs = load_available_monographs()
            
            with open("prompts/classifier_prompt.txt", "r") as f:
                prompt_template = f.read()
            
            prompt = prompt_template.format(
                product_spec=json.dumps(product_spec, indent=2),
                available_monographs=", ".join(available_monographs),
                rules_classification=json.dumps(rules_result, indent=2)
            )
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Parse JSON response from LLM
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    llm_result = json.loads(json_match.group())
                    return llm_result
            except json.JSONDecodeError:
                pass
        except Exception as e:
            print(f"LLM backup failed: {e}. Using rules-based result.")
    
    return rules_result


if __name__ == "__main__":
    # Test the classifier
    test_spec = {
        "product_name": "Vitamin D Supplement",
        "medicinal_ingredients": [
            {"name": "Cholecalciferol", "dose": 1000, "unit": "IU"}
        ],
        "non_medicinal_ingredients": ["Microcrystalline cellulose"],
        "intended_use": "Supports bone and immune health"
    }
    
    result = classify_product(test_spec)
    print("Classification result:", json.dumps(result, indent=2))
