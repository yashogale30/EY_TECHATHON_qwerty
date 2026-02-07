# agents/master_agent.py
"""
Enhanced Master Agent with PDF Report Generation
=================================================
Selects the best RFP and generates a professional PDF report.
"""

import os
import numpy as np
from pdf_generator_v2 import generate_rfp_pdf


def master_agent(state):
    """
    Enhanced master agent:
    1. Finds the best RFP
    2. Generates a PDF report

    Args:
        state (dict): Graph state with scores, rfps, tech_matches, prices

    Returns:
        dict: Updated state with best_rfp and pdf_path
    """

    if not state.get("scores"):
        state["best_rfp"] = "No tenders found"
        state["pdf_path"] = None
        return state

    # Find the best RFP
    best = max(range(len(state["scores"])), key=lambda i: state["scores"][i])
    best_rfp_data = {
        "rfp": state["rfps"][best],
        "matches": state["tech_matches"][best],
        "price": state["prices"][best],
        "score": state["scores"][best]
    }
    state["best_rfp"] = best_rfp_data

    # Generate PDF safely on Windows
    try:
        pdf_data = {
            "rfp": best_rfp_data["rfp"],
            "matches": best_rfp_data["matches"],
            "price": float(best_rfp_data["price"]) if isinstance(best_rfp_data["price"], (np.floating, np.integer)) else best_rfp_data["price"],
            "score": float(best_rfp_data["score"]) if isinstance(best_rfp_data["score"], (np.floating, np.integer)) else best_rfp_data["score"]
        }

        # Create outputs folder in current directory
        output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(output_dir, exist_ok=True)

        pdf_path = generate_rfp_pdf(
            rfp_data=pdf_data,
            output_path=os.path.join(output_dir, "rfp_bid_report.pdf")
        )

        state["pdf_path"] = pdf_path
        print(f"✅ PDF report generated: {pdf_path}")

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        state["pdf_path"] = None

    return state
