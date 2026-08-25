FEATURE_GROUPS = [
    {
        "title": "Demographics",
        "fields": ["age", "gender"],
    },
    {
        "title": "Blood & Lab Values",
        "fields": [
            "total_protein", "calcium", "iron", "vitamin_d", "alt_liver",
            "manganese", "body_water_content",
        ],
    },
    {
        "title": "Hair & Stress Indices",
        "fields": ["total_keratine", "hair_texture", "stress_level"],
    },
    {
        "title": "Lifestyle & History",
        "fields": [
            "family_hair_fall_history", "chronic_illness", "late_night_sleep",
            "sleep_disturbance", "water_reason", "chemical_use", "anemia", "stress",
        ],
    },
]

FEATURE_META = {
    "age": {
        "label": "Age", "unit": "years", "type": "number",
        "hard_min": 1, "hard_max": 120, "train_min": 20, "train_max": 55, "step": 1,
    },
    "gender": {
        "label": "Gender", "type": "select",
        "options": [(0, "Female"), (1, "Male"), (2, "Other")],
    },
    "total_protein": {
        "label": "Total Protein", "unit": "g/dL", "type": "number",
        "hard_min": 2, "hard_max": 12, "train_min": 4.8, "train_max": 9.5, "step": 0.1,
    },
    "calcium": {
        "label": "Calcium", "unit": "mg/dL", "type": "number",
        "hard_min": 4, "hard_max": 16, "train_min": 7.0, "train_max": 11.5, "step": 0.1,
    },
    "iron": {
        "label": "Iron", "unit": "µg/dL", "type": "number",
        "hard_min": 5, "hard_max": 400, "train_min": 10, "train_max": 210, "step": 1,
    },
    "vitamin_d": {
        "label": "Vitamin D", "unit": "ng/mL", "type": "number",
        "hard_min": 0, "hard_max": 150, "train_min": 4.0, "train_max": 78.4, "step": 0.1,
    },
    "alt_liver": {
        "label": "ALT (Liver Enzyme)", "unit": "U/L", "type": "number",
        "hard_min": 0, "hard_max": 300, "train_min": 5, "train_max": 81, "step": 1,
    },
    "manganese": {
        "label": "Manganese", "unit": "µg/L (whole blood)", "type": "number",
        "hard_min": 0, "hard_max": 50, "train_min": 1, "train_max": 20, "step": 0.1,
    },
    "body_water_content": {
        "label": "Body Water Content", "unit": "%", "type": "number",
        "hard_min": 20, "hard_max": 90, "train_min": 35, "train_max": 75, "step": 0.1,
    },
    "stress_level": {
        "label": "Stress Level", "unit": "PSS score, 0–40", "type": "number",
        "hard_min": 0, "hard_max": 40, "train_min": 0, "train_max": 40, "step": 1,
    },
    "total_keratine": {
        "label": "Total Keratin Index", "unit": "0–100 composite", "type": "number",
        "hard_min": 0, "hard_max": 100, "train_min": 0, "train_max": 100, "step": 1,
    },
    "hair_texture": {
        "label": "Hair Texture Index", "unit": "0–100 composite", "type": "number",
        "hard_min": 0, "hard_max": 100, "train_min": 0, "train_max": 100, "step": 1,
    },
    "family_hair_fall_history": {"label": "Family History of Hair Fall", "type": "bool"},
    "chronic_illness": {"label": "Chronic Illness", "type": "bool"},
    "late_night_sleep": {"label": "Frequent Late-Night Sleep", "type": "bool"},
    "sleep_disturbance": {"label": "Sleep Disturbance", "type": "bool"},
    "water_reason": {"label": "Hard / Chemically-Treated Water Exposure", "type": "bool"},
    "chemical_use": {"label": "Chemical Hair Treatment Use", "type": "bool"},
    "anemia": {"label": "Anemia", "type": "bool"},
    "stress": {"label": "Self-Reported High Stress", "type": "bool"},
}

FEATURE_COLUMNS_FALLBACK = [f for group in FEATURE_GROUPS for f in group["fields"]]
