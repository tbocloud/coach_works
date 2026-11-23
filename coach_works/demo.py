"""Demo data for Unicorn Coach Works (India).

Two ways to run it, from the same data:

	# on a bench (creates everything, submits and invoices)
	bench --site <site> execute coach_works.demo.load_demo_data

	# over HTTP, through a Server Script, when the app lives only in git
	python3 scripts/seed_demo_server_script.py

The body below is deliberately restrained: no ``import`` statements and no private attribute
access, so the same text is valid inside the Server Script sandbox (``frappe`` is injected
there) and as a normal module function on a bench.
"""

try:
	import frappe
except ImportError:  # Server Script sandbox injects `frappe` and refuses `import`
	frappe = frappe


def add_days(date, days):
	return frappe.utils.add_days(date, days)


def nowdate():
	return frappe.utils.nowdate()


COMPANY = "Unicorn Coach Works"

JOBS = [
	{
		"reg": "KA-05-MJ-3390",
		"customer": "Iyer Sweets & Snacks",
		"stage": "Enquiry",
		"description": "Mini food truck fitout with cold storage counter.",
		"charges": [("CW-INTERIOR", 1), ("CW-AC-SERVICE", 1)],
	},
	{
		"reg": "MH-02-CD-4412",
		"customer": "Sharma Caterers",
		"stage": "Build",
		"description": "Full food truck body build with service window, gas line and LED signage.",
		"charges": [("CW-FOODTRUCK-BUILD", 1), ("CW-GASLINE", 1), ("CW-ELECTRICAL", 1)],
	},
	{
		"reg": "MH-01-KL-8890",
		"customer": "Anand Foods Pvt Ltd",
		"stage": "Paint / Finishing",
		"description": "Repaint exterior panels and fit new branding vinyl.",
		"charges": [("CW-PAINT", 1), ("CW-BODY-REPAIR", 1)],
	},
	{
		"reg": "TN-09-BE-1123",
		"customer": "Nair Event Services",
		"stage": "Build",
		"description": "Hearse van conversion with rear deck, seating and curtain rails.",
		"charges": [("CW-HEARSE-BUILD", 1), ("CW-INTERIOR", 1)],
	},
	{
		"reg": "PB-10-AF-7721",
		"customer": "Gill Transport",
		"stage": "Ready",
		"description": "Side wheel fixing and load body strengthening.",
		"charges": [("CW-SIDEWHEEL", 1), ("CW-BODY-REPAIR", 1)],
	},
	{
		"reg": "WB-02-AL-5567",
		"customer": "Bose Mobile Banking",
		"stage": "Paint / Finishing",
		"description": "Mobile ATM van exterior wrap and interior cabin finishing.",
		"charges": [("CW-INTERIOR", 1), ("CW-PAINT", 1)],
	},
	{
		"reg": "GJ-01-RT-2204",
		"customer": "Patel Wedding Planners",
		"stage": "Ready",
		"description": "Thar interior customisation and lighting upgrade.",
		"charges": [("CW-INTERIOR", 1), ("CW-ELECTRICAL", 1)],
	},
	{
		"reg": "TS-09-EF-9081",
		"customer": "Khan Hospitality",
		"stage": "Delivered",
		"description": "Food truck build delivered and invoiced.",
		"charges": [("CW-FOODTRUCK-BUILD", 1)],
	},
]

STAGE_HISTORY = {
	"Enquiry": ["Enquiry"],
	"Build": ["Enquiry", "Estimate", "Approved", "Build"],
	"Paint / Finishing": ["Enquiry", "Estimate", "Approved", "Build", "Paint / Finishing"],
	"Ready": ["Enquiry", "Estimate", "Approved", "Build", "Paint / Finishing", "Ready"],
	"Delivered": [
		"Enquiry",
		"Estimate",
		"Approved",
		"Build",
		"Paint / Finishing",
		"Ready",
		"Delivered",
	],
}


def compute_total(rows):
	total = 0
	for row in rows:
		total = total + (row.get("qty") or 0) * (row.get("rate") or 0)
	return total


def repair_totals():
	"""Fill in totals for documents created before the controller could run.

	A DocType created over the API has no Python controller, so `set_totals` never executes
	and `total_amount` stays zero. Recomputing here keeps the reports and the dashboard honest.
	"""
	fixed = 0
	for name in frappe.get_all("Coach Work Order", pluck="name"):
		doc = frappe.get_doc("Coach Work Order", name)
		total = compute_total(doc.charges)
		if doc.total_amount != total:
			doc.db_set("total_amount", total, update_modified=False)
			fixed = fixed + 1
	for name in frappe.get_all("Job Work Estimate", pluck="name"):
		doc = frappe.get_doc("Job Work Estimate", name)
		total = compute_total(doc.work_details)
		if doc.total_amount != total:
			doc.db_set("total_amount", total, update_modified=False)
			fixed = fixed + 1
	return fixed


def settle_unpaid_invoices():
	"""Pay the demo invoices so the ledger shows money received."""
	paid = 0
	account = frappe.db.get_value(
		"Account", {"company": COMPANY, "account_type": "Bank", "is_group": 0}, "name"
	) or frappe.db.get_value("Account", {"company": COMPANY, "account_type": "Cash", "is_group": 0}, "name")
	if not account:
		return paid
	for name in frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "outstanding_amount": (">", 0)},
		pluck="name",
	):
		invoice = frappe.get_doc("Sales Invoice", name)
		payment = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": invoice.customer,
				"company": invoice.company,
				"posting_date": add_days(nowdate(), -1),
				"paid_amount": invoice.outstanding_amount,
				"received_amount": invoice.outstanding_amount,
				"source_exchange_rate": 1,
				"target_exchange_rate": 1,
				"paid_to": account,
				"paid_to_account_currency": "INR",
				"references": [
					{
						"reference_doctype": "Sales Invoice",
						"reference_name": invoice.name,
						"allocated_amount": invoice.outstanding_amount,
					}
				],
			}
		)
		payment.flags.ignore_permissions = True
		payment.insert()
		payment.submit()
		paid = paid + 1
	return paid


def load_demo_data(company=COMPANY, invoice_delivered=True):
	company = company if frappe.db.exists("Company", company) else frappe.defaults.get_default("company")
	rates = {}
	for code in frappe.get_all("Item", filters={"name": ("like", "CW-%")}, pluck="name"):
		rates[code] = frappe.db.get_value("Item", code, "standard_rate")

	made = []
	for job in JOBS:
		vehicle = frappe.db.get_value("Coach Work Vehicle", {"registration_no": job["reg"]}, "name")
		if not vehicle:
			continue
		if frappe.db.exists("Coach Work Order", {"vehicle": vehicle, "docstatus": 1}):
			continue

		estimate = make_estimate(job, vehicle, rates)
		order = make_order(job, vehicle, estimate, rates, company)
		made.append(order.name)
		if job["stage"] == "Delivered" and invoice_delivered:
			invoice_order(order, company)

	repaired = repair_totals()
	settled = settle_unpaid_invoices()
	return {"jobs": made, "totals_repaired": repaired, "invoices_paid": settled}


def make_estimate(job, vehicle, rates):
	pdate = add_days(nowdate(), -16)
	doc = frappe.get_doc(
		{
			"doctype": "Job Work Estimate",
			"customer": job["customer"],
			"vehicle": vehicle,
			"posting_date": pdate,
			"valid_till": add_days(nowdate(), 14),
			"remarks": job["description"],
			"work_details": [
				{"charge": code, "qty": qty, "rate": rates.get(code) or 0} for code, qty in job["charges"]
			],
		}
	)
	doc.total_amount = compute_total(doc.work_details)
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()
	return doc.name


def make_order(job, vehicle, estimate, rates, company):
	pdate = add_days(nowdate(), -12)
	order = frappe.get_doc(
		{
			"doctype": "Coach Work Order",
			"customer": job["customer"],
			"vehicle": vehicle,
			"posting_date": pdate,
			"expected_delivery_date": add_days(nowdate(), -3 if job["stage"] == "Delivered" else 5),
			"stage": job["stage"],
			"estimate": estimate,
			"work_description": job["description"],
			"charges": [
				{"charge": code, "qty": qty, "rate": rates.get(code) or 0} for code, qty in job["charges"]
			],
		}
	)
	# walk the stage history so the log shows a real progression
	history = STAGE_HISTORY.get(job["stage"], [job["stage"]])
	order.set("stage_log", [])
	order.stage = history[0]
	order.append(
		"stage_log",
		{
			"stage": history[0],
			"moved_on": pdate + " 09:15:00",
			"moved_by": "Administrator",
			"remarks": "Job created",
		},
	)
	for index, stage in enumerate(history[1:], start=1):
		order.append(
			"stage_log",
			{
				"stage": stage,
				"moved_on": add_days(pdate, index * 2) + " 10:30:00",
				"moved_by": "Administrator",
				"remarks": "Moved to " + stage,
			},
		)
	order.stage = history[-1]

	order.total_amount = compute_total(order.charges)
	order.flags.ignore_permissions = True
	order.insert()
	order.submit()
	return order


def invoice_order(order, company):
	invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": order.customer,
			"company": company,
			"posting_date": add_days(nowdate(), -3),
			"due_date": add_days(nowdate(), 12),
			"po_no": order.name,
			"items": [
				{
					"item_code": row.charge,
					"description": row.description or frappe.db.get_value("Item", row.charge, "item_name"),
					"qty": row.qty,
					"rate": row.rate,
				}
				for row in order.charges
			],
		}
	)
	invoice.flags.ignore_permissions = True
	invoice.insert()
	invoice.submit()

	order.db_set("sales_invoice", invoice.name)
	order.db_set("status", "Closed")

	bank = frappe.db.get_value(
		"Account", {"company": invoice.company, "account_type": "Bank", "is_group": 0}, "name"
	)
	if bank and frappe.db.exists("Mode of Payment", "Bank Draft"):
		payment = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": invoice.customer,
				"company": invoice.company,
				"posting_date": add_days(nowdate(), -1),
				"paid_amount": invoice.grand_total,
				"received_amount": invoice.grand_total,
				"source_exchange_rate": 1,
				"target_exchange_rate": 1,
				"mode_of_payment": "Bank Draft",
				"paid_to": bank,
				"paid_to_account_currency": "INR",
				"references": [
					{
						"reference_doctype": "Sales Invoice",
						"reference_name": invoice.name,
						"allocated_amount": invoice.grand_total,
					}
				],
			}
		)
		payment.flags.ignore_permissions = True
		payment.insert()
		payment.submit()

	return invoice.name
