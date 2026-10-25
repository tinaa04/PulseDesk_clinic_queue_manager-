"""Staff-assigned scheduling categories; not medical diagnosis."""
CATEGORIES = ["Acute / Emergency", "Chronic Illness", "Minor / Routine", "Follow-up / Scheduled"]
def validate_category(value):
    if value not in CATEGORIES:
        raise ValueError("Choose a valid staff-assigned category.")
    return value
