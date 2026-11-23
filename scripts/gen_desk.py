"""Generate Frappe 16 desk files (Desktop Icon, Dock, Sidebars) for coach_works."""

import datetime
import json
import os
import re


def doctype_name(label):
	return label.replace(" ", "")


SPEC = {
	"app": "coach_works",
	"app_title": "Coach Works",
	"logo": "/assets/coach_works/logo.svg",
	"tiles": [
		{"label": "Coach Works", "link": "auto"},
	],
	"rail": [
		{
			"title": "Job Work",
			"module": "Job Work",
			"icon": "wrench",
			"items": [
				("workspace", "Home", "Job Work", "home"),
				("doctype", "Coach Work Order", doctype_name("Coach Work Order"), "clipboard-list"),
				("doctype", "Vehicle", doctype_name("Vehicle"), "truck"),
				("doctype", "Job Work Estimate", doctype_name("Job Work Estimate"), "file-text"),
				("doctype", "Job Work Charge", doctype_name("Job Work Charge"), "receipt"),
				("doctype", "Work Stage", doctype_name("Work Stage"), "git-branch"),
				(
					"section",
					"Setup",
					"settings",
					[
						("doctype", "Vehicle Type", doctype_name("Vehicle Type")),
						("doctype", "Coach Work Settings", doctype_name("Coach Work Settings")),
					],
				),
			],
		},
		{
			"title": "Coach Works Reports",
			"module": "Job Work",
			"icon": "chart-column",
			"items": [
				("workspace", "Overview", "Job Work", "layout-dashboard"),
				("report", "Jobs In Progress", "Jobs In Progress", "loader-circle"),
				(
					"report",
					"Jobs Ready for Delivery",
					"Jobs Ready for Delivery",
					"circle-check",
				),
				(
					"report",
					"Vehicle Job History",
					"Vehicle Job History",
					"history",
				),
			],
		},
	],
}

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coach_works")


def scrub(s):
	return s.replace(" ", "_").replace("-", "_").lower()


def slug(s):
	return re.sub(r"\s+", "-", s.lower().replace("&", " and ").strip())


FLAGS = {
	"added": 0,
	"child": 0,
	"collapsible": 1,
	"hidden": 0,
	"indent": 0,
	"is_default_module": 0,
	"keep_closed": 0,
	"open_in_new_tab": 0,
	"show_arrow": 0,
}
TYPES = {
	"doctype": "DocType",
	"report": "Report",
	"workspace": "Workspace",
	"page": "Page",
	"dashboard": "Dashboard",
}


def meta(doctype, name):
	return {
		"app": SPEC["app"],
		"creation": NOW,
		"modified": NOW,
		"docstatus": 0,
		"idx": 0,
		"doctype": doctype,
		"name": name,
		"owner": "Administrator",
		"modified_by": "Administrator",
		"standard": 1,
	}


def dump(path, doc):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as f:
		f.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
	print("wrote", os.path.relpath(path, ROOT))


def link(kind, label, target, icon=None, child=0):
	row = {**FLAGS, "type": "Link", "label": label, "child": child}
	if kind == "url":
		row.update(link_type="URL", url=target)
	else:
		row.update(link_type=TYPES[kind], link_to=target)
	if icon:
		row["icon"] = icon
	return row


def rows(items):
	out = []
	for it in items:
		if it[0] == "section":
			_, label, icon, children = it
			out.append(
				{
					**FLAGS,
					"type": "Section Break",
					"label": label,
					"icon": icon,
					"link_type": "DocType",
					"indent": 1,
					"keep_closed": 1,
				}
			)
			out += [link(*c, child=1) for c in children]
		else:
			out.append(link(*it))
	return [
		{
			"doctype": "Sidebar Item",
			"parentfield": "items",
			"parenttype": "Sidebar",
			"idx": i,
			**r,
		}
		for i, r in enumerate(out, 1)
	]


bad = [r["title"] for r in SPEC["rail"] if re.search(r"[/?#%\\]", r["title"])]
assert not bad, f"unroutable characters in titles: {bad}"
assert len({slug(r["title"]) for r in SPEC["rail"]}) == len(SPEC["rail"]), "duplicate slugs"

for r in SPEC["rail"]:
	doc = meta("Sidebar", r["title"])
	doc.update(
		title=r["title"],
		module=r["module"],
		header_icon=r["icon"],
		items=rows(r["items"]),
	)
	s = scrub(r["title"])
	dump(f"{ROOT}/{scrub(r['module'])}/sidebar/{s}/{s}.json", doc)

dock = meta("Dock", SPEC["app"])
dock.update(
	user="",
	items=[
		{
			"added": 0,
			"hidden": 0,
			"icon": r["icon"],
			"link_type": "Sidebar",
			"link_to": r["title"],
			"title": r["title"],
		}
		for r in SPEC["rail"]
	],
)
dump(f"{ROOT}/dock/{SPEC['app']}/{SPEC['app']}.json", dock)

first_url = "/desk/" + slug(SPEC["rail"][0]["title"])
for n, t in enumerate(SPEC["tiles"]):
	tile = meta("Desktop Icon", t["label"])
	tile.update(
		label=t["label"],
		icon_type="App",
		link_type="External",
		hidden=0,
		idx=20 + n,
		link=first_url if t["link"] == "auto" else t["link"],
		logo_url=t.get("logo", SPEC["logo"]),
		roles=[],
	)
	dump(f"{ROOT}/desktop_icon/{scrub(t['label'])}.json", tile)

print(f"\nSet hooks.add_to_apps_screen route to: {first_url}")
