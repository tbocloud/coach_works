"""Demo data for Unicorn Coach Works.

Run once on a demo site, as a System Manager:

	bench --site <site> execute coach_works.demo.load_demo_data
	# or over HTTP
	POST /api/method/coach_works.demo.load_demo_data

It expects the demo customers, `CW-*` items and vehicles to exist. It creates a job for every
demo vehicle that has none, gives each job past the Enquiry stage a submitted quotation (accepted
from Approved onwards), and bills the delivered job. Re-running it only fills what is missing.
"""

import frappe
from frappe.utils import add_days, nowdate

JOBS = [
	(
		"KA-05-MJ-3390",
		"Iyer Sweets & Snacks",
		"Enquiry",
		"Mini food truck fit-out with cold storage counter.",
		[("CW-INTERIOR", 1), ("CW-AC-SERVICE", 1)],
	),
	(
		"MH-02-CD-4412",
		"Sharma Caterers",
		"Build",
		"Full food truck body build with service window, gas line and LED signage.",
		[("CW-FOODTRUCK-BUILD", 1), ("CW-GASLINE", 1), ("CW-ELECTRICAL", 1)],
	),
	(
		"MH-01-KL-8890",
		"Anand Foods Pvt Ltd",
		"Paint / Finishing",
		"Repaint exterior panels and fit new branding vinyl.",
		[("CW-PAINT", 1), ("CW-BODY-REPAIR", 1)],
	),
	(
		"TN-09-BE-1123",
		"Nair Event Services",
		"Build",
		"Hearse van conversion with rear deck, seating and curtain rails.",
		[("CW-HEARSE-BUILD", 1), ("CW-INTERIOR", 1)],
	),
	(
		"PB-10-AF-7721",
		"Gill Transport",
		"Ready",
		"Side wheel fixing and load body strengthening.",
		[("CW-SIDEWHEEL", 1), ("CW-BODY-REPAIR", 1)],
	),
	(
		"WB-02-AL-5567",
		"Bose Mobile Banking",
		"Paint / Finishing",
		"Mobile ATM van exterior wrap and interior cabin finishing.",
		[("CW-INTERIOR", 1), ("CW-PAINT", 1)],
	),
	(
		"GJ-01-RT-2204",
		"Patel Wedding Planners",
		"Ready",
		"Interior customisation and lighting upgrade.",
		[("CW-INTERIOR", 1), ("CW-ELECTRICAL", 1)],
	),
	(
		"TS-09-EF-9081",
		"Khan Hospitality",
		"Delivered",
		"Food truck build, delivered and invoiced.",
		[("CW-FOODTRUCK-BUILD", 1)],
	),
]


@frappe.whitelist()
def load_demo_data():
	frappe.only_for("System Manager")
	made = []
	for reg, customer, stage, description, charges in JOBS:
		vehicle = frappe.db.get_value("Coach Work Vehicle", {"registration_no": reg}, "name")
		if not vehicle or not frappe.db.exists("Customer", customer):
			continue
		if frappe.db.exists("Coach Work Order", {"vehicle": vehicle}):
			continue
		made.append(make_job(vehicle, customer, stage, description, charges).name)

	quoted = add_quotations()
	return {"jobs": made, "quotations": quoted}


def make_job(vehicle, customer, stage, description, charges):
	job = frappe.get_doc(
		{
			"doctype": "Coach Work Order",
			"customer": customer,
			"vehicle": vehicle,
			"posting_date": add_days(nowdate(), -12),
			"expected_delivery_date": add_days(nowdate(), -3 if stage == "Delivered" else 5),
			"work_description": description,
			"charges": [
				{"charge": code, "qty": qty, "rate": frappe.db.get_value("Item", code, "standard_rate") or 0}
				for code, qty in charges
				if frappe.db.exists("Item", code)
			],
		}
	)
	job.insert(ignore_permissions=True)
	job.db_set("stage", stage)
	job.db_set("status", frappe.db.get_value("Work Stage", stage, "job_status") or "Open")
	return job


def add_quotations():
	"""Give every job past Enquiry a submitted quotation; accept it from Approved onwards."""
	from coach_works.job_work.doctype.coach_work_order.coach_work_order import make_quotation

	quoted_seq = frappe.db.get_value("Work Stage", "Quoted", "sequence") or 20
	approved_seq = frappe.db.get_value("Work Stage", "Approved", "sequence") or 30
	made = []
	for job in frappe.get_all(
		"Coach Work Order",
		filters={"quotation": ("is", "not set"), "status": ("!=", "Cancelled")},
		fields=["name", "stage", "sales_invoice"],
	):
		seq = frappe.db.get_value("Work Stage", job.stage, "sequence") or 0
		if seq < quoted_seq or frappe.db.exists("Quotation", {"coach_work_order": job.name, "docstatus": 1}):
			continue
		doc = frappe.get_doc("Coach Work Order", job.name)
		if not doc.charges:
			continue
		quote = make_quotation(job.name)
		quote.transaction_date = doc.posting_date
		quote.valid_till = add_days(doc.posting_date, 30)
		quote.flags.ignore_permissions = True
		quote.insert()
		quote.submit()
		if seq >= approved_seq:
			doc.db_set("quotation", quote.name)
		made.append(quote.name)
	return made
