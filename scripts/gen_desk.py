"""Generate Frappe 16 desk files (Desktop Icon, Dock, Sidebars) for coach_works."""

import datetime
import json
import os
import re

RENAMED = {"Vehicle": "Coach Work Vehicle"}


def doctype_name(label):
	"""Real DocType name for a sidebar label; these DocTypes are spaced, not squashed."""
	return RENAMED.get(label, label)


SPEC = {
	"app": "coach_works",
	"app_title": "Coach Works",
	"logo": "/assets/coach_works/logo.svg",
	"tiles": [
		{"label": "Coach Works", "link": "/desk/coach-works-dashboard"},
	],
	# One sidebar for the whole app. Its title cannot be another module's name, which is why the
	# empty `Coach Works` module was removed (patch v1_0.remove_empty_coach_works_module).
	"rail": [
		{
			"title": "Coach Works",
			"module": "Job Work",
			"icon": "truck",
			"items": [
				("page", "Dashboard", "coach-works-dashboard", "layout-dashboard"),
				("doctype", "Jobs", "Coach Work Order", "clipboard-list"),
				("doctype", "Quotations", "Quotation", "file-text"),
				("doctype", "Vehicles", doctype_name("Vehicle"), "truck"),
				("doctype", "Customers", "Customer", "users"),
				("doctype", "Invoices", "Sales Invoice", "receipt"),
				("doctype", "Payments", "Payment Entry", "wallet"),
				(
					"section",
					"Reports",
					"chart-column",
					[
						("report", "Jobs In Progress", "Jobs In Progress"),
						("report", "Ready for Delivery", "Jobs Ready for Delivery"),
						("report", "Vehicle History", "Vehicle Job History"),
					],
				),
				(
					"section",
					"Setup",
					"settings",
					[
						("doctype", "Work Stages", "Work Stage"),
						("doctype", "Vehicle Types", "Vehicle Type"),
						("doctype", "Items & Services", "Item"),
						("doctype", "Settings", "Coach Work Settings"),
					],
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

first_url = SPEC["tiles"][0]["link"]
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
