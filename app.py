"""
Flask web server for the NPN Application Drafter.

Provides:
- GET / : Form to input product spec
- POST /draft : Process spec and return application draft + validation + reviewer notes
"""

import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from agent.classifier import classify_product
from agent.retriever import get_monographs
from agent.drafter import draft_application
from agent.validator import validate_application
from agent.reviewer_notes import generate_reviewer_notes

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.getenv("ANTHROPIC_API_KEY")


@app.route("/")
def index():
    """Serve the main form."""
    return render_template("index.html")


@app.route("/api/draft", methods=["POST"])
def api_draft():
    """
    Main endpoint: takes a product spec JSON and returns:
    - Classification (Class 1/2/3)
    - Matched monographs
    - Application draft
    - Validation results
    - Reviewer checklist
    """
    
    try:
        # Parse input
        data = request.get_json()
        
        if not data or "product_spec" not in data:
            return jsonify({"error": "Missing product_spec in request"}), 400
        
        product_spec = data["product_spec"]
        
        if isinstance(product_spec, str):
            product_spec = json.loads(product_spec)
        
        # Step 1: Classify
        classification = classify_product(product_spec)
        
        # Step 2: Retrieve monographs
        monograph_data = get_monographs(classification["matched_monographs"])
        
        if not monograph_data and classification["class"] != 3:
            return jsonify({"error": "No matching monographs found"}), 400
        
        # Step 3: Draft application
        if not API_KEY:
            return jsonify({"error": "ANTHROPIC_API_KEY not set"}), 500
        
        draft_result = draft_application(product_spec, monograph_data, API_KEY)
        
        if draft_result.get("error"):
            return jsonify({
                "classification": classification,
                "draft": draft_result.get("draft"),
                "draft_error": draft_result.get("error"),
                "validation": None,
                "reviewer_notes": None
            }), 200  # Return partial result
        
        application_draft = draft_result["draft"]
        
        # Step 4: Validate
        validation_result = validate_application(application_draft, monograph_data)
        
        # Step 5: Generate reviewer notes
        reviewer_notes = generate_reviewer_notes(application_draft, API_KEY)
        
        # Return complete result
        return jsonify({
            "classification": classification,
            "draft": application_draft,
            "validation": validation_result,
            "reviewer_notes": reviewer_notes,
            "error": None
        })
    
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON in product_spec: {str(e)}"}), 400
    
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


@app.route("/api/sample-products", methods=["GET"])
def api_sample_products():
    """Return sample product specs for demo."""
    samples = [
        {
            "name": "Simple Vitamin D (Class 1)",
            "product_name": "Vitamin D3 Tablets",
            "medicinal_ingredients": [
                {"name": "Cholecalciferol", "source": "from lanolin", "dose": 1000, "unit": "IU"}
            ],
            "non_medicinal_ingredients": ["Microcrystalline cellulose", "Magnesium stearate"],
            "intended_use": "Supports bone and immune health"
        },
        {
            "name": "Calcium + Vitamin D (Class 2)",
            "product_name": "Calcium + D3 Tablets",
            "medicinal_ingredients": [
                {"name": "Calcium carbonate", "source": "from oyster shell", "dose": 500, "unit": "mg"},
                {"name": "Cholecalciferol", "source": "from lanolin", "dose": 400, "unit": "IU"}
            ],
            "non_medicinal_ingredients": ["Microcrystalline cellulose", "Magnesium stearate"],
            "intended_use": "Supports bone health and calcium absorption"
        },
        {
            "name": "Novel Extract (Class 3)",
            "product_name": "Ginseng + Curcumin Complex",
            "medicinal_ingredients": [
                {"name": "Korean ginseng extract", "source": "root", "dose": 100, "unit": "mg"},
                {"name": "Curcumin", "source": "from turmeric", "dose": 200, "unit": "mg"}
            ],
            "non_medicinal_ingredients": ["Capsule shell", "Rice bran"],
            "intended_use": "Supports energy and joint health"
        }
    ]
    
    return jsonify(samples)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
