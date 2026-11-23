import frappe

STAGES = [
	("Enquiry", "#868e96", "open"),
	("Estimate", "#4c6ef5", "open"),
	("Approved", "#12b886", "open"),
	("Build", "#f59f00", "open"),
	("Paint / Finishing", "#fd7e14", "open"),
	("Ready", "#0ca678", "open"),
	("Delivered", "#495057", "closed"),
	("Cancelled", "#c92a2a", "cancelled"),
]

VEHICLE_TYPES = [
	"Food Truck",
	"Hearse Van",
	"Mobile ATM",
	"Car Customization",
	"Side Wheel Fixing",
	"Mini Food Truck",
]

DEFAULTS = {
	"Coach Works Settings": {
		"company": None,
		"default_stage": "Enquiry",
		"default_work_stage": "Fabrication",
		"enable_estimate_approval": 1,
	},
	"Vehicle Type": [{"doctype": "Vehicle Type", "vehicle_type": v} for v in VEHICLE_TYPES],
}


def after_install():
	after_migrate()


def after_migrate():
	_sync_work_stages()
	_sync_vehicle_types()
	_sync_settings()


def _sync_work_stages():
	for idx, (stage, color, status) in enumerate(STAGES, start=1):
		if frappe.db.exists("Work Stage", stage):
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
	for row in DEFAULTS["Vehicle Type"]:
		if frappe.db.exists("Vehicle Type", row["vehicle_type"]):
			continue
		frappe.get_doc({"doctype": "Vehicle Type", **row}).insert(
			ignore_permissions=True, ignore_if_duplicate=True
		)


def _sync_settings():
	if frappe.db.exists("Coach Works Settings", "Coach Works Settings"):
		return
	values = dict(DEFAULTS["Coach Works Settings"])
	values["company"] = values["company"] or frappe.defaults.get_defaults().get("company")
	frappe.get_doc({"doctype": "Coach Works Settings", **values}).insert(
		ignore_permissions=True, ignore_if_duplicate=True
	)
