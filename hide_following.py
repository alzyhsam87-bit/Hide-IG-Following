#!/usr/bin/env python3
"""Toggle hidden Instagram privacy settings via the internal GraphQL API.

These settings exist server-side but are not exposed in the Instagram app UI.

Requirements: pip install requests
Usage:        python hide_following.py
"""

import json, base64, sys
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    sys.exit("Install the one dependency first: pip install requests")

API_URL = "https://i.instagram.com/graphql/query"
DOC_ID  = "33823799134204572300329356040"

SETTINGS = [
    ("hide_followers_following_list", "Hide followers/following list"),
    ("hide_self_from_others_lists",   "Hide yourself from others' lists"),
]

BASE_HEADERS = {
    "content-type":            "application/x-www-form-urlencoded",
    "user-agent":              "Instagram 453.0.0.57.79 Android (35/15; 450dpi; 1080x2400; samsung; SM-G998B; p3s; exynos2100; en_GB; 1100805506)",
    "x-ig-app-id":             "567067343352427",
    "x-ig-capabilities":       "3brTv10C",
    "x-graphql-client-library": "pando",
}


def _bearer(session_id):
    user_id = session_id.split("%3A")[0]
    payload = json.dumps(
        {"ds_user_id": user_id, "sessionid": session_id},
        separators=(",", ":"),
    )
    return "Bearer IGT:2:" + base64.b64encode(payload.encode()).decode()


def get_username(session_id):
    user_id = session_id.split("%3A")[0]
    headers = {
        "user-agent":     BASE_HEADERS["user-agent"],
        "x-ig-app-id":    BASE_HEADERS["x-ig-app-id"],
        "authorization":  _bearer(session_id),
    }
    try:
        r = requests.get(
            f"https://b.i.instagram.com/api/v1/users/{user_id}/info/",
            headers=headers, timeout=10,
        )
        if r.ok:
            return r.json().get("user", {}).get("username")
    except requests.RequestException:
        pass
    return None


def set_setting(session_id, setting_id, value):
    """Set a boolean privacy setting. Returns (ok, resulting_value)."""
    body = urlencode({
        "method": "post",
        "format": "json",
        "server_timestamps": "true",
        "locale": "user",
        "fb_api_req_friendly_name": "SetBooleanSetting",
        "client_doc_id": DOC_ID,
        "enable_canonical_naming": "true",
        "enable_canonical_variable_overrides": "true",
        "enable_canonical_naming_ambiguous_type_prefixing": "true",
        "variables": json.dumps({"data": {
            "value": value,
            "setting_id": setting_id,
            "callsite": "account_privacy",
            "allow_error_codes": True,
        }}),
    })
    headers = {
        **BASE_HEADERS,
        "authorization":       _bearer(session_id),
        "x-fb-friendly-name":  "SetBooleanSetting",
        "x-root-field-name":   "xdt_api__v1__settings__set_bool",
    }
    try:
        r = requests.post(API_URL, data=body, headers=headers, timeout=10)
        if not r.ok:
            return False, None
        resp = r.json()
        if resp.get("status") != "ok":
            return False, None
        for entry in resp.get("data", {}).values():
            if isinstance(entry, dict) and entry.get("setting_id") == setting_id:
                return True, entry.get("value")
    except requests.RequestException:
        pass
    return False, None


def main():
    print()
    print("  Hide IG Following")
    print("  Toggle hidden Instagram privacy settings.")
    print()

    session_id = input("  Session ID: ").strip()
    if len(session_id) < 10:
        sys.exit("  Invalid session ID.")

    print("  Validating...")
    username = get_username(session_id)
    if not username:
        sys.exit("  Invalid or expired session.")
    print(f"  Logged in as @{username}")
    print()

    while True:
        idx = 1
        options = []
        for setting_id, label in SETTINGS:
            print(f"  {idx}. Enable  — {label}")
            options.append((setting_id, label, True))
            idx += 1
            print(f"  {idx}. Disable — {label}")
            options.append((setting_id, label, False))
            idx += 1
        print(f"  0. Exit")
        print()

        choice = input("  > ").strip()
        if choice == "0":
            break
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(options):
            print("  Invalid choice.\n")
            continue

        setting_id, label, value = options[int(choice) - 1]
        action = "Enabling" if value else "Disabling"
        print(f"  {action}...")

        ok, result = set_setting(session_id, setting_id, value)
        if ok:
            state = "on" if result else "off"
            print(f"  Done. {label} is now {state}.\n")
        else:
            print("  Request failed. Session may have expired.\n")


if __name__ == "__main__":
    main()
