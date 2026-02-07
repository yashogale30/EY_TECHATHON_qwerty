"""
IMPROVED TECHNICAL AGENT
=========================
Enhanced specification matching with weighted scoring and fuzzy matching

Key Improvements:
- Weighted specification scoring (not all specs are equal)
- Fuzzy string matching for variations
- Configurable match threshold
- Better product ranking algorithm
"""

from utils.spec_flattener import flatten_json
from typing import List, Dict
import re


class TechnicalMatcher:
    """
    Advanced technical specification matching engine
    """
    
    # Specification weights (based on criticality in cable/electrical products)
    SPEC_WEIGHTS = {
        'voltage': 0.25,       # Most critical - wrong voltage = complete failure
        'standards': 0.20,     # Compliance is mandatory for government tenders
        'conductor': 0.18,     # Material affects performance significantly
        'insulation': 0.15,    # Important for safety and durability
        'cores': 0.12,         # Affects capacity and application
        'armoring': 0.10       # Protection level, less critical for some applications
    }
    
    # Fuzzy matching patterns for common variations
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
        """Enhanced normalization with special character handling"""
        if not val:
            return ""
        return re.sub(r'[^\w\s]', ' ', str(val).lower().strip())
    
    def fuzzy_match(self, value: str, text: str, synonyms: dict) -> bool:
        """
        Check if value matches text using fuzzy matching with synonyms
        
        Args:
            value: Value to find (from database)
            text: Text to search in (from RFP)
            synonyms: Dictionary of synonym lists
            
        Returns:
            True if match found
        """
        norm_value = self.normalize(value)
        norm_text = self.normalize(text)
        
        # Direct match
        if norm_value in norm_text:
            return True
        
        # Synonym matching
        for canonical, variants in synonyms.items():
            if norm_value in variants:
                # Check if any variant is in text
                for variant in variants:
                    if variant in norm_text:
                        return True
        
        return False
    
    def calculate_match_score(self, product_row, rfp_text: str) -> tuple:
        """
        Calculate weighted match score for a product against RFP requirements
        
        Args:
            product_row: Single row from product database
            rfp_text: Normalized RFP technical text
            
        Returns:
            Tuple of (weighted_score, match_details)
        """
        scores = {}
        
        # Voltage matching
        voltage = str(product_row['Voltage_Rating'])
        if self.normalize(voltage) in rfp_text:
            scores['voltage'] = 100
        else:
            scores['voltage'] = 0
        
        # Standards matching (high priority)
        standards = str(product_row['Standards_Compliance'])
        if self.normalize(standards) in rfp_text:
            scores['standards'] = 100
        elif any(std in rfp_text for std in ['is', 'iec', 'ieee']):
            scores['standards'] = 60  # Partial match if any standard mentioned
        else:
            scores['standards'] = 0
        
        # Conductor material (fuzzy matching)
        conductor = str(product_row['Conductor_Material'])
        if self.fuzzy_match(conductor, rfp_text, self.MATERIAL_SYNONYMS):
            scores['conductor'] = 100
        else:
            scores['conductor'] = 0
        
        # Insulation type (fuzzy matching)
        insulation = str(product_row['Insulation_Type'])
        if self.fuzzy_match(insulation, rfp_text, self.INSULATION_SYNONYMS):
            scores['insulation'] = 100
        else:
            scores['insulation'] = 0
        
        # Number of cores
        cores = str(product_row['Number_of_Cores'])
        if cores in rfp_text or f"{cores}c" in rfp_text or f"{cores}-core" in rfp_text:
            scores['cores'] = 100
        else:
            scores['cores'] = 0
        
        # Armoring
        armoring = str(product_row['Armoring'])
        if self.normalize(armoring) in rfp_text:
            scores['armoring'] = 100
        else:
            scores['armoring'] = 0
        
        # Calculate weighted total score
        weighted_score = sum(
            scores[spec] * self.SPEC_WEIGHTS[spec]
            for spec in self.SPEC_WEIGHTS.keys()
        )
        
        return weighted_score, scores
    
    def match_products(self, rfp: dict, min_score: float = 30.0, max_results: int = 10) -> List[Dict]:
        """
        Find and rank matching products for an RFP
        
        Args:
            rfp: RFP dictionary with technical specifications
            min_score: Minimum match score to include (0-100)
            max_results: Maximum number of results to return
            
        Returns:
            List of matched products with scores
        """
        # Flatten and normalize RFP technical text
        tech_text = self.normalize(
            flatten_json(rfp.get("technical_specifications", "")) +
            " " +
            flatten_json(rfp.get("scope_of_supply", ""))
        )
        
        matches = []
        
        for _, row in self.product_db.iterrows():
            weighted_score, component_scores = self.calculate_match_score(row, tech_text)
            
            # Only include products above threshold
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
        
        # Sort by match score (descending)
        matches.sort(key=lambda x: x["spec_match_percent"], reverse=True)
        
        return matches[:max_results]


def technical_agent(state):
    """
    Enhanced technical matching agent
    
    Replaces simple string matching with weighted, fuzzy matching algorithm
    """
    matcher = TechnicalMatcher(state["product_db"])
    results = []
    
    for rfp in state["rfps"]:
        matches = matcher.match_products(rfp, min_score=30.0, max_results=10)
        results.append(matches)
    
    state["tech_matches"] = results
    return state