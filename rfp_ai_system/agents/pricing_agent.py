"""
CORRECTED PRICING AGENT
========================
Replaces random pricing with actual cost calculation from product database

Key Improvements:
- Uses real product prices from OEM database
- Calculates based on minimum order quantities
- Adds realistic margin (15-30%)
- Handles missing products gracefully
"""

import random


def pricing_agent(state):
    """
    Calculate realistic pricing for each tender based on matched products
    
    Process:
    1. For each matched product, get unit price and MOQ from database
    2. Calculate total cost = sum(unit_price × MOQ × quantity_estimate)
    3. Add realistic margin (15-30% based on tender size)
    4. Handle missing/unmatched products
    
    Args:
        state: Current graph state with tech_matches and product_db
        
    Returns:
        Updated state with prices list
    """
    product_db = state["product_db"]
    totals = []

    for tender_matches in state["tech_matches"]:
        tender_total = 0.0
        
        if not tender_matches:
            totals.append(0)
            continue

        for match in tender_matches:
            if not match:
                continue
            
            product_id = match.get("product_id")
            
            # Find product in database
            product_row = product_db[product_db["Product_ID"] == product_id]
            
            if product_row.empty:
                # Product not found - add estimated cost
                tender_total += 50000  # Fallback estimate
                continue
            
            # Get actual pricing data
            unit_price = product_row["Unit_Price_INR_per_meter"].iloc[0]
            min_order_qty = product_row["Min_Order_Qty_Meters"].iloc[0]
            
            # Estimate quantity multiplier based on tender requirements
            # For now, use minimum order quantity
            # TODO: Parse tender quantity requirements from RFP text
            quantity_multiplier = 1.0  # Conservative estimate
            
            total_meters = min_order_qty * quantity_multiplier
            product_cost = unit_price * total_meters
            
            tender_total += product_cost
        
        # Add realistic margin (15-30% based on tender size)
        if tender_total > 0:
            # Larger tenders get lower margins (economies of scale)
            if tender_total > 500000:
                margin = 0.15  # 15% for large tenders
            elif tender_total > 200000:
                margin = 0.20  # 20% for medium tenders
            else:
                margin = 0.25  # 25% for small tenders
            
            # Add some randomness to margin (±5%)
            margin_variation = random.uniform(-0.05, 0.05)
            final_margin = margin + margin_variation
            
            quoted_price = tender_total * (1 + final_margin)
            totals.append(round(quoted_price, 2))
        else:
            totals.append(0)

    state["prices"] = totals
    return state