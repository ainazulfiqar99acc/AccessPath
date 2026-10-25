"""Hosted boundary tests. Provider responses here are explicit test doubles, not demo evidence."""
import json
import time
import httpx
import pytest
from fastapi.testclient import TestClient
from backend import ai, automation
from backend.config import settings, validate_startup, loopback_origin
from backend.demo import SAMPLES
from backend.main import app
from backend.parser import parse_form
from backend.security import COOKIE
from backend.storage import db, purge_expired

ORIGIN = 'https://accesspath.example'


@pytest.fixture
def hosted(tmp_path, monkeypatch):
    for name, value in {
        'ACCESSPATH_MODE': 'hosted', 'SYNTHETIC_DEMO': 'true', 'AI_PROVIDER': 'huggingface',
        'FRONTEND_ORIGIN': ORIGIN, 'HF_TOKEN': 'test-only-provider-credential',
        'HF_MODEL': 'Qwen/Qwen3-8B:nscale', 'ACCESSPATH_DATA': str(tmp_path),
        'DEMO_TTL_SECONDS': '7200', 'PORTAL_URL': 'http://127.0.0.1:9314',
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(ai, 'VERIFIED', set())
    with TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}) as client:
        yield client


def create(client):
    response = client.post('/api/sessions', json={'form_id': 'scholarship', 'synthetic_ack': True})
    assert response.status_code == 200, response.text
    return '/api/sessions/' + response.json()['id']


def values():
    return {**SAMPLES['scholarship'], 'study_level': 'undergraduate', 'has_support': 'no', 'declaration': True}


def save(client, url):
    result = client.put(url + '/answers', json={'answers': values(), 'checklist': ['student_record', 'enrollment_proof']})
    assert result.status_code == 200, result.text


def test_hosted_configuration_fails_closed(hosted, monkeypatch):
    assert validate_startup().hosted
    for name, invalid in [('SYNTHETIC_DEMO', 'false'), ('AI_PROVIDER', 'ollama'),
                          ('FRONTEND_ORIGIN', 'http://accesspath.example'),
                          ('HF_MODEL', 'google/gemma'), ('PORTAL_URL', 'https://agency.example'),
                          ('AI_TIMEOUT_SECONDS', '9999'), ('HF_TOKEN', '')]:
        with monkeypatch.context() as patch:
            patch.setenv(name, invalid)
            with pytest.raises(ValueError):
                validate_startup()


@pytest.mark.parametrize('url', [
    'https://127.0.0.1:9314', 'http://agency.example:9314', 'http://127.0.0.1:9314/path',
    'http://person:password@127.0.0.1:9314', 'http://127.0.0.1:9314?target=elsewhere',
])
def test_loopback_policy_rejects_unapproved_origins(url):
    with pytest.raises(ValueError):
        loopback_origin(url)


def test_browser_cookie_and_owner_isolation_for_every_draft_action(hosted):
    url = create(hosted)
    save(hosted, url)
    token = hosted.post(url + '/prepare').json()['action_token']
    cookie = hosted.get('/api/forms').request.headers.get('cookie', '')
    assert COOKIE in cookie
    with TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}) as stranger:
        assert stranger.get(url).status_code == 404
        assert stranger.put(url + '/answers', json={'answers': values()}).status_code == 404
        assert stranger.post(url + '/prepare').status_code == 404
        assert stranger.post(url + '/submit', json={'confirmation': True, 'action_token': token}).status_code == 404
        assert stranger.delete(url).status_code == 404
    assert hosted.get(url).json()['answers']['full_name'] == SAMPLES['scholarship']['full_name']
    response = hosted.get('/api/health')
    assert response.headers['cache-control'] == 'no-store'
    hosted.cookies.clear()
    set_cookie = hosted.get('/api/health').headers['set-cookie'].lower()
    assert all(flag in set_cookie for flag in ['__host-accesspath-browser=', 'httponly', 'secure', 'samesite=strict', 'path=/'])
    assert hosted.get(url).status_code == 404


def test_synthetic_acknowledgement_and_no_personal_text_persisted(hosted):
    assert hosted.post('/api/sessions', json={'form_id': 'scholarship'}).status_code == 422
    url = create(hosted)
    rejected = hosted.put(url + '/answers', json={'answers': {'full_name': 'A Real Person', 'email': 'private@personal.example'}})
    assert rejected.status_code == 422
    assert hosted.get(url).json()['answers'] == {}
    save(hosted, url)
    with db() as con:
        row = dict(con.execute('SELECT * FROM sessions').fetchone())
        assert 'A Real Person' not in json.dumps(row)
        assert row['owner_hash'] and not any(secret in json.dumps(row) for secret in ['test-only-provider-credential', hosted.cookies.get(COOKIE)])


@pytest.mark.parametrize('answers', [{'study_level': 'Private personal detail'}, {'has_support': 'private@example.org'}, {'declaration': 'Private personal detail'}])
def test_public_choice_fields_cannot_be_used_to_store_arbitrary_text(hosted, answers):
    url = create(hosted)
    assert hosted.put(url + '/answers', json={'answers': answers}).status_code == 422
    assert hosted.get(url).json()['answers'] == {}


def test_public_count_is_source_bounded_even_during_draft_save(hosted):
    result = hosted.post('/api/sessions', json={'form_id': 'benefit', 'synthetic_ack': True}).json()
    url = '/api/sessions/' + result['id']
    for count in ['Private personal detail', '2.5', '999']:
        assert hosted.put(url + '/answers', json={'answers': {'household_size': count}}).status_code == 422
    assert hosted.put(url + '/answers', json={'answers': {'household_size': '3'}}).status_code == 200


def test_hosted_csrf_requires_exact_origin(hosted):
    for origin in ['https://untrusted.example', 'null', ORIGIN + '.attacker.example']:
        assert hosted.post('/api/sessions', headers={'Origin': origin}, json={'form_id': 'scholarship', 'synthetic_ack': True}).status_code == 403
    hosted.headers.pop('origin')
    assert hosted.post('/api/sessions', json={'form_id': 'scholarship', 'synthetic_ack': True}).status_code == 403


def test_expired_data_and_audit_are_removed(hosted):
    url = create(hosted)
    save(hosted, url)
    with db() as con:
        con.execute('UPDATE sessions SET expires_at=?', (time.time() - 1,))
    assert hosted.get(url).status_code == 404
    with db() as con:
        assert con.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 0
        assert con.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0


def test_expiring_draft_cannot_start_browser_submission(hosted, monkeypatch):
    url = create(hosted); save(hosted, url)
    token = hosted.post(url + '/prepare').json()['action_token']
    with db() as con:
        con.execute('UPDATE sessions SET expires_at=?', (time.time() + 30,))
    assert hosted.post(url + '/prepare').status_code == 409
    assert hosted.post(url + '/submit', json={'confirmation': True, 'action_token': token}).status_code == 409


def test_hosted_draft_count_and_actual_body_limits(hosted):
    for _ in range(3):
        create(hosted)
    assert hosted.post('/api/sessions', json={'form_id': 'scholarship', 'synthetic_ack': True}).status_code == 429
    assert hosted.post('/api/sessions', content=b'x' * 30001).status_code == 413
    assert hosted.post('/api/sessions', content=iter([b'x' * 15000, b'x' * 15001])).status_code == 413
    assert hosted.post('/api/sessions', content=b'{}', headers={'content-length': 'bad'}).status_code == 400


def test_public_rate_limit_survives_browser_cookie_rotation(hosted):
    with db() as con:
        con.execute('INSERT INTO rate_limits VALUES(?,?,?,?)', ('global', int(time.time()) // 60, 600, time.time() + 60))
    response = hosted.get('/api/forms')
    assert response.status_code == 429 and 'retry-after' in response.headers
    hosted.cookies.clear()
    assert hosted.get('/api/forms').status_code == 429
    assert hosted.get('/api/health').status_code == 200


def test_automation_allows_only_fixed_fictional_paths():
    origin = automation.PORTAL_URL
    assert automation.allowed_request(origin + '/forms/scholarship', 'scholarship')
    assert automation.allowed_request(origin + '/forms/scholarship/submit', 'scholarship')
    for url in ['https://www.gov.uk', origin + '/admin', origin + '/forms/benefit',
                origin + '/forms/scholarship?redirect=https://agency.example', origin.replace('9314', '9999') + '/forms/scholarship']:
        assert not automation.allowed_request(url, 'scholarship')


def mock_provider(monkeypatch, handler):
    original = httpx.AsyncClient
    def client(**kwargs):
        return original(**kwargs, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(ai.httpx, 'AsyncClient', client)


def test_hosted_provider_receives_only_source_and_checked_output_is_cached(hosted, monkeypatch):
    url = create(hosted); save(hosted, url)
    calls = []
    def provider(request):
        assert str(request.url) == ai.HF_CHAT
        payload = json.loads(request.content)
        assert payload['model'] == 'Qwen/Qwen3-8B:nscale'
        assert 'Synthetic Demo Student' not in request.content.decode()
        assert 'student@example.org' not in request.content.decode()
        assert payload['response_format']['type'] == 'json_schema'
        calls.append(payload)
        form = parse_form('scholarship')
        output = {'fields': [{'field_id': f.id, 'plain_label': f.label, 'explanation': f.instructions or 'Confirm this fictional demonstration.'} for f in form.fields]}
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(output)}}]})
    mock_provider(monkeypatch, provider)
    first = hosted.post('/api/forms/scholarship/explain')
    assert first.status_code == 200 and not first.json()['cached']
    assert first.json()['local'] is False and first.json()['model_digest'] is None
    assert hosted.post('/api/forms/scholarship/explain').json()['cached'] is True
    assert len(calls) == 1
    assert hosted.get('/api/health').json()['model']['verified'] is True


@pytest.mark.parametrize('failure', ['unauthorized', 'invalid_json', 'unsupported_claim', 'timeout'])
def test_provider_errors_are_sanitized_and_no_fallback_is_invented(hosted, monkeypatch, failure):
    def provider(request):
        if failure == 'unauthorized':
            return httpx.Response(401, json={'error': 'test-only-provider-credential private account details'})
        if failure == 'timeout':
            raise httpx.ReadTimeout('test-only-provider-credential', request=request)
        content = 'not JSON' if failure == 'invalid_json' else json.dumps({'fields': [{'field_id': f.id, 'plain_label': f.label, 'explanation': 'You are eligible and approved.'} for f in parse_form('scholarship').fields]})
        return httpx.Response(200, json={'choices': [{'message': {'content': content}}]})
    mock_provider(monkeypatch, provider)
    response = hosted.post('/api/forms/scholarship/explain')
    assert response.status_code == 502
    assert 'Original instructions remain usable' in response.text
    assert 'test-only-provider-credential' not in response.text
    with db() as con:
        assert con.execute('SELECT COUNT(*) FROM explanations').fetchone()[0] == 0


def test_health_discloses_hosted_storage_and_unverified_inference(hosted):
    health = hosted.get('/api/health').json()
    assert health['portal_url'] == ORIGIN
    assert health['model']['local'] is False and health['model']['verified'] is False
    assert health['deployment']['synthetic_only'] is True
    assert health['deployment']['draft_ttl_seconds'] == 7200


def test_portal_also_rejects_personal_text(hosted):
    from backend.portal import app as portal
    with TestClient(portal) as client:
        assert client.get('/healthz').json()['fictional'] is True
        assert 'SYNTHETIC DEMO' in client.get('/forms/scholarship').text
        response = client.post('/forms/scholarship/submit', data={'full_name': 'A Real Person'})
        assert response.status_code == 422
        response = client.post('/forms/scholarship/submit', data={**values(), 'declaration': 'on'})
        assert response.status_code == 200 and 'id="receipt">AP-' in response.text


def test_readiness_checks_internal_services_without_billable_inference(hosted, monkeypatch):
    original = httpx.AsyncClient
    calls = []
    def portal(request):
        calls.append(str(request.url))
        assert str(request.url) == settings().portal + '/healthz'
        return httpx.Response(200, json={'status': 'ok'})
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(portal)))
    assert hosted.get('/api/readyz').status_code == 200
    assert len(calls) == 1
    def unavailable(request):
        return httpx.Response(503)
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(unavailable)))
    assert hosted.get('/api/readyz').status_code == 503


def test_groq_free_adapter_uses_selected_model_and_source_only(hosted, monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'groq')
    monkeypatch.setenv('GROQ_API_KEY', 'test-only-groq-credential')
    def provider(request):
        assert str(request.url) == ai.GROQ_CHAT
        body = json.loads(request.content)
        assert body['model'] == 'qwen/qwen3.8-27b' and body['max_tokens'] == 900
        assert body['reasoning_effort'] == 'none'
        assert body['response_format']['json_schema']['strict'] is True
        assert 'student@example.org' not in request.content.decode()
        form = parse_form('scholarship')
        output = {'fields': [{'field_id': f.id, 'plain_label': f.label, 'explanation': f.instructions or 'Confirm this fictional demonstration.'} for f in form.fields]}
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(output)}}]})
    mock_provider(monkeypatch, provider)
    result = hosted.post('/api/forms/scholarship/explain')
    assert result.status_code == 200 and result.json()['provider'] == 'groq'
    assert result.json()['local'] is False


def test_groq_quota_failure_is_clear_and_never_falls_back(hosted, monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'groq')
    monkeypatch.setenv('GROQ_API_KEY', 'test-only-groq-credential')
    calls = []
    def limited(request):
        calls.append(str(request.url)); return httpx.Response(429)
    mock_provider(monkeypatch, limited)
    result = hosted.post('/api/forms/scholarship/explain')
    assert result.status_code == 429 and result.headers['retry-after'] == '60'
    assert 'free-tier rate limit' in result.text and calls == [ai.GROQ_CHAT]


def test_exported_frontend_gateway_preserves_api_and_portal_boundaries(hosted, tmp_path):
    from backend.web import WebApplication
    assets = tmp_path / 'export'
    assets.mkdir(); (assets/'index.html').write_text('<h1>Explicit static UI test fixture</h1>')
    chunks = assets/'_next/static'; chunks.mkdir(parents=True)
    (chunks/'fixture.js').write_text('/* Explicit test fixture */')
    web = WebApplication(assets)
    with TestClient(web, base_url=ORIGIN, headers={'Origin': ORIGIN}) as client:
        response = client.get('/')
        assert response.status_code == 200 and 'static UI test fixture' in response.text
        assert response.headers['x-frame-options'] == 'DENY' and response.headers['cache-control'] == 'no-store'
        assert 'immutable' in client.get('/_next/static/fixture.js').headers['cache-control']
        assert client.get('/missing').status_code == 404
        assert client.get('/forms/scholarship').status_code == 200
        assert client.get('/portal.css').status_code == 200
        url = create(client); save(client, url)
        assert client.get(url).json()['answers']['email'] == 'student@example.org'
        assert client.delete(url).status_code == 200
        assert client.get(url).status_code == 404
