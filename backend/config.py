"""Explicit local/hosted settings. Hosted mode never silently falls back to local AI."""
from dataclasses import dataclass
import os
from urllib.parse import urlsplit


def loopback_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1')
            or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('The fictional portal must use an explicit HTTP loopback origin.')
    # Accessing port validates malformed port strings too.
    if not parsed.port:
        raise ValueError('The fictional portal requires an explicit port.')
    return value.rstrip('/')


@dataclass(frozen=True)
class Settings:
    mode: str
    provider: str
    origin: str
    portal: str
    model: str
    timeout: int
    ttl: int

    @property
    def hosted(self) -> bool:
        return self.mode == 'hosted'


def settings() -> Settings:
    mode = os.getenv('ACCESSPATH_MODE', 'local')
    provider = os.getenv('AI_PROVIDER', 'ollama')
    if mode not in ('local', 'hosted') or provider not in ('ollama', 'huggingface', 'groq'):
        raise ValueError('Choose ACCESSPATH_MODE local/hosted and AI_PROVIDER ollama/huggingface/groq.')
    hosted = mode == 'hosted'
    origin = os.getenv('FRONTEND_ORIGIN') or (os.getenv('RENDER_EXTERNAL_URL') if hosted else None) or 'http://127.0.0.1:3103'
    parsed = urlsplit(origin)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('FRONTEND_ORIGIN must be a single origin without credentials or a path.')
    if hosted and (parsed.scheme != 'https' or parsed.hostname in ('localhost', '127.0.0.1', '::1')):
        raise ValueError('Hosted mode requires its real HTTPS FRONTEND_ORIGIN or RENDER_EXTERNAL_URL.')
    if hosted and os.getenv('SYNTHETIC_DEMO') != 'true':
        raise ValueError('Hosted mode requires SYNTHETIC_DEMO=true.')
    if hosted and provider not in ('huggingface', 'groq'):
        raise ValueError('Hosted mode requires the explicitly configured hosted Qwen provider.')
    if provider == 'groq':
        model = os.getenv('GROQ_MODEL', 'qwen/qwen3.8-27b')
        if model != 'qwen/qwen3.8-27b':
            raise ValueError('Groq mode supports only the explicitly selected open-weight Qwen model.')
    elif provider == 'huggingface':
        model = os.getenv('HF_MODEL', 'Qwen/Qwen3-8B:nscale')
        if model not in ('Qwen/Qwen3-8B:nscale', 'Qwen/Qwen3-8B:featherless-ai'):
            raise ValueError('Select an approved Qwen3-8B inference provider; no arbitrary model routing is allowed.')
    else:
        model = os.getenv('OLLAMA_MODEL', 'qwen3:8b')
        if not model.startswith('qwen') or 'cloud' in model:
            raise ValueError('Local mode supports local Qwen models only.')
        loopback_origin(os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434'))
    timeout = int(os.getenv('AI_TIMEOUT_SECONDS', '120' if hosted else '240'))
    ttl = int(os.getenv('DEMO_TTL_SECONDS', '7200'))
    if not 10 <= timeout <= 240 or not 300 <= ttl <= 7200:
        raise ValueError('AI timeout must be 10–240 seconds and demo lifetime 300–7200 seconds.')
    return Settings(mode, provider, origin.rstrip('/'), loopback_origin(os.getenv('PORTAL_URL', 'http://127.0.0.1:9314')), model, timeout, ttl)


def validate_startup():
    config = settings()
    if config.provider == 'huggingface' and not os.getenv('HF_TOKEN', '').strip():
        raise ValueError('HF_TOKEN is required in the server environment. Never put it in NEXT_PUBLIC variables.')
    if config.provider == 'groq' and not os.getenv('GROQ_API_KEY', '').strip():
        raise ValueError('GROQ_API_KEY is required in the server environment. Never put it in NEXT_PUBLIC variables.')
    return config
