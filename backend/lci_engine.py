import math

def mean(arr):
    if not arr:
        return 0
    return sum(arr) / len(arr)

def stdev(arr):
    if not arr:
        return 0
    m = mean(arr)
    variance = sum((x - m) ** 2 for x in arr) / len(arr)
    return math.sqrt(variance)

def coefficient_of_variation(arr):
    m = mean(arr)
    if m == 0:
        return 1.0
    return stdev(arr) / m

def compute_lci(months_production, fulfillment, coop, digital, govt, monsoon_adjustment_enabled=True):
    # July, August, September indices (0-indexed: 6, 7, 8)
    MONSOON_IDX = [6, 7, 8]
    
    # Calculate Coefficient of Variation (CV)
    raw_cv = coefficient_of_variation(months_production)
    
    # Exclude July, Aug, Sep for non-monsoon CV
    non_monsoon_production = [x for i, x in enumerate(months_production) if i not in MONSOON_IDX]
    adjusted_cv = coefficient_of_variation(non_monsoon_production)
    
    # Check if the monsoon explained the drop (difference > 0.05)
    explained = (raw_cv - adjusted_cv) > 0.05
    
    used_cv = adjusted_cv if (monsoon_adjustment_enabled and explained) else raw_cv
    
    # Consistency Score scaled 0-100 (where 0 CV is 100, and >= 0.6 CV is 0)
    consistency_score = max(0.0, min(100.0, (1.0 - (used_cv / 0.6)) * 100.0))
    
    # Define factors, weights, and values
    weights = {
        "production": 0.30,
        "fulfillment": 0.25,
        "digital": 0.20,
        "coop": 0.15,
        "govt": 0.10
    }
    
    values = {
        "production": consistency_score,
        "fulfillment": fulfillment,
        "digital": digital,
        "coop": coop,
        "govt": govt
    }
    
    labels = {
        "production": "Production consistency",
        "fulfillment": "Fulfilment history",
        "coop": "Cooperative standing",
        "digital": "Digital payment footprint",
        "govt": "Govt. scheme enrolment"
    }
    
    nudges = {
        "production": "Keep your loom running on a steady weekly rhythm outside the monsoon months — consistent output raises this fastest.",
        "fulfillment": "Complete your next 3 consecutive marketplace deliveries on time to raise this score.",
        "coop": "Attend your next few cooperative meetings and keep your membership active.",
        "digital": "Receive more sale payments directly into your Karigar Wallet instead of cash.",
        "govt": "Enrol in the Bunkar Mudra Yojana or e-Shram if you haven't already — a one-time boost."
    }
    
    baseline = 600
    score_delta = 0
    contributions = []
    
    for key, w in weights.items():
        v = values[key]
        # contribScore = ((w * v - w * 50) / 100) * 600
        contrib_score = 6.0 * w * (v - 50.0)
        score_delta += contrib_score
        contributions.append({
            "key": key,
            "label": labels[key],
            "value": v,
            "weight": w,
            "contrib_score": round(contrib_score, 1),
            "nudge": nudges[key]
        })
        
    score = round(max(300, min(900, baseline + score_delta)))
    
    # Determine Risk Band
    if score >= 750:
        band = "Excellent"
    elif score >= 650:
        band = "Good"
    elif score >= 550:
        band = "Fair"
    else:
        band = "Needs Building"
        
    # Calculate Pre-approved Loan Limit
    # limit = max(3000, min(50000, round(((score-300)/600)*50000/500)*500))
    limit_fraction = (score - 300) / 600.0
    raw_limit = limit_fraction * 50000.0
    rounded_limit = round(raw_limit / 500.0) * 500
    loan_limit = int(max(3000, min(50000, rounded_limit)))
    
    # Sort contributions to find the weakest factor for the voice nudge
    sorted_contribs = sorted(contributions, key=lambda c: c["contrib_score"])
    voice_nudge = sorted_contribs[0]["nudge"]
    
    return {
        "score": score,
        "band": band,
        "baseline": baseline,
        "loan_limit": loan_limit,
        "cv": {
            "raw": round(raw_cv, 4),
            "adjusted": round(adjusted_cv, 4),
            "used": round(used_cv, 4),
            "explained": explained
        },
        "contributions": contributions,
        "voice_nudge": voice_nudge
    }
