#!/usr/bin/env python3
"""Run coach_works/demo.py on a live site through a Server Script.

The app's Python is not on every server -- a site can carry the DocTypes (created over the API)
without the app checked out in the bench. A Server Script is executed server-side, so it can
submit documents, which the REST API cannot.

Usage::

	COACH_TOKEN=<api_key>:<api_secret> python3 scripts/seed_demo_server_script.py

Re-running is safe: a job that already exists for a vehicle is skipped.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = os.environ.get("COACH_SITE", "https://coachworks-demo.tbocloud.in").rstrip("/")
TOKEN = os.environ.get("COACH_TOKEN", "")
SCRIPT_NAME = "Coach Works Demo Seed"
API_METHOD = "coach_works_demo_seed"
DEMO_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coach_works", "demo.py")


def call(method, path, payload=None):
	url = f"{SITE}{path}"
	data = json.dumps(payload).encode() if payload is not None else None
	req = urllib.request.Request(url, data=data, method=method)
	req.add_header("Authorization", f"token {TOKEN}")
	req.add_header("Content-Type", "application/json")
	req.add_header("Accept", "application/json")
	try:
		with urllib.request.urlopen(req, timeout=300) as resp:
			return 200, json.loads(resp.read().decode() or "{}")
	except urllib.error.HTTPError as e:
		body = e.read().decode()
		try:
			return e.code, json.loads(body)
		except ValueError:
			return e.code, {"_raw": body[:400]}


def server_body():
	"""The demo module as sandbox-safe source.

	The sandbox refuses `import`, so the guarded import at the top of the module is dropped and
	`frappe` is used as injected. The module's own source is kept verbatim after that, so the
	bench route and this one run the same code.
	"""
	with open(DEMO_PY) as f:
		source = f.read()
	source = re.sub(r"try:\n\timport frappe\nexcept ImportError:.*?\n\tfrappe = frappe\n", "", source, flags=re.S)
	if "\timport frappe" in source:
		sys.exit("demo.py still imports frappe; the Server Script sandbox refuses imports")
	return (
		source
		+ "\n\ntry:\n"
		+ "\tfrappe.response['result'] = load_demo_data()\n"
		+ "\tfrappe.db.commit()\n"
		+ "\tfrappe.response['committed'] = 1\n"
		+ "except Exception:\n"
		+ "\tfrappe.db.rollback()\n"
		+ "\tfrappe.response['traceback'] = frappe.utils.get_traceback()[-2500:]\n"
	)


def deploy_script(body):
	payload = {
		"doctype": "Server Script",
		"name": SCRIPT_NAME,
		"script_type": "API",
		"api_method": API_METHOD,
		"allow_guest": 0,
		"disabled": 0,
		"script": body,
	}
	path = "/api/resource/Server%20Script/" + urllib.parse.quote(SCRIPT_NAME, safe="")
	code, _existing = call("GET", path)
	if code == 200:
		code, data = call("PUT", path, {"script": body})
		verb = "updated"
	else:
		code, data = call("POST", "/api/resource/Server%20Script", payload)
		verb = "created"
	if code not in (200, 201):
		sys.exit(f"could not deploy {SCRIPT_NAME}: {code} {str(data)[:500]}")
	print(f"{verb} Server Script {SCRIPT_NAME}")


def run():
	code, data = call("GET", f"/api/method/{API_METHOD}")
	if code != 200:
		print(f"seed failed ({code}): {str(data)[:1200]}")
		return code
	print(json.dumps(data.get("message"), indent=1, default=str))
	return 200


def main():
	global SITE, TOKEN
	if "--site" in sys.argv:
		SITE = sys.argv[sys.argv.index("--site") + 1].rstrip("/")
	if not TOKEN:
		TOKEN = os.environ.get("COACH_TOKEN", "")
	if not TOKEN:
		sys.exit("Set COACH_TOKEN=<api_key>:<api_secret>")

	code, me = call("GET", "/api/method/frappe.auth.get_logged_user")
	print(f"site {SITE} as {me.get('message')}")
	if code != 200:
		sys.exit(f"auth failed: {me}")

	deploy_script(server_body())
	return run()


if __name__ == "__main__":
	sys.exit(main())
