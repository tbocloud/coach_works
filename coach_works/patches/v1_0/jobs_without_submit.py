import frappe


def execute():
	"""Jobs are no longer submitted: bring every existing job back to an editable state.

	A cancelled job becomes an editable job sitting in the Cancelled stage, so nothing is lost
	and the list still shows it as cancelled.
	"""
	cancelled_stage = "Cancelled" if frappe.db.exists("Work Stage", "Cancelled") else None
	if cancelled_stage:
		frappe.db.sql(
			"""update `tabCoach Work Order`
			set stage = %s, status = 'Cancelled'
			where docstatus = 2""",
			cancelled_stage,
		)
	for table in ("tabCoach Work Order", "tabJob Work Charge", "tabJob Work Stage Log"):
		frappe.db.sql(f"update `{table}` set docstatus = 0 where docstatus != 0")  # nosemgrep
