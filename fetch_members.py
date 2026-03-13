import os
import csv
import getpass
import requests
from dotenv import load_dotenv

COLUMNS = [
    "user_login", "user_email", "first_name", "last_name",
    "partnerfirst", "partnerlast", "partneremail",
    "cellphone1", "partnerphone", "homephone",
    "home_address", "yourgender", "partnergender",
    "contact_list_privacy_setting", "privacy_approval",
]

OUTPUT_FILE = "members data raw.csv"


def fetch_members(wp_password):
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_user = os.getenv("WP_USER", "")

    if not wp_url or not wp_user or not wp_password:
        raise ValueError("Missing credentials. Check WP_URL and WP_USER in .env")

    endpoint = f"{wp_url}/wp-json/yedidya/v1/members"

    response = requests.get(
        endpoint,
        auth=(wp_user, wp_password),
        timeout=30,
    )

    if response.status_code == 401:
        raise ConnectionError("401 Unauthorized — wrong username or password")
    if response.status_code == 403:
        raise ConnectionError("403 Forbidden — make sure the WordPress user has admin (edit_users) capability")
    if response.status_code == 404:
        raise ConnectionError("404 Not Found — is the plugin installed and activated?")
    if not response.ok:
        raise ConnectionError(f"{response.status_code} Error — {response.text[:200]}")

    members = response.json()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(members)

    return len(members)


if __name__ == "__main__":
    load_dotenv()
    password = getpass.getpass("WordPress Application Password: ")
    count = fetch_members(password)
    print(f"✓ Fetched {count} members from WordPress → {OUTPUT_FILE}")
