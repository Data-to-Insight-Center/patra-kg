import json
import random
import time
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:5002"
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "examples" / "model_cards" / "imagenet"


def load_templates():
    templates = []
    for p in TEMPLATE_DIR.glob("*.json"):
        with p.open() as f:
            templates.append(json.load(f))
    if not templates:
        raise RuntimeError(f"No templates found in {TEMPLATE_DIR}")
    return templates


def make_payload(template: dict, idx: int) -> dict:
    payload = json.loads(json.dumps(template))  # deep copy
    suffix = f"-{idx:04d}"
    # Ensure unique external_id to satisfy DB constraint
    payload["external_id"] = f"imagenet-{idx:04d}"
    # Nudge name/version for uniqueness if server enforces it
    if "name" in payload and isinstance(payload["name"], str):
        payload["name"] = f"{payload['name']}{suffix}"
    if "version" in payload and isinstance(payload["version"], str):
        payload["version"] = payload["version"]
    # Required by ingester: provide defaults if missing
    payload.setdefault("deployment_strategy", "none")
    payload.setdefault("deployment_test", "n/a")
    payload.setdefault("citation", payload.get("citation", "n/a"))
    return payload


def post_modelcard(payload: dict) -> requests.Response:
    # Try user-specified alias first, then fallback to canonical endpoint
    for path in ("/upload_mc", "/modelcard"):
        url = f"{BASE_URL}{path}"
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 404:
            return resp
    return resp


def main():
    templates = load_templates()
    successes = 0
    failures = 0
    for i in range(1000):
        tpl = random.choice(templates)
        body = make_payload(tpl, i)
        try:
            r = post_modelcard(body)
            if r.status_code >= 200 and r.status_code < 300:
                successes += 1
            else:
                failures += 1
                print(f"POST failed [{r.status_code}]: {r.text[:200]}")
        except Exception as e:
            failures += 1
            print(f"POST error: {e}")
        # light pacing to avoid overwhelming dev server
        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/1000 (ok={successes}, fail={failures})")
            time.sleep(0.2)

    print(f"Done. ok={successes}, fail={failures}")


if __name__ == "__main__":
    main()


