"""
Drafter: Uses Anthropic Claude to convert product spec + monographs into an application draft.

This is the core LLM integration. The Drafter receives:
- Product specification
- Matched monograph data

And produces:
- Structured application draft (JSON)
- Marked for validation and human review
"""

import json
import re
from typing import Dict, Optional
from anthropic import Anthropic


def draft_application(product_spec: Dict, monographs: Dict, api_key: str) -> Dict:
    """
    Use Claude to draft a NPN application.
    
    Args:
        product_spec: Product information (ingredients, intended use, etc.)
        monographs: Dict mapping monograph_id -> monograph data
        api_key: Anthropic API key
    
    Returns:
        Structured application draft as dict, or error dict if generation fails.
    """
    
    client = Anthropic(api_key=api_key)
    
    # Load the drafter prompt template
    try:
        with open("prompts/drafter_prompt.txt", "r") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        return {
            "error": "Drafter prompt not found at prompts/drafter_prompt.txt",
            "draft": None
        }
    
    # Format the prompt
    prompt = (
        prompt_template
        .replace("{product_spec}", json.dumps(product_spec, indent=2))
        .replace("{monographs}", json.dumps(monographs, indent=2))
    )
    
    try:
        # Call Claude
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        
        # Extract JSON from response
        # Look for {...} pattern in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            draft = json.loads(json_match.group())
            
            # Enrich with metadata
            draft["_meta"] = {
                "model": "claude-3-5-sonnet-20241022",
                "product_name": product_spec.get("product_name", "Unknown"),
                "monographs_used": list(monographs.keys()),
            }
            
            return {
                "error": None,
                "draft": draft
            }
        else:
            return {
                "error": "Could not extract JSON from LLM response",
                "response": response_text,
                "draft": None
            }
    
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON decode error: {str(e)}",
            "draft": None
        }
    
    except Exception as e:
        return {
            "error": f"LLM call failed: {str(e)}",
            "draft": None
        }


def draft_with_fallback(product_spec: Dict, monographs: Dict, api_key: str) -> Dict:
    """
    Attempt to draft, with fallback to a template if LLM fails.
    """
    result = draft_application(product_spec, monographs, api_key)
    
    if result["error"]:
        # Fallback: create a basic template
        fallback_draft = create_template_draft(product_spec, monographs)
        return {
            "error": result["error"],
            "draft": fallback_draft,
            "fallback": True
        }
    
    return result


def create_template_draft(product_spec: Dict, monographs: Dict) -> Dict:
    """
    Create a basic template draft when LLM is unavailable.
    """
    medicinal_ingredients = []
    
    for ing in product_spec.get("medicinal_ingredients", []):
        medicinal_ingredients.append({
            "ingredient": ing.get("name", ""),
            "source": ing.get("source", "Unknown source"),
            "dose": f"{ing.get('dose', 0)} {ing.get('unit', '')}",
            "dose_numeric": ing.get("dose", 0),
            "dose_unit": ing.get("unit", ""),
            "monograph_reference": list(monographs.keys())[0] if monographs else "unknown"
        })
    
    # Get first monograph's claims and risk info
    first_mono = list(monographs.values())[0] if monographs else {}
    allowed_claims = first_mono.get("allowed_claims", [])
    recommended_use = allowed_claims[0] if allowed_claims else "Product for health maintenance"
    
    return {
        "product_name": product_spec.get("product_name", "Natural Health Product"),
        "applicant_info": "Health Product Applicant",
        "medicinal_ingredients": medicinal_ingredients,
        "non_medicinal_ingredients": product_spec.get("non_medicinal_ingredients", []),
        "recommended_use": recommended_use,
        "recommended_dose": {
            "description": f"See monograph for {list(monographs.keys())[0] if monographs else 'product'}",
            "frequency": "As directed"
        },
        "duration_of_use": first_mono.get("duration_of_use", "As directed"),
        "risk_information": first_mono.get("risk_information", {}),
        "claims": allowed_claims[:3],
        "monograph_class": 1,
        "monographs_referenced": list(monographs.keys()),
        "_meta": {
            "source": "template_fallback",
            "reason": "LLM unavailable"
        }
    }


if __name__ == "__main__":
    # Test: requires ANTHROPIC_API_KEY env var
    import os
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        exit(1)
    
    test_spec = {
        "product_name": "Vitamin D Supplement",
        "medicinal_ingredients": [
            {"name": "Cholecalciferol", "source": "from lanolin", "dose": 1000, "unit": "IU"}
        ],
        "non_medicinal_ingredients": ["Microcrystalline cellulose", "Magnesium stearate"],
        "intended_use": "Supports bone and immune health"
    }
    
    # Mock monograph
    test_mono = {
        "vitamin_d": {
            "name": "Vitamin D",
            "allowed_claims": ["Helps in the development and maintenance of bones and teeth"],
            "dose_range": {"min_iu_per_day": 200, "max_iu_per_day": 2500},
            "duration_of_use": "Long-term use",
            "risk_information": {"cautions": ["Consult practitioner if symptoms persist"]}
        }
    }
    
    result = draft_application(test_spec, test_mono, api_key)
    print("Draft result:")
    print(json.dumps(result, indent=2))
