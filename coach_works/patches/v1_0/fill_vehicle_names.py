import frappe

from coach_works.job_work.doctype.coach_work_vehicle.coach_work_vehicle import vehicle_title


def execute():
	"""Vehicles are now shown by registration (or chassis) number: fill the new title field.

	The old free-text "Owner Name" became `customer_name`, fetched from the customer; vehicles
	with no customer keep the old text there so nothing typed in is lost.
	"""
	has_owner_name = frappe.db.has_column("Coach Work Vehicle", "owner_name")
	fields = ["name", "registration_no", "chassis_no", "make_model", "customer"]
	if has_owner_name:
		fields.append("owner_name")

	for row in frappe.get_all("Coach Work Vehicle", fields=fields):
		customer_name = None
		if row.customer:
			customer_name = frappe.db.get_value("Customer", row.customer, "customer_name")
		if not customer_name and has_owner_name:
			customer_name = row.owner_name
		frappe.db.set_value(
			"Coach Work Vehicle",
			row.name,
			{
				"registration_no": (row.registration_no or "").strip().upper() or None,
				"vehicle_name": vehicle_title(row),
				"customer_name": customer_name,
			},
			update_modified=False,
		)
	frappe.db.sql(
		"""update `tabCoach Work Order` job
		join `tabCoach Work Vehicle` v on v.name = job.vehicle
		set job.vehicle_type = v.vehicle_type
		where ifnull(job.vehicle_type, '') = ''"""
	)
	frappe.db.sql(
		"""update `tabCoach Work Order` job
		join `tabEmployee` e on e.name = job.assigned_to
		set job.supervisor_name = e.employee_name
		where ifnull(job.supervisor_name, '') = ''"""
	)
