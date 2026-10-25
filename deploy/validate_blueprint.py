"""Validate syntax against Render's current official schema without applying changes."""
import hashlib
import json
from pathlib import Path
import urllib.request
import jsonschema
import yaml

url = 'https://render.com/schema/render.yaml.json'
with urllib.request.urlopen(url, timeout=30) as response:
    raw = response.read()
jsonschema.validate(yaml.safe_load(Path('render.yaml').read_text(encoding='utf-8')), json.loads(raw))
print(json.dumps({'schema_url': url, 'schema_sha256': hashlib.sha256(raw).hexdigest(), 'valid': True,
                  'scope': 'Structural validation only; no resources created or changed.'}))
