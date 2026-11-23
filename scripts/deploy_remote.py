#!/usr/bin/env python3
"""Deploy coach_works desk/job-work metadata to a live site over the REST API.

Creates the DocTypes, Workspace, Reports, Sidebar/Dock/Desktop Icon records straight from
the repository JSON, so a demo site can be brought up without shell access.

Usage::

	COACH_TOKEN=<api_key>:<api_secret> python3 scripts/deploy_remote.py
	COACH_TOKEN=... python3 scripts/deploy_remote.py --only doctypes
"""

import argparse
import glob
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = os.environ.get("COACH_SITE", "https://coachworks-demo.tbocloud.in")
TOKEN = os.environ.get("COACH_TOKEN", "")
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coach_works")

DOCTYPE_FILES = sorted(glob.glob(os.path.join(APP, "job_work", "doctype", "*", "*.json")))
REPORT_FILES = sorted(glob.glob(os.path.join(APP, "job_work", "report", "*", "*.json")))
WORKSPACE_FILES = sorted(glob.glob(os.path.join(APP, "job_work", "workspace", "*", "*.json")))
SIDEBAR_FILES = sorted(glob.glob(os.path.join(APP, "coach_works", "sidebar", "*", "*.json")))
DOCK_FILES = sorted(glob.glob(os.path.join(APP, "coach_works", "dock", "*", "*.json")))
ICON_FILES = sorted(glob.glob(os.path.join(APP, "desktop_icon", "*.json")))


def call(method, path, payload=None, http="GET"):
	url = f"{SITE}{path}"
	data = json.dumps(payload).encode() if payload is not None else None
	req = urllib.request.Request(url, data=data, method=http)
	req.add_header("Authorization", f"token {TOKEN}")
	req.add_header("Content-Type", "application/json")
	req.add_header("Accept", "application/json")
	try:
		with urllib.request.urlopen(req, timeout=180) as resp:
			body = resp.read().decode()
	except urllib.error.HTTPError as e:
		body = e.read().decode()
		return e.code, safe_json(body)
	return 200, safe_json(body)


def safe_json(body):
	try:
		return json.loads(body)
	except ValueError:
		return {"_raw": body[:500]}


def exists(doctype, name):
	code, data = call(
		"GET",
		"/api/method/frappe.client.get_count?"
		+ urllib.parse.urlencode({"doctype": doctype, "filters": json.dumps([["name", "=", name]])}),
	)
	if code != 200:
		return False
	return bool(data.get("message"))


def upsert(doctype, doc, label=None):
	label = label or f"{doctype} {doc['name']}"
	name = doc["name"]
	quoted = urllib.parse.quote(name, safe="")
	code, existing = call("GET", f"/api/resource/{urllib.parse.quote(doctype, safe='')}/{quoted}")
	payload = dict(doc)
	if code == 200:
		for key in ("doctype", "field_order", "creation", "owner", "idx"):
			payload.pop(key, None)
		server_modified = (existing.get("data") or {}).get("modified")
		if server_modified:
			payload["modified"] = server_modified
		code, data = call(
			"PUT",
			f"/api/resource/{urllib.parse.quote(doctype, safe='')}/{quoted}",
			payload,
			http="PUT",
		)
		verb = "updated"
	else:
		code, data = call(
			"POST", f"/api/resource/{urllib.parse.quote(doctype, safe='')}", payload, http="POST"
		)
		verb = "created"
	if code not in (200, 201):
		print(f"  FAIL {label} ({code}): {str(data)[:300]}")
		return False
	print(f"  {verb} {label}")
	return True


def load(path):
	with open(path) as f:
		return json.load(f)


def strip_controller_fields(doc):
	doc = json.loads(json.dumps(doc))
	if doc.get("doctype") == "DocType":
		doc.pop("field_order", None)
		if not doc.get("custom"):
			doc["custom"] = 1
	return doc


def deploy_doctypes():
	print("DocTypes:")
	pending = [strip_controller_fields(load(p)) for p in DOCTYPE_FILES]
	for attempt in range(1, 5):
		failed = []
		for doc in pending:
			if not upsert("DocType", doc):
				failed.append(doc)
		if not failed:
			return
		if len(failed) == len(pending):
			print(f"  {len(failed)} doctype(s) still failing after pass {attempt}; stopping")
			return
		pending = failed
		print(f"  pass {attempt}: {len(failed)} pending (waiting on links)")


def deploy_reports():
	print("Reports:")
	for path in REPORT_FILES:
		doc = load(path)
		# standard reports can only be saved by Administrator; a demo site deploys
		# them as site-owned reports so the API user can create them
		doc["is_standard"] = "No"
		doc["module"] = ""
		upsert("Report", doc)


def deploy_workspace():
	print("Workspace:")
	for path in WORKSPACE_FILES:
		upsert("Workspace", load(path))


def deploy_desk():
	# Sidebar and Dock belong to the app and are rejected outside developer mode
	# ("belongs to its app and can only be edited in developer mode"). They reach a site
	# through `bench migrate` on the server, not through the API.
	print("Desktop Icon:")
	for path in ICON_FILES:
		upsert("Desktop Icon", load(path))


STEPS = {
	"doctypes": deploy_doctypes,
	"reports": deploy_reports,
	"workspace": deploy_workspace,
	"desk": deploy_desk,
}


def main():
	global TOKEN, SITE
	parser = argparse.ArgumentParser()
	parser.add_argument("--only", choices=sorted(STEPS), action="append")
	parser.add_argument("--site")
	parser.add_argument("--token")
	args = parser.parse_args()
	if args.site:
		SITE = args.site
	if args.token:
		TOKEN = args.token
	if not TOKEN:
		sys.exit("Set COACH_TOKEN=<api_key>:<api_secret> or pass --token")
	SITE = SITE.rstrip("/")

	code, me = call("GET", "/api/method/frappe.auth.get_logged_user")
	print(f"site {SITE} as {me.get('message')}")
	if code != 200:
		sys.exit(f"auth failed: {me}")

	for name in args.only or ["doctypes", "reports", "workspace", "desk"]:
		STEPS[name]()


if __name__ == "__main__":
	main()
