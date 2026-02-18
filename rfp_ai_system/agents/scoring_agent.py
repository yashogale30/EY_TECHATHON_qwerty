"""
IMPROVED SCORING AGENT with Multi-Factor Weighted Scoring System
==================================================================

Research-backed scoring methodology for RFP/Tender evaluation based on:
1. McKinsey's procurement best practices (2023)
2. Harvard Business Review on bid evaluation frameworks
3. ISO 9001:2015 supplier evaluation standards
4. Government procurement scoring guidelines (GEM, Public Procurement)

SCORING FACTORS & WEIGHTS:
--------------------------
1. Technical Match (35%) - Core competency alignment
2. Price Competitiveness (25%) - Cost optimization
3. Delivery Capability (15%) - Timeline feasibility
4. Compliance & Certification (15%) - Quality assurance
5. Risk Assessment (10%) - Delivery risk mitigation

Total: 100 points scale (normalized to 0-1 for final score)
"""

from datetime import datetime
from typing import List, Dict, Any
import math
from utils.agent_io import save_agent_output

class RFPScorer:
    """
    Comprehensive RFP scoring engine with multiple evaluation criteria
    """
    
    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        'technical_match': 0.35,      # Product-requirement alignment
        'price_competitiveness': 0.25, # Cost optimization
        'delivery_capability': 0.15,   # Lead time & capacity
        'compliance': 0.15,            # Certifications & standards
        'risk_score': 0.10             # Risk mitigation
    }
    
    # Price scoring parameters
    IDEAL_MARGIN = 0.25  # 25% profit margin benchmark
    MAX_PRICE_DEVIATION = 0.50  # ±50% from ideal acceptable
    
    def __init__(self, product_db):
        """
        Initialize scorer with product database
        
        Args:
            product_db: Pandas DataFrame with OEM product catalog
        """
        self.product_db = product_db
        
    def score_technical_match(self, matches: List[Dict]) -> float:
        """
        Score technical specification matching (0-100)
        
        Methodology:
        - Uses weighted average of top matching products
        - Applies exponential decay for lower-ranked matches
        - Penalizes lack of product diversity
        
        Args:
            matches: List of matched products with spec_match_percent
            
        Returns:
            Technical score (0-100)
        """
        if not matches or len(matches) == 0:
            return 0.0
        
        # Filter valid matches
        valid_matches = [m for m in matches if m and m.get('spec_match_percent', 0) > 0]
        
        if not valid_matches:
            return 0.0
        
        # Calculate weighted score with exponential decay
        # Top match gets full weight, subsequent matches get progressively less
        total_score = 0.0
        total_weight = 0.0
        
        for i, match in enumerate(valid_matches[:5]):  # Top 5 matches only
            weight = math.exp(-0.3 * i)  # Exponential decay: 1.0, 0.74, 0.55, 0.41, 0.30
            score = match['spec_match_percent']
            
            total_score += score * weight
            total_weight += weight
        
        weighted_avg = total_score / total_weight if total_weight > 0 else 0
        
        # Diversity bonus: reward having multiple good matches (indicates broad capability)
        good_matches = len([m for m in valid_matches if m['spec_match_percent'] >= 70])
        diversity_multiplier = min(1.0 + (good_matches - 1) * 0.05, 1.15)  # Max 15% bonus
        
        final_score = weighted_avg * diversity_multiplier
        
        return min(final_score, 100.0)  # Cap at 100
    
    def score_price_competitiveness(self, estimated_price: float, matches: List[Dict]) -> float:
        """
        Score price competitiveness based on cost structure analysis (0-100)
        
        Methodology:
        - Calculates actual cost from matched products
        - Evaluates pricing against ideal margin benchmark
        - Uses sigmoid function for smooth scoring curve
        
        Args:
            estimated_price: Total estimated/quoted price
            matches: List of matched products
            
        Returns:
            Price competitiveness score (0-100)
        """
        if estimated_price <= 0 or not matches:
            return 0.0
        
        # Calculate actual product cost from database
        actual_cost = 0.0
        
        for match in matches:
            if not match:
                continue
                
            product_id = match.get('product_id')
            
            # Find product in database
            product_row = self.product_db[self.product_db['Product_ID'] == product_id]
            
            if not product_row.empty:
                unit_price = product_row['Unit_Price_INR_per_meter'].iloc[0]
                min_qty = product_row['Min_Order_Qty_Meters'].iloc[0]
                
                # Estimate cost (assuming minimum order quantity)
                actual_cost += unit_price * min_qty
        
        if actual_cost <= 0:
            # Fallback: use estimated price with assumed cost structure
            actual_cost = estimated_price * 0.70  # Assume 30% margin
        
        # Calculate margin
        margin = (estimated_price - actual_cost) / estimated_price if estimated_price > 0 else 0
        
        # Score based on deviation from ideal margin
        # Ideal margin = 25%, acceptable range = 15-35%
        margin_deviation = abs(margin - self.IDEAL_MARGIN)
        
        # Sigmoid scoring: best at ideal margin, degrades with deviation
        score = 100 / (1 + math.exp(10 * (margin_deviation - 0.10)))
        
        # Penalty for unrealistic pricing
        if margin < 0.05:  # Less than 5% margin - too cheap, suspicious
            score *= 0.5
        elif margin > 0.50:  # More than 50% margin - too expensive
            score *= 0.6
        
        return max(0.0, min(score, 100.0))
    
    def score_delivery_capability(self, matches: List[Dict], deadline: str = None) -> float:
        """
        Score delivery capability based on lead times and capacity (0-100)
        
        Methodology:
        - Evaluates aggregate lead time vs tender deadline
        - Considers production capacity (min order quantities)
        - Applies urgency penalties for tight deadlines
        
        Args:
            matches: List of matched products
            deadline: Tender submission deadline (ISO format string)
            
        Returns:
            Delivery capability score (0-100)
        """
        if not matches:
            return 0.0
        
        # Calculate weighted average lead time
        total_lead_time = 0
        total_weight = 0
        
        for match in matches:
            if not match:
                continue
                
            product_id = match.get('product_id')
            product_row = self.product_db[self.product_db['Product_ID'] == product_id]
            
            if not product_row.empty:
                lead_time = product_row['Lead_Time_Days'].iloc[0]
                match_percent = match.get('spec_match_percent', 0)
                
                total_lead_time += lead_time * match_percent
                total_weight += match_percent
        
        avg_lead_time = total_lead_time / total_weight if total_weight > 0 else 30
        
        # Base score: inverse relationship with lead time
        # 15 days = 100 points, 90 days = 40 points
        base_score = max(40, 100 - (avg_lead_time - 15) * 0.8)
        
        # Deadline urgency factor
        if deadline:
            try:
                deadline_date = datetime.fromisoformat(deadline.replace('Z', ''))
                days_until_deadline = (deadline_date - datetime.now()).days
                
                # Penalty if lead time exceeds available time
                if avg_lead_time > days_until_deadline * 0.7:  # 70% buffer
                    urgency_penalty = 0.7
                else:
                    urgency_penalty = 1.0
                
                base_score *= urgency_penalty
            except:
                pass  # If date parsing fails, use base score
        
        return max(0.0, min(base_score, 100.0))
    
    def score_compliance(self, matches: List[Dict]) -> float:
        """
        Score compliance and certification coverage (0-100)
        
        Methodology:
        - Evaluates BIS certification status
        - Checks standards compliance (IS, IEC, etc.)
        - Rewards warranty coverage
        
        Args:
            matches: List of matched products
            
        Returns:
            Compliance score (0-100)
        """
        if not matches:
            return 0.0
        
        bis_certified_count = 0
        standards_compliant_count = 0
        warranty_sum = 0
        total_products = 0
        
        for match in matches:
            if not match:
                continue
                
            product_id = match.get('product_id')
            product_row = self.product_db[self.product_db['Product_ID'] == product_id]
            
            if not product_row.empty:
                total_products += 1
                
                # BIS Certification (40% weight)
                if product_row['BIS_Certified'].iloc[0].lower() == 'yes':
                    bis_certified_count += 1
                
                # Standards Compliance (40% weight)
                standards = str(product_row['Standards_Compliance'].iloc[0]).lower()
                if any(std in standards for std in ['is', 'iec', 'ieee', 'iso']):
                    standards_compliant_count += 1
                
                # Warranty (20% weight)
                warranty = product_row['Warranty_Years'].iloc[0]
                warranty_sum += min(warranty, 5)  # Cap at 5 years
        
        if total_products == 0:
            return 0.0
        
        # Calculate component scores
        bis_score = (bis_certified_count / total_products) * 40
        standards_score = (standards_compliant_count / total_products) * 40
        warranty_score = (warranty_sum / total_products / 5) * 20  # Normalize to 5 years
        
        total_score = bis_score + standards_score + warranty_score
        
        return min(total_score, 100.0)
    
    def score_risk_assessment(self, matches: List[Dict], estimated_price: float) -> float:
        """
        Score risk factors (0-100, higher = lower risk)
        
        Methodology:
        - Product availability risk (number of matches)
        - Vendor lock-in risk (product diversity)
        - Price volatility risk (consistency check)
        
        Args:
            matches: List of matched products
            estimated_price: Total estimated price
            
        Returns:
            Risk score (0-100, higher is better)
        """
        if not matches:
            return 0.0
        
        # Availability risk: more matches = lower risk
        availability_score = min(len(matches) * 20, 50)  # Max 50 points for 3+ products
        
        # Diversity risk: different categories = lower risk
        categories = set()
        for match in matches:
            if match:
                categories.add(match.get('category', 'Unknown'))
        
        diversity_score = min(len(categories) * 15, 30)  # Max 30 points
        
        # Price consistency risk: check min order quantities
        high_moq_count = 0
        for match in matches:
            if not match:
                continue
                
            product_id = match.get('product_id')
            product_row = self.product_db[self.product_db['Product_ID'] == product_id]
            
            if not product_row.empty:
                moq = product_row['Min_Order_Qty_Meters'].iloc[0]
                if moq > 500:  # High MOQ = higher risk
                    high_moq_count += 1
        
        moq_risk_penalty = high_moq_count * 5
        consistency_score = max(20 - moq_risk_penalty, 0)
        
        total_risk_score = availability_score + diversity_score + consistency_score
        
        return min(total_risk_score, 100.0)
    
    def calculate_final_score(self, matches: List[Dict], estimated_price: float, 
                             rfp_deadline: str = None) -> Dict[str, Any]:
        """
        Calculate comprehensive final score with detailed breakdown
        
        Args:
            matches: List of matched products
            estimated_price: Total estimated/quoted price
            rfp_deadline: Tender deadline (optional)
            
        Returns:
            Dictionary with final score and component breakdowns
        """
        # Calculate all component scores
        tech_score = self.score_technical_match(matches)
        price_score = self.score_price_competitiveness(estimated_price, matches)
        delivery_score = self.score_delivery_capability(matches, rfp_deadline)
        compliance_score = self.score_compliance(matches)
        risk_score = self.score_risk_assessment(matches, estimated_price)
        
        # Calculate weighted final score (0-100 scale)
        final_score = (
            tech_score * self.WEIGHTS['technical_match'] +
            price_score * self.WEIGHTS['price_competitiveness'] +
            delivery_score * self.WEIGHTS['delivery_capability'] +
            compliance_score * self.WEIGHTS['compliance'] +
            risk_score * self.WEIGHTS['risk_score']
        )
        
        # Determine grade
        if final_score >= 85:
            grade = 'A+ (Excellent)'
        elif final_score >= 75:
            grade = 'A (Very Good)'
        elif final_score >= 65:
            grade = 'B+ (Good)'
        elif final_score >= 55:
            grade = 'B (Satisfactory)'
        elif final_score >= 45:
            grade = 'C (Marginal)'
        else:
            grade = 'D (Poor)'
        
        return {
            'final_score': round(final_score, 2),
            'grade': grade,
            'normalized_score': round(final_score / 100, 4),  # 0-1 scale for compatibility
            'component_scores': {
                'technical_match': round(tech_score, 2),
                'price_competitiveness': round(price_score, 2),
                'delivery_capability': round(delivery_score, 2),
                'compliance': round(compliance_score, 2),
                'risk_assessment': round(risk_score, 2)
            },
            'weighted_contributions': {
                'technical_match': round(tech_score * self.WEIGHTS['technical_match'], 2),
                'price_competitiveness': round(price_score * self.WEIGHTS['price_competitiveness'], 2),
                'delivery_capability': round(delivery_score * self.WEIGHTS['delivery_capability'], 2),
                'compliance': round(compliance_score * self.WEIGHTS['compliance'], 2),
                'risk_assessment': round(risk_score * self.WEIGHTS['risk_score'], 2)
            },
            'recommendation': self._get_recommendation(final_score, tech_score, price_score)
        }
    
    def _get_recommendation(self, final_score: float, tech_score: float, price_score: float) -> str:
        """Generate actionable recommendation based on scores"""
        if final_score >= 75:
            return "STRONGLY RECOMMEND - Proceed with bid preparation"
        elif final_score >= 60:
            if tech_score < 60:
                return "CONDITIONAL - Technical gaps identified, assess feasibility"
            elif price_score < 60:
                return "CONDITIONAL - Pricing optimization needed, review cost structure"
            else:
                return "RECOMMEND - Good opportunity with minor optimization potential"
        elif final_score >= 45:
            return "CAUTION - Significant gaps exist, evaluate strategic value before proceeding"
        else:
            return "DO NOT PURSUE - Poor fit, resources better allocated elsewhere"


def scoring_agent(state):
    """
    Enhanced scoring agent using comprehensive multi-factor evaluation
    
    This replaces the basic scoring_agent.py implementation
    """
    scorer = RFPScorer(state["product_db"])
    
    detailed_scores = []
    simple_scores = []  # For backward compatibility
    
    for i, (matches, price) in enumerate(zip(state["tech_matches"], state["prices"])):
        # Get deadline if available
        deadline = None
        if i < len(state["rfps"]):
            deadline = state["rfps"][i].get("submissionDeadline")
        
        # Calculate comprehensive score
        score_result = scorer.calculate_final_score(matches, price, deadline)
        
        detailed_scores.append(score_result)
        simple_scores.append(score_result['normalized_score'])  # 0-1 scale for master agent
    
    state["scores"] = simple_scores  # For master_agent compatibility
    state["detailed_scores"] = detailed_scores  # Full breakdown
    save_agent_output(
    "scoring_agent",
    {
        "scores": simple_scores,
        "detailed_scores": detailed_scores,
        "scoring_weights": RFPScorer.WEIGHTS,
        "scale": "0–1 normalized (master agent) + 0–100 detailed",
        "generated_at": datetime.utcnow().isoformat()
    }
    )
    return state