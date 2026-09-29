import math

OCC_A = {"delivery_rider": 1.8, "campus_worker": 1.0, "domestic_worker": 1.0, "construction_worker": 2.0, "freelancer": 1.0}
OCC_B = {"delivery_rider": 1.5, "campus_worker": 1.0, "domestic_worker": 1.2, "construction_worker": 1.5, "freelancer": 1.0}

def hours_factor(h): 
    return 0.8 if h < 20 else (1.0 if h <= 40 else 1.3)
    
def age_factor(a):   
    return 1.0 if a < 30 else (1.3 if a < 45 else 1.7)

def premium_a(si, occ, hours, night):
    raw = (si/1000) * 0.08 * OCC_A.get(occ, 1.0) * hours_factor(hours) * (1.2 if night else 1.0)
    return math.ceil(round(raw, 6))

def premium_b(daily, occ, age):
    raw = (daily/100) * 0.9 * OCC_B.get(occ, 1.0) * age_factor(age)
    return math.ceil(round(raw, 6))

def get_recommendation(occ):
    # primary = Product A if OCC_A[occ] >= 1.5 else Product B
    if OCC_A.get(occ, 1.0) >= 1.5:
        return "A", "B" # primary, secondary
    return "B", "A"
