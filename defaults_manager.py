"""
Persistent defaults manager for Yedidya tools.
Stores non-sensitive defaults (file paths, SFTP paths) in:
  %APPDATA%/YedidyaPortal/config.json

Both run.py (standalone) and the portal GUI read/write the same file.
"""
import json
import os
import sys

_CONFIG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'YedidyaPortal')
_CONFIG_PATH = os.path.join(_CONFIG_DIR, 'config.json')

# When running as a PyInstaller .exe, use the folder containing the .exe.
# When running standalone from source, use the script's own directory.
if getattr(sys, 'frozen', False):
    _SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SEED_DEFAULTS = {
    'members_list': {
        'raw_csv_path':                os.path.join(_SCRIPT_DIR, 'members data raw.csv'),
        'processed_csv_path':          os.path.join(_SCRIPT_DIR, 'pre-processing output.csv'),
        'pdf_path':                    os.path.join(_SCRIPT_DIR, 'members_list.pdf'),
        'staging_sftp_remote_path':    '/srv/htdocs/wp-content/uploads/members_list.pdf',
        'production_sftp_remote_path': '/srv/htdocs/wp-content/uploads/members_list.pdf',
    },
    'portal': {
        'environment': 'staging',
    },
    'db_extract': {
        'presets': json.dumps({
            'All Member Fields': (
                'role, first_name, last_name, userlatin, usertitle, yourgender, '
                'privacy_approval, contact_list_privacy_setting, home_address, '
                'cellphone1, homephone, bmitzvah, usercast, hebrewname, '
                'havepartner, partnerfirst, '
                'partnerlast, partnerlatin, partnertitle, partnergender, '
                'partnerphone, partneremail, partnerbmparsha, partnercast, '
                'partnerhebname, havechildren, child1nameb, child1gender, '
                'child1birthdate, child1hebbirthdate, child2name, child2gender2, '
                'child1birthdate2, child2hebbirthdate, child3name, child3gender, '
                'child3birthdate, child3hebbirthdate, child4name, child4gender, '
                'child4birthdate, child4hebbirthdate, child5name, child5gender, '
                'child5birthdate, child5hebbirthdate, child6name, child6gender, '
                'child6birthdate, child6hebbirthdate6, haveyahrzeits, '
                'deceased1name, yahrzeit1relationship, yahrzeit1date, '
                'deceased2name, yahrzeit2relationship, yahrzeit2date, '
                'deceased3name, yahrzeit3relationship, yahrzeit3date, '
                'deceased4name, yahrzeit4relationship, yahrzeit4date, '
                'havemoreyahrzeits, deceased5name, yahrzeit5relationship, '
                'yahrzeit5date, deceased6name, yahrzeit6relationship, '
                'yahrzeit6date, deceased7name, yahrzeit7relationship, '
                'yahrzeit7date, deceased8name, yahrzeit8relationship, '
                'yahrzeit8date, deceased9name, yahrzeit9relationship, '
                'yahrzeit9date, deceased10name, yahrzeit10relationship, '
                'yahrzeit10date, deceased11name, yahrzeit11relationship, '
                'yahrzeit11date, deceased12name, yahrzeit12relationship, '
                'yahrzeit12date, haveevents, event1type, event1date, event1desc, '
                'event2type, event2date, event2desc, event3type, event3date, '
                'event3desc, event4type, event4date, event4desc'
            ),
        }, ensure_ascii=False),
    },
}


def _load():
    if not os.path.exists(_CONFIG_PATH):
        return {}
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data):
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get(action, key):
    """Return stored value for action/key, falling back to seed default."""
    data = _load()
    seed = _SEED_DEFAULTS.get(action, {}).get(key, '')
    return data.get(action, {}).get(key, seed)


def set_default(action, key, value):
    """Persist a new default value for action/key."""
    data = _load()
    if action not in data:
        data[action] = {}
    data[action][key] = value
    _save(data)


def get_all(action):
    """Return all defaults for an action (stored values merged over seeds)."""
    data = _load()
    result = _SEED_DEFAULTS.get(action, {}).copy()
    result.update(data.get(action, {}))
    return result
