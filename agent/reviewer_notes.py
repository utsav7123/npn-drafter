"""
Reviewer Notes: Generates a human-readable checklist for regulatory review.

This makes the human review step explicit and structured. The reviewer
doesn't get a mysterious LLM output; they get a clear checklist of what
to verify before submission.
"""

import json
import re
from typing import Dict, List
from anthropic import Anthropic


def generate_reviewer_notes(
    application_draft: Dict,
    api_key: str
) -> Dict:
    """
    Generate a reviewer checklist using Claude.
    
    Args:
        application_draft: The drafted NPN application
        api_key: Anthropic API key
    
    Returns:
        Dict with checklist_items: List[Dict] with category, item, severity
    """
    
    client = Anthropic(api_key=api_key)
    
    # Load the reviewer prompt
    try:
        with open("prompts/reviewer_prompt.txt", "r") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        return {
            "error": "Reviewer prompt not found",
            "checklist_items": create_default_checklist(application_draft)
        }
    
    # Format the prompt
    prompt = prompt_template.replace(
        "{application_draft}",
        json.dumps(application_draft, indent=2)
    )
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "error": None,
                    "checklist_items": result.get("checklist_items", [])
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback to default
        return {
            "error": "Could not parse LLM response",
            "checklist_items": create_default_checklist(application_draft)
        }
    
    except Exception as e:
        return {
            "error": f"LLM call failed: {str(e)}",
            "checklist_items": create_default_checklist(application_draft)
        }


def create_default_checklist(application_draft: Dict) -> List[Dict]:
    """
    Create a default checklist when LLM is unavailable.
    This is a solid fallback that covers key regulatory items.
    """
    
    checklist = [
        {
            "category": "Ingredients",
            "item": "Verify all medicinal ingredients against supplier documentation and certificates of analysis",
            "severity": "high"
        },
        {
            "category": "Ingredients",
            "item": "Confirm ingredient sources match approved suppliers for Class 1 monographs",
            "severity": "high"
        },
        {
            "category": "Doses",
            "item": "Double-check all dose values against current monograph limits (monographs are updated periodically)",
            "severity": "high"
        },
        {
            "category": "Claims",
            "item": "Ensure all label claims are verbatim from the monograph allowed claims list",
            "severity": "high"
        },
        {
            "category": "Claims",
            "item": "Verify no unauthorized therapeutic claims are present (e.g., cure, treat, diagnose)",
            "severity": "high"
        },
        {
            "category": "Labeling",
            "item": "Check that directions for use are clear and safe for intended population",
            "severity": "medium"
        },
        {
            "category": "Labeling",
            "item": "Confirm risk information (cautions, contraindications) are complete and from monograph",
            "severity": "high"
        },
        {
            "category": "Non-Medicinal Ingredients",
            "item": "Verify all non-medicinal ingredients are on the acceptable list and within limits",
            "severity": "medium"
        },
        {
            "category": "Packaging",
            "item": "Ensure package size and number of doses per unit are appropriate for the product class",
            "severity": "low"
        },
        {
            "category": "Subpopulations",
            "item": "If product is for children, verify dose is within pediatric limits from monograph",
            "severity": "high"
        },
        {
            "category": "Monograph Compliance",
            "item": "Confirm the monograph version used is the current published version (not outdated)",
            "severity": "high"
        },
    ]
    
    # Add specific items based on application content
    if len(application_draft.get("medicinal_ingredients", [])) > 1:
        checklist.insert(2, {
            "category": "Multi-Ingredient",
            "item": "Since product has multiple medicinal ingredients, verify this is Class 2 (each ingredient in separate monograph)",
            "severity": "high"
        })
    
    return checklist


if __name__ == "__main__":
    import os
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    test_draft = {
        "product_name": "Vitamin D Supplement",
        "medicinal_ingredients": [
            {
                "ingredient": "Cholecalciferol",
                "dose": "1000 IU",
                "monograph_reference": "vitamin_d"
            }
        ],
        "claims": ["Helps in the development and maintenance of bones and teeth."],
        "monographs_referenced": ["vitamin_d"]
    }
    
    if api_key:
        result = generate_reviewer_notes(test_draft, api_key)
    else:
        result = {
            "error": None,
            "checklist_items": create_default_checklist(test_draft)
        }
    
    print("Reviewer checklist:")
    print(json.dumps(result, indent=2))
