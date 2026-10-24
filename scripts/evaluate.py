"""Run sequential REAL Qwen inference on source forms. Contains no applicant data."""
import asyncio
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from backend.ai import explain, model_status
from backend.parser import parse_form

EXPECTED = {
    'scholarship': ['full_name','email','study_level','enrollment','has_support','support_details','statement','declaration'],
    'community': ['full_name','email','workshop','access_notes','declaration'],
    'benefit': ['full_name','email','household_size','topic','declaration'],
}


async def main():
    results = {'measured_at':datetime.now(timezone.utc).isoformat(), 'python':platform.python_version(),
               'model_status':await model_status(), 'synthetic_forms_only':True, 'forms':[]}
    for identifier, expected in EXPECTED.items():
        form = parse_form(identifier)
        assert [f.id for f in form.fields] == expected
        output = await explain(form, refresh=True)
        results['forms'].append({'form_id':identifier,'field_ids_exact':True,
                                 'field_count':len(form.fields),'required_count':sum(f.required for f in form.fields),
                                 'conditional_count':sum(bool(f.required_when) for f in form.fields),
                                 'requirement_count':len(form.requirements),'explanation':output})
        print(f'{identifier}: {len(form.fields)} fields; real inference {output["seconds"]} seconds',flush=True)
    target = Path('docs/evaluation-results.json')
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(f'Measured evidence written to {target}')


if __name__=='__main__':
    asyncio.run(main())
