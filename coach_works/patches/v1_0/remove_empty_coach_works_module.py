import frappe


def execute():
	"""Drop the empty `Coach Works` module.

	It held nothing, and its name blocked the app's sidebar from being called "Coach Works":
	Frappe refuses a sidebar titled after another module. Runs before the model sync, which is
	when the new sidebar is written.
	"""
	if not frappe.db.exists("Module Def", "Coach Works"):
		return
	if frappe.db.get_value("Module Def", "Coach Works", "app_name") != "coach_works":
		return
	for doctype in ("DocType", "Report", "Page", "Workspace", "Dashboard", "Sidebar"):
		if frappe.db.exists(doctype, {"module": "Coach Works"}):
			# something real lives there; leave it alone
			return
	frappe.delete_doc("Module Def", "Coach Works", force=True, ignore_permissions=True)
