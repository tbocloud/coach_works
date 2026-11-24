import frappe
from frappe.model.rename_doc import rename_doc


def execute():
	"""Quotes are now ERPNext Quotations, so the "Estimate" stage is called "Quoted"."""
	if frappe.db.exists("Work Stage", "Estimate") and not frappe.db.exists("Work Stage", "Quoted"):
		rename_doc("Work Stage", "Estimate", "Quoted", force=True, show_alert=False)
		frappe.db.set_value("Work Stage", "Quoted", "stage_name", "Quoted")

	# a build should not start before the customer has agreed a price
	if frappe.db.exists("Work Stage", "Build"):
		frappe.db.set_value("Work Stage", "Build", "requires_quotation", 1)
