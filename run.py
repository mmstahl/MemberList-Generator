import os
import sys
import argparse
import getpass
import subprocess
import paramiko
from dotenv import load_dotenv
from fetch_members import fetch_members

# --- Parse arguments ---
parser = argparse.ArgumentParser(description="Generate and publish the Yedidya member list.")
parser.add_argument(
    "--site",
    choices=["staging", "production"],
    default=None,
    help="Target site: staging or production",
)
args = parser.parse_args()

if args.site is None:
    print("Usage:")
    print("  python run.py --site staging      run against the staging site")
    print("  python run.py --site production   generate PDF and prompt before uploading")
    sys.exit(0)

# --- Load environment file for selected site ---
script_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(script_dir, f".env.{args.site}")

if not os.path.exists(env_file):
    print(f"Error: {env_file} not found. Create it from .env.example.")
    sys.exit(1)

load_dotenv(env_file)

SFTP_HOST = os.getenv("SFTP_HOST", "")
SFTP_USER = os.getenv("SFTP_USER", "")
SFTP_REMOTE_PATH = os.getenv("SFTP_REMOTE_PATH", "/srv/htdocs/wp-content/uploads/members_list.pdf")

SCRIPT_DIR = script_dir
PDF_LOCAL = os.path.join(SCRIPT_DIR, "members_list.pdf")


def step(n, total, label):
    print(f"[{n}/{total}] {label}")


def run_script(filename):
    result = subprocess.run(
        [sys.executable, filename],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or "(no output)"
        raise RuntimeError(f"{filename} failed:\n{error}")
    return result.stdout.strip()


def upload_pdf(sftp_password):
    if not SFTP_HOST or not SFTP_USER or not sftp_password:
        raise ValueError("Missing SFTP credentials. Check SFTP_HOST and SFTP_USER in .env")

    if not os.path.exists(PDF_LOCAL):
        raise FileNotFoundError(f"PDF not found at {PDF_LOCAL}")

    transport = paramiko.Transport((SFTP_HOST, 22))
    transport.connect(username=SFTP_USER, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        sftp.put(PDF_LOCAL, SFTP_REMOTE_PATH)
    finally:
        sftp.close()
        transport.close()


def main():
    is_production = args.site == "production"
    total = 4

    print(f"Site: {args.site.upper()}")
    print()

    wp_password = getpass.getpass("WordPress Application Password: ")
    sftp_password = None if is_production else getpass.getpass("SFTP Password: ")
    print()

    # Step 1 — Fetch members
    step(1, total, "Fetching members from WordPress...")
    try:
        count = fetch_members(wp_password)
        print(f"✓ Fetched {count} members")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Step 2 — Pre-process CSV
    step(2, total, "Pre-processing CSV...")
    try:
        out = run_script("pre_process.py")
        print(f"✓ {out}" if out else "✓ Pre-processing complete")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Step 3 — Generate PDF
    step(3, total, "Generating PDF...")
    try:
        out = run_script("MemberList Generator.py")
        print(f"✓ {out}" if out else "✓ PDF generated: members_list.pdf")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Step 4 — Upload via SFTP
    if is_production:
        # Open PDF for review before uploading
        print(f"\nPDF ready: {PDF_LOCAL}")
        os.startfile(PDF_LOCAL)
        answer = input("Upload to production? [y/N]: ").strip().lower()
        if answer != "y":
            print("Upload cancelled.")
            print("\nDone.")
            return
        sftp_password = getpass.getpass("SFTP Password: ")
        print()

    step(4, total, "Uploading to server...")
    try:
        upload_pdf(sftp_password)
        print(f"✓ Uploaded to {SFTP_REMOTE_PATH}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
