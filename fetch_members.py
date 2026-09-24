import csv
import requests

COLUMNS = [
    "user_login", "user_email", "first_name", "last_name",
    "havepartner", "partnerfirst", "partnerlast", "partneremail",
    "cellphone1", "partnerphone", "homephone",
    "home_address", "yourgender", "partnergender",
    "contact_list_privacy_setting", "privacy_approval",
    "user_status",
]

API_ENDPOINT = '/wp-json/yedidya/v1/members'


def fetch_members(wp_url, wp_user, wp_password, output_path):
    """Fetch members from WordPress and write to CSV. Returns member count."""
    endpoint = f"{wp_url.rstrip('/')}{API_ENDPOINT}"

    response = requests.get(endpoint, auth=(wp_user, wp_password), timeout=30)

    if response.status_code == 401:
        raise ConnectionError("401 Unauthorized — wrong username or password")
    if response.status_code == 403:
        raise ConnectionError("403 Forbidden — make sure the WordPress user has admin (edit_users) capability")
    if response.status_code == 404:
        raise ConnectionError("404 Not Found — is the plugin installed and activated?")
    if not response.ok:
        raise ConnectionError(f"{response.status_code} Error — {response.text[:200]}")

    members = response.json()

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(members)

    return len(members)


if __name__ == "__main__":
    import sys
    import keyring
    import defaults_manager as dm

    wp_url      = keyring.get_password('YedidyaPortal', 'wp_url') or ''
    wp_user     = keyring.get_password('YedidyaPortal', 'wp_user') or ''
    wp_password = keyring.get_password('YedidyaPortal', 'wp_password') or ''

    if not wp_url or not wp_user or not wp_password:
        print("WordPress credentials not found in Credential Manager. Run run.py first.")
        sys.exit(1)

    output_path = dm.get('members_list', 'raw_csv_path')
    count = fetch_members(wp_url, wp_user, wp_password, output_path)
    print(f"✓ Fetched {count} members → {output_path}")
