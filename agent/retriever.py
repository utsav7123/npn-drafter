"""
Retriever: Loads monograph files by ID.

In v1, this is simple JSON file lookup.
In v2, this would query a vector database over the full NNHPD corpus.
"""

import json
import os
from typing import Dict, List, Optional


def get_monograph(monograph_id: str) -> Optional[Dict]:
    """
    Load a monograph by ID.
    
    Args:
        monograph_id: e.g., "vitamin_d"
    
    Returns:
        The monograph data as a dict, or None if not found.
    """
    path = f"monographs/{monograph_id}.json"
    
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def get_monographs(monograph_ids: List[str]) -> Dict[str, Dict]:
    """
    Load multiple monographs by ID.
    
    Args:
        monograph_ids: List of monograph IDs
    
    Returns:
        Dict mapping monograph_id -> monograph data.
        Missing monographs are skipped.
    """
    result = {}
    for mono_id in monograph_ids:
        mono = get_monograph(mono_id)
        if mono:
            result[mono_id] = mono
    
    return result


def list_all_monographs() -> List[Dict]:
    """
    List all available monographs with their key info.
    
    Returns:
        List of dicts with 'id', 'name', 'class'.
    """
    result = []
    monograph_dir = "monographs"
    
    if not os.path.exists(monograph_dir):
        return result
    
    for filename in sorted(os.listdir(monograph_dir)):
        if filename.endswith(".json"):
            mono_id = filename.replace(".json", "")
            mono = get_monograph(mono_id)
            if mono:
                result.append({
                    "id": mono_id,
                    "name": mono.get("name", "Unknown"),
                    "class": mono.get("class", 1),
                    "active_ingredient": mono.get("active_ingredient", "")
                })
    
    return result


if __name__ == "__main__":
    # Test
    print("Available monographs:")
    for mono in list_all_monographs():
        print(f"  - {mono['id']}: {mono['name']} (Class {mono['class']})")
    
    print("\nLoading vitamin_d:")
    vit_d = get_monograph("vitamin_d")
    if vit_d:
        print(f"  Name: {vit_d.get('name')}")
        print(f"  Dose range: {vit_d.get('dose_range')}")
