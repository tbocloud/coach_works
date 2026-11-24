import frappe

OLD = {
	"Dashboard Chart": ["Jobs by Stage", "Jobs by Customer", "Job Value Trend"],
	"Number Card": ["Jobs In Progress", "Jobs Ready for Delivery", "Open Job Value", "Vehicles"],
	"Dashboard": ["Coach Works"],
	"Workspace": ["Job Work"],
	"Sidebar": ["Job Work", "Coach Works Reports"],
}


def execute():
	"""Remove the first version's overview workspace, dashboard, charts, cards and sidebars.

	The Dashboard page replaces all of them. Frappe reaps orphaned workspaces, dashboards and
	sidebars itself, but not charts or number cards, so they are removed here, only when they
	belong to this app's module.
	"""
	for doctype, names in OLD.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		has_module = frappe.get_meta(doctype).has_field("module")
		for name in names:
			if not frappe.db.exists(doctype, name):
				continue
			if has_module and frappe.db.get_value(doctype, name, "module") not in (None, "", "Job Work"):
				continue
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, ignore_missing=True)
