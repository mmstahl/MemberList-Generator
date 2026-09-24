"""
Yedidya Members List — standalone runner.

Credentials are stored in Windows Credential Manager (via keyring).
File paths are stored in %APPDATA%\YedidyaPortal\config.json and shown
as defaults; press Enter to accept or type a new value to update.
"""
import os
import sys
import importlib.util
import getpass
import keyring

import defaults_manager as dm
from fetch_members import fetch_members
from pre_process import pre_process
from upload import upload_sftp

KEYRING_SERVICE = 'YedidyaPortal'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------

def _get_or_prompt(key, label, sensitive=False):
    """Return stored credential, or prompt and save if missing."""
    value = keyring.get_password(KEYRING_SERVICE, key)
    if not value:
        if sensitive:
            value = getpass.getpass(f"{label}: ")
        else:
            value = input(f"{label}: ").strip()
        if value:
            keyring.set_password(KEYRING_SERVICE, key, value)
    return value or ''


def _load_credentials():
    print("Checking credentials...")
    wp_url       = _get_or_prompt('wp_url',       'WordPress URL')
    wp_user      = _get_or_prompt('wp_user',      'WordPress username')
    wp_password  = _get_or_prompt('wp_password',  'WordPress application password', sensitive=True)
    sftp_host    = _get_or_prompt('sftp_host',    'SFTP host')
    sftp_user    = _get_or_prompt('sftp_user',    'SFTP username')
    sftp_password = _get_or_prompt('sftp_password', 'SFTP password', sensitive=True)
    return wp_url, wp_user, wp_password, sftp_host, sftp_user, sftp_password


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _prompt_path(label, action, key):
    """Show current default, let user accept or override. Saves new value."""
    current = dm.get(action, key)
    display = f" [{current}]" if current else ""
    value = input(f"{label}{display}: ").strip()
    if not value:
        return current
    if value != current:
        dm.set_default(action, key, value)
    return value


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def step(n, total, label):
    print(f"\n[{n}/{total}] {label}")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "memberlist_generator",
        os.path.join(SCRIPT_DIR, "MemberList Generator.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    print("Yedidya Members List Generator")
    print("=" * 34)

    wp_url, wp_user, wp_password, sftp_host, sftp_user, sftp_password = _load_credentials()

    print("\nFile paths (press Enter to accept defaults):")
    raw_csv_path       = _prompt_path("Raw CSV output",    'members_list', 'raw_csv_path')
    processed_csv_path = _prompt_path("Processed CSV",     'members_list', 'processed_csv_path')
    pdf_path           = _prompt_path("PDF output",        'members_list', 'pdf_path')
    sftp_remote_path   = _prompt_path("SFTP remote path",  'members_list', 'sftp_remote_path')
    total = 4

    # Step 1 — Fetch
    step(1, total, "Fetching members from WordPress...")
    try:
        count = fetch_members(wp_url, wp_user, wp_password, raw_csv_path)
        print(f"  ✓ Fetched {count} members")
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    # Step 2 — Pre-process
    step(2, total, "Pre-processing CSV...")
    try:
        count = pre_process(raw_csv_path, processed_csv_path)
        print(f"  ✓ Processed {count} entries")
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    # Step 3 — Generate PDF
    step(3, total, "Generating PDF...")
    try:
        generator = _load_generator()
        generator.generate_pdf(processed_csv_path, pdf_path, fonts_dir=SCRIPT_DIR)
        print(f"  ✓ PDF generated: {pdf_path}")
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    # Step 4 — Upload
    print(f"\nPDF ready: {pdf_path}")
    try:
        os.startfile(pdf_path)
    except Exception:
        pass
    answer = input("Upload to server? [y/N]: ").strip().lower()
    if answer != "y":
        print("Upload cancelled.")
        print("\nDone.")
        return

    step(4, total, "Uploading to server...")
    try:
        upload_sftp(pdf_path, sftp_host, sftp_user, sftp_password, sftp_remote_path)
        print(f"  ✓ Uploaded to {sftp_remote_path}")
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
