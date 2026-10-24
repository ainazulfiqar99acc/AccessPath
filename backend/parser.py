import hashlib
import re
from pathlib import Path
from bs4 import BeautifulSoup
from .schema import Form, FormField, FieldEvidence, Requirement, Option

FORM_DIR = Path(__file__).parent / 'forms'
FORM_IDS = ('scholarship', 'community', 'benefit')


def parse_form(form_id: str) -> Form:
    if form_id not in FORM_IDS:
        raise ValueError('Unsupported fictional form')
    html = (FORM_DIR / f'{form_id}.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    fields = []
    for el in soup.select('form input[name], form select[name], form textarea[name]'):
        field_id = el['id']
        label = soup.find('label', attrs={'for': field_id}) or el.find_parent('label')
        help_el = soup.find(id=el.get('aria-describedby', ''))
        fieldset = el.find_parent('fieldset')
        text = help_el.get_text(' ', strip=True) if help_el else ''
        label_text = label.get_text(' ', strip=True)
        fields.append(FormField(
            id=field_id, label=label_text, type=el.get('type', el.name),
            section=fieldset.legend.get_text(strip=True) if fieldset else 'Confirmation',
            required=el.has_attr('required'), instructions=text,
            options=[Option(value=o.get('value', ''), label=o.get_text(strip=True)) for o in el.select('option') if o.get('value')],
            constraints={k: el[k] for k in ('minlength', 'maxlength', 'min', 'max', 'pattern', 'step') if el.has_attr(k)},
            required_when=el.get('data-required-when'),
            evidence=FieldEvidence(selector=f'#{field_id}', label=label_text, instructions=text),
        ))
    return Form(id=form_id, title=soup.h1.get_text(strip=True),
                instructions=soup.find(id='instructions').get_text(' ', strip=True),
                source_hash=hashlib.sha256(html.encode()).hexdigest(), fields=fields,
                requirements=[Requirement(id=el['data-requirement'], text=el.get_text(' ', strip=True), selector=f'[data-requirement="{el["data-requirement"]}"]') for el in soup.select('[data-requirement]')],
                ambiguities=[el.get_text(' ', strip=True) for el in soup.select('[data-ambiguity]')])


def active(field: FormField, answers: dict) -> bool:
    if not field.required_when:
        return True
    key, value = field.required_when.split(':', 1)
    return answers.get(key) == value


def validate_answers(form: Form, answers: dict, complete: bool = True) -> dict[str, str]:
    errors = {}
    known = {f.id for f in form.fields}
    for unknown in answers.keys() - known:
        errors[unknown] = 'This field is not in the supported form.'
    for f in form.fields:
        if not active(f, answers):
            continue
        value = answers.get(f.id, '')
        required = f.required or bool(f.required_when)
        if f.type == 'checkbox':
            if value not in ('', False, True):
                errors[f.id] = 'Use the confirmation checkbox.'
            elif complete and required and value is not True:
                errors[f.id] = 'Please confirm this statement.'
            continue
        if not isinstance(value, str):
            errors[f.id] = 'Enter text for this field.'
            continue
        if not value.strip():
            if complete and required:
                errors[f.id] = 'Please complete this field.'
            continue
        c = f.constraints
        if f.options and value not in {o.value for o in f.options}:
            errors[f.id] = 'Choose one of the listed options.'
        elif 'minlength' in c and len(value) < int(c['minlength']):
            errors[f.id] = f'Use at least {c["minlength"]} characters.'
        elif 'maxlength' in c and len(value) > int(c['maxlength']):
            errors[f.id] = f'Use no more than {c["maxlength"]} characters.'
        elif 'pattern' in c and not re.fullmatch(c['pattern'], value):
            errors[f.id] = 'Use 4 to 20 letters, numbers or hyphens.'
        elif f.type == 'email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            errors[f.id] = 'Enter an email address such as name@example.org.'
        elif f.type == 'number':
            try:
                number = int(value)
                if not int(c.get('min', number)) <= number <= int(c.get('max', number)):
                    raise ValueError()
            except ValueError:
                errors[f.id] = f'Enter a whole number from {c.get("min")} to {c.get("max")}.'
    return errors
