import frappe

STAGES = [
	("Enquiry", "#868e96", "Open"),
	("Estimate", "#4c6ef5", "Open"),
	("Approved", "#12b886", "Open"),
	("Build", "#f59f00", "Open"),
	("Paint / Finishing", "#fd7e14", "Open"),
	("Ready", "#0ca678", "Open"),
	("Delivered", "#495057", "Closed"),
	("Cancelled", "#c92a2a", "Cancelled"),
]

VEHICLE_TYPES = [
	"Food Truck",
	"Hearse Van",
	"Mobile ATM",
	"Car Customization",
	"Side Wheel Fixing",
	"Mini Food Truck",
]


def after_install():
	after_migrate()


def after_migrate():
	_sync_work_stages()
	_sync_vehicle_types()
	_sync_settings()


def _exists(doctype, name=None):
	return frappe.db.exists(doctype, name) if name else frappe.db.exists("DocType", doctype)


def _sync_work_stages():
	if not _exists("Work Stage"):
		return
	for idx, (stage, color, status) in enumerate(STAGES, start=1):
		if _exists("Work Stage", stage):
			continue
		frappe.get_doc(
			{
				"doctype": "Work Stage",
				"stage_name": stage,
				"color": color,
				"job_status": status,
				"sequence": idx * 10,
			}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)


def _sync_vehicle_types():
	if not _exists("Vehicle Type"):
		return
	for vehicle_type in VEHICLE_TYPES:
		if _exists("Vehicle Type", vehicle_type):
			continue
		frappe.get_doc({"doctype": "Vehicle Type", "vehicle_type": vehicle_type}).insert(
			ignore_permissions=True, ignore_if_duplicate=True
		)


def _sync_settings():
	if not _exists("Coach Work Settings"):
		return
	if _exists("Coach Work Settings", "Coach Work Settings"):
		return
	frappe.get_doc(
		{
			"doctype": "Coach Work Settings",
			"company": frappe.defaults.get_defaults().get("company"),
			"default_stage": "Enquiry",
			"enable_estimate_approval": 1,
		}
	).insert(ignore_permissions=True, ignore_if_duplicate=True)
