"""
IMPROVED TECHNICAL AGENT
=========================
Enhanced specification matching with weighted scoring and fuzzy matching
"""

from utils.spec_flattener import flatten_json
from typing import List, Dict
import re


class TechnicalMatcher:
    """
    Advanced technical specification matching engine
    """

    # Specification weights
    SPEC_WEIGHTS = {
        'voltage': 0.25,
        'standards': 0.20,
        'conductor': 0.18,
        'insulation': 0.15,
        'cores': 0.12,
        'armoring': 0.10
    }

    # Synonyms
    MATERIAL_SYNONYMS = {
        'copper': ['cu', 'copper', 'coppper'],
        'aluminum': ['al', 'aluminium', 'aluminum', 'alumunium'],
        'steel': ['st', 'steel', 'stl']
    }

    INSULATION_SYNONYMS = {
        'xlpe': ['xlpe', 'cross-linked polyethylene', 'cross linked polyethylene'],
        'pvc': ['pvc', 'polyvinyl chloride', 'poly vinyl chloride'],
        'epr': ['epr', 'ethylene propylene rubber']
    }

    def __init__(self, product_db):
        self.product_db = product_db

    def normalize(self, val):
        """Normalize text"""
        if not val:
            return ""
        return re.sub(r'[^\w\s]', ' ', str(val).lower().strip())

    def fuzzy_match(self, value: str, text: str, synonyms: dict) -> bool:
        """Fuzzy match with synonyms"""
        norm_value = self.normalize(value)
        norm_text = self.normalize(text)

        # Direct match
        if norm_value in norm_text:
            return True

        # Synonym match
        for _, variants in synonyms.items():
            if norm_value in variants:
                for variant in variants:
                    if variant in norm_text:
                        return True

        return False

    def calculate_match_score(self, product_row, rfp_text: str) -> tuple:
        """Calculate weighted technical score"""
        scores = {}

        # Voltage
        voltage = str(product_row['Voltage_Rating'])
        scores['voltage'] = 100 if self.normalize(voltage) in rfp_text else 0

        # Standards
        standards = str(product_row['Standards_Compliance'])
        if self.normalize(standards) in rfp_text:
            scores['standards'] = 100
        elif any(std in rfp_text for std in ['is', 'iec', 'ieee']):
            scores['standards'] = 60
        else:
            scores['standards'] = 0

        # Conductor
        conductor = str(product_row['Conductor_Material'])
        scores['conductor'] = 100 if self.fuzzy_match(
            conductor, rfp_text, self.MATERIAL_SYNONYMS
        ) else 0

        # Insulation
        insulation = str(product_row['Insulation_Type'])
        scores['insulation'] = 100 if self.fuzzy_match(
            insulation, rfp_text, self.INSULATION_SYNONYMS
        ) else 0

        # Cores
        cores = str(product_row['Number_of_Cores'])
        scores['cores'] = 100 if (
            cores in rfp_text or f"{cores}c" in rfp_text or f"{cores}-core" in rfp_text
        ) else 0

        # Armoring
        armoring = str(product_row['Armoring'])
        scores['armoring'] = 100 if self.normalize(armoring) in rfp_text else 0

        # Weighted score
        weighted_score = sum(
            scores[spec] * self.SPEC_WEIGHTS[spec]
            for spec in self.SPEC_WEIGHTS.keys()
        )

        return weighted_score, scores

    def match_products(
        self,
        rfp: dict,
        min_score: float = 30.0,
        max_results: int = 30
    ) -> List[Dict]:
        """
        Find and rank matching products
        """

        # Flatten + normalize RFP text
        tech_text = self.normalize(
            flatten_json(rfp.get("technical_specifications", "")) +
            " " +
            flatten_json(rfp.get("scope_of_supply", ""))
        )

        matches = []

        for _, row in self.product_db.iterrows():
            weighted_score, component_scores = self.calculate_match_score(row, tech_text)

            if weighted_score >= min_score:
                matches.append({
                    "product_id": row["Product_ID"],
                    "product_name": row["Product_Name"],
                    "category": row["Category"],
                    "spec_match_percent": round(weighted_score, 2),
                    "component_scores": component_scores,
                    "unit_price": row["Unit_Price_INR_per_meter"],
                    "lead_time_days": row["Lead_Time_Days"],
                    "bis_certified": row["BIS_Certified"]
                })

        # Sort descending
        matches.sort(key=lambda x: x["spec_match_percent"], reverse=True)

        # ✅ LIMIT RESULTS TO 30
        return matches[:max_results]


def technical_agent(state):
    """
    Technical matching agent
    Now returns up to 30 matches per RFP
    """

    matcher = TechnicalMatcher(state["product_db"])
    results = []

    for rfp in state["rfps"]:
        matches = matcher.match_products(
            rfp,
            min_score=30.0,   # keep same threshold
            max_results=30    # 🔥 updated from 10 → 30
        )
        results.append(matches)

    state["tech_matches"] = results
    return state
