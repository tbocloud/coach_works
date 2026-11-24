"""Defaults a fresh site needs: work stages, vehicle types and settings.

Everything here only fills what is missing, so a site's own edits are never overwritten.
"""

import os

import frappe

# (stage, colour, job status, needs an accepted quotation)
STAGES = [
	("Enquiry", "#868e96", "Open", 0),
	("Quoted", "#7c3aed", "Open", 0),
	("Approved", "#2490ef", "Open", 0),
	("Build", "#f59f00", "Open", 1),
	("Paint / Finishing", "#e8590c", "Open", 0),
	("Ready", "#0ca678", "Open", 0),
	("Delivered", "#495057", "Closed", 0),
	("Cancelled", "#c92a2a", "Cancelled", 0),
]

VEHICLE_TYPES = [
	"Food Truck",
	"Mini Food Truck",
	"Hearse Van",
	"Mobile ATM",
	"Car Customization",
	"Side Wheel Fixing",
]


def after_install():
	after_migrate()


def after_migrate():
	sync_module_def()
	sync_work_stages()
	sync_vehicle_types()
	sync_settings()


def sync_module_def():
	"""A module first created over the API was marked custom; once the app is installed it is not."""
	module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_work")
	if os.path.isdir(module_path) and frappe.db.exists("Module Def", "Job Work"):
		frappe.db.set_value("Module Def", "Job Work", "custom", 0)


def sync_work_stages():
	for idx, (stage, color, status, needs_quote) in enumerate(STAGES, start=1):
		if frappe.db.exists("Work Stage", stage):
			continue
		frappe.get_doc(
			{
				"doctype": "Work Stage",
				"stage_name": stage,
				"color": color,
				"job_status": status,
				"requires_quotation": needs_quote,
				"sequence": idx * 10,
			}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)


def sync_vehicle_types():
	for vehicle_type in VEHICLE_TYPES:
		if not frappe.db.exists("Vehicle Type", vehicle_type):
			frappe.get_doc({"doctype": "Vehicle Type", "vehicle_type": vehicle_type}).insert(
				ignore_permissions=True, ignore_if_duplicate=True
			)


def sync_settings():
	settings = frappe.get_single("Coach Work Settings")
	changed = False
	if not settings.company:
		settings.company = frappe.defaults.get_global_default("company") or frappe.db.get_value(
			"Company", {}, "name"
		)
		changed = bool(settings.company)
	if not settings.default_stage and frappe.db.exists("Work Stage", "Enquiry"):
		settings.default_stage = "Enquiry"
		changed = True
	if changed:
		settings.flags.ignore_mandatory = True
		settings.flags.ignore_permissions = True
		settings.save()
