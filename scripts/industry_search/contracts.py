"""Shared contracts and stable identifiers; no model-generated approval states."""
from datetime import date, datetime, timezone
from functools import lru_cache
import hashlib
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from jsonschema import Draft202012Validator, FormatChecker

REPO = Path(__file__).resolve().parents[2]
VERSION = 'groundsignal.search-run.v1'
DIMENSIONS = ('upstream', 'downstream', 'competitors', 'investors', 'investments',
              'people', 'products', 'capacity', 'counterevidence')
TRACKING = {'fbclid', 'gclid', 'msclkid', 'spm', 'ref_src'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def digest(value):
    if not isinstance(value, (bytes, str)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, str):
        value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    import os
    import tempfile
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


@lru_cache(maxsize=8)
def validator(name):
    schema = read_json(REPO / 'schemas' / (name + '.v1.schema.json'))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def check(name, data):
    errors = sorted(validator(name).iter_errors(data), key=lambda x: str(list(x.path)))
    if errors:
        error = errors[0]
        # Validation messages must not echo secrets or untrusted response bodies.
        raise ValueError(f'{name}: {list(error.path)} ({error.validator})')
    return data


def canonical_url(url):
    """Preserve semantic query parameters; remove only recognized tracking keys."""
    if not isinstance(url, str) or any(ord(c) < 32 for c in url):
        raise ValueError('invalid_url')
    parts = urlsplit(url)
    if parts.scheme.lower() not in {'http', 'https'} or not parts.hostname:
        raise ValueError('invalid_url')
    if parts.username or parts.password or '\\' in url:
        raise ValueError('credential_or_ambiguous_url')
    host = parts.hostname.encode('idna').decode('ascii').lower().rstrip('.')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if host in {'localhost', 'metadata.google.internal'} or host.endswith(('.localhost', '.local')):
        raise ValueError('private_url')
    if address and not address.is_global:
        raise ValueError('private_url')
    port = parts.port
    if port and port not in {80, 443}:
        raise ValueError('non_web_port')
    authority = '[' + host + ']' if ':' in host else host
    if port and port != {'http': 80, 'https': 443}[parts.scheme.lower()]:
        authority += ':' + str(port)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith('utm_') and k.lower() not in TRACKING]
    return urlunsplit((parts.scheme.lower(), authority, parts.path or '/', urlencode(sorted(query)), ''))


def hostname(url):
    return urlsplit(canonical_url(url)).hostname


def domain_matches(host, domain):
    return host == domain or host.endswith('.' + domain)


def target_check(data):
    check('research-target', data)
    for value in [data['name'], *data['aliases']]:
        if not value.strip() or '"' in value or '\n' in value:
            raise ValueError('target_name_must_be_literal')
    for domain in data['official_domains']:
        if hostname('https://' + domain) != domain:
            raise ValueError('official_domain_must_be_hostname')
    for key in ('after', 'before'):
        if data['time_range'][key]:
            date.fromisoformat(data['time_range'][key])
    if all(data['time_range'].values()) and data['time_range']['after'] >= data['time_range']['before']:
        raise ValueError('invalid_time_range')
    for url in data['seed_urls']:
        canonical_url(url)
    return data


def aliases(target):
    return list(dict.fromkeys([target['name'], *target['aliases']]))


def mentions(text, target):
    """English aliases use word boundaries: AMD must not match an unrelated word."""
    compact = re.sub(r'\s+', ' ', text).casefold()
    for name in aliases(target):
        name = re.sub(r'\s+', ' ', name).casefold()
        if re.fullmatch(r'[a-z0-9 .&-]+', name):
            if re.search(r'(?<![\w])' + re.escape(name) + r'(?![\w])', compact):
                return True
        elif name in compact:
            return True
    return False


def config_check(config):
    check('research-config', config)
    for role, model in config['models'].items():
        if not model['enabled']:
            continue
        parts = urlsplit(model['base_url'])
        if parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError('model_endpoint_must_not_contain_credentials_or_query')
        local = parts.hostname in {'localhost', '127.0.0.1', '::1'}
        if not parts.hostname or (parts.scheme != 'https' and not (local and parts.scheme == 'http')):
            raise ValueError('model_endpoint_requires_https_or_loopback')
        # Prevent request overrides from bypassing model identity, budget or tools policy.
        if set(model['extra_body']) - {'thinking', 'reasoning_effort', 'chat_template_kwargs', 'temperature'}:
            raise ValueError('unsupported_model_extra_body')
    return config
