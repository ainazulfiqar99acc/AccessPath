import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend import automation
from backend.parser import parse_form, validate_answers, active
from backend.schema import ModelExplanation, Explanation
from backend.ai import validate_explanations


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('ACCESSPATH_DATA', str(tmp_path))
    with TestClient(app) as c:
        yield c


def answers():
    return {'full_name':'Synthetic Test Student','email':'student@example.org','study_level':'undergraduate',
            'enrollment':'TEST-42','has_support':'no','statement':'I want to study accessible design and build useful tools.','declaration':True}


def draft(client, values=None):
    result = client.post('/api/sessions', json={'form_id':'scholarship'}).json()
    assert client.put(f'/api/sessions/{result["id"]}/answers', json={'answers':values or answers(),'checklist':['student_record','enrollment_proof']}).status_code == 200
    return result['id']


def test_extraction_and_optional_fields():
    form = parse_form('scholarship')
    assert len(form.fields) == 8
    assert [f.id for f in form.fields if f.required] == ['full_name','email','study_level','enrollment','has_support','statement','declaration']
    assert form.fields[3].constraints['pattern'] == '[A-Za-z0-9-]{4,20}'
    assert len(form.requirements) == 2
    assert len(form.ambiguities) == 1
    assert not next(f for f in parse_form('community').fields if f.id == 'access_notes').required
    assert parse_form('benefit').fields[2].constraints == {'min':'1','max':'20','step':'1'}


def test_conditional_constraints():
    form = parse_form('scholarship')
    a = answers()
    assert validate_answers(form,a) == {}
    a['has_support']='yes'
    assert 'support_details' in validate_answers(form,a)
    a['support_details']='Synthetic provider'
    a['enrollment']='!bad'
    a['email']='not-email'
    assert set(validate_answers(form,a)) == {'email','enrollment'}


def test_numbers_and_boolean_validation():
    form = parse_form('benefit')
    a={'full_name':'Synthetic Student','email':'a@example.org','household_size':'2.5','topic':'food','declaration':'yes'}
    assert set(validate_answers(form,a)) == {'household_size','declaration'}
    a['household_size']='21'
    assert 'household_size' in validate_answers(form,a)


def test_consent_and_token_invalidation(client):
    identifier = draft(client)
    url=f'/api/sessions/{identifier}'
    assert client.post(url+'/submit',json={'confirmation':True,'action_token':'x'*32}).status_code == 409
    reviewed=client.post(url+'/prepare').json()
    assert client.post(url+'/submit',json={'confirmation':False,'action_token':reviewed['action_token']}).status_code == 403
    client.put(url+'/answers',json={'answers':answers(),'checklist':['student_record','enrollment_proof']})
    assert client.post(url+'/submit',json={'confirmation':True,'action_token':reviewed['action_token']}).status_code == 409


def test_invalid_values_and_checklist_block_review(client):
    a=answers();a['email']='bad'
    identifier=draft(client,a)
    assert client.post(f'/api/sessions/{identifier}/prepare').status_code==422
    client.put(f'/api/sessions/{identifier}/answers',json={'answers':answers(),'checklist':[]})
    assert client.post(f'/api/sessions/{identifier}/prepare').status_code==422


def test_unknown_fields_rejected(client):
    identifier=draft(client)
    assert client.put(f'/api/sessions/{identifier}/answers',json={'answers':{'invented':'value'}}).status_code==422
    assert client.post('/api/sessions',json={'form_id':'https://example.org'}).status_code==422


def test_audit_deletion_and_anti_csrf(client):
    identifier=draft(client)
    result=client.get(f'/api/sessions/{identifier}').json()
    log=json.dumps(result['events'])
    assert 'student@example.org' not in log and 'Synthetic Test Student' not in log
    assert client.delete(f'/api/sessions/{identifier}',headers={'Origin':'https://untrusted.example'}).status_code==403
    assert client.delete(f'/api/sessions/{identifier}').status_code==200
    assert client.get(f'/api/sessions/{identifier}').status_code==404


def test_inactive_answers_removed(client):
    a=answers();a['support_details']='Should not be sent'
    identifier=draft(client,a)
    assert 'support_details' not in client.get(f'/api/sessions/{identifier}').json()['answers']


def test_actual_automation_gate_and_replay(client,monkeypatch):
    calls=[]
    async def controlled_stub(form,a):
        calls.append(form.id)
        return 'AP-UNIT-TEST'
    monkeypatch.setattr(automation,'fill_and_submit',controlled_stub)
    identifier=draft(client);url=f'/api/sessions/{identifier}'
    token=client.post(url+'/prepare').json()['action_token']
    assert calls == []
    assert client.post(url+'/submit',json={'confirmation':True,'action_token':token}).json()['receipt']=='AP-UNIT-TEST'
    assert calls == ['scholarship']
    assert client.post(url+'/submit',json={'confirmation':True,'action_token':token}).status_code==409
    assert client.put(url+'/answers',json={'answers':answers()}).status_code==409


def test_model_output_guards():
    form=parse_form('scholarship')
    output=ModelExplanation(fields=[Explanation(field_id=f.id,plain_label=f.label,explanation=f.instructions or 'Confirm this fictional demonstration.') for f in form.fields])
    validate_explanations(form,output)
    output.fields[0].explanation='Pay 999 dollars to continue.'
    with pytest.raises(ValueError):validate_explanations(form,output)
    output.fields[0].explanation='You are eligible for a scholarship.'
    with pytest.raises(ValueError):validate_explanations(form,output)
    output.fields.pop()
    with pytest.raises(ValueError):validate_explanations(form,output)


def test_expiry_source_change_and_failed_automation(client,monkeypatch):
    from backend.storage import db
    identifier=draft(client);url=f'/api/sessions/{identifier}'
    token=client.post(url+'/prepare').json()['action_token']
    with db() as con:
        con.execute('UPDATE sessions SET token_at=0 WHERE id=?',(identifier,))
    assert client.post(url+'/submit',json={'confirmation':True,'action_token':token}).status_code==409
    token=client.post(url+'/prepare').json()['action_token']
    async def fail(form,a):raise RuntimeError('Test browser unavailable')
    monkeypatch.setattr(automation,'fill_and_submit',fail)
    assert client.post(url+'/submit',json={'confirmation':True,'action_token':token}).status_code==502
    assert client.get(url).json()['status']=='draft'
    assert client.post(url+'/submit',json={'confirmation':True,'action_token':token}).status_code==409
    with db() as con:
        con.execute("UPDATE sessions SET source_hash='changed' WHERE id=?",(identifier,))
    assert client.post(url+'/prepare').status_code==409
