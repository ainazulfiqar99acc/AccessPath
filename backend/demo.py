"""Only fixed, fictional free-text values may be persisted by the public demo."""
from fastapi import HTTPException
from .parser import parse_form, validate_answers

SAMPLES = {
    'scholarship': {
        'full_name': 'Synthetic Demo Student', 'email': 'student@example.org',
        'enrollment': 'DEMO-2026', 'support_details': 'Synthetic education fund',
        'statement': 'I want to study accessible design and make everyday services easier to use.',
    },
    'community': {
        'full_name': 'Synthetic Community Member', 'email': 'member@example.org',
        'access_notes': 'Synthetic demonstration: a quiet seating area.',
    },
    'benefit': {'full_name': 'Synthetic Household Member', 'email': 'household@example.org'},
}


def validate_synthetic(form_id: str, answers: dict):
    form = parse_form(form_id)
    fields = {f.id: f for f in form.fields}
    source_errors = validate_answers(form, answers)
    for field_id, value in answers.items():
        field = fields.get(field_id)
        if (not field or (field.type == 'checkbox' and not isinstance(value, bool))
                or (field.type in ('select', 'number') and value != '' and field_id in source_errors)
                or (field.type not in ('select', 'number', 'checkbox') and field_id not in SAMPLES[form_id] and value != '')):
            raise HTTPException(422, 'Synthetic Demo accepts only source-defined choices, bounded counts, and the provided sample text.')
    for field, value in SAMPLES[form_id].items():
        if field in answers and answers[field] not in ('', value):
            raise HTTPException(422, 'Synthetic Demo accepts only the provided sample text. Use “Use sample answer”; do not enter personal information.')
