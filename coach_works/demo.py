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
		changed = doc.total_amount != total
		for row in doc.charges:
			line = (row.qty or 0) * (row.rate or 0)
			if row.amount != line:
				# a submitted document cannot be saved again, but the line amount is a
				# computed display value, so it is written on the row itself
				frappe.db.set_value("Job Work Charge", row.name, "amount", line, update_modified=False)
				changed = True
		if changed:
			doc.flags.ignore_permissions = True
			doc.db_set("total_amount", total, update_modified=False)
			fixed = fixed + 1
	for name in frappe.get_all("Job Work Estimate", pluck="name"):
		doc = frappe.get_doc("Job Work Estimate", name)
		total = compute_total(doc.work_details)
		changed = doc.total_amount != total
		for row in doc.work_details:
			line = (row.qty or 0) * (row.rate or 0)
			if row.amount != line:
				frappe.db.set_value("Job Work Charge", row.name, "amount", line, update_modified=False)
				changed = True
		if changed:
			doc.flags.ignore_permissions = True
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


SALARIES = {
	"Production Manager": 62000,
	"Senior Fabricator": 38000,
	"Painter": 26000,
	"Accounts Executive": 34000,
	"Electrician": 27000,
	"Store Keeper": 24000,
	"Upholsterer": 28500,
	"HR Executive": 32000,
	"Welder": 26500,
	"Sales Coordinator": 31000,
}


def ensure_component(component, abbr, kind):
	if frappe.db.exists("Salary Component", component):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Salary Component",
			"salary_component": component,
			"salary_component_abbr": abbr,
			"type": kind,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()


def ensure_holiday_list(company):
	name = "Unicorn Coach Works Holidays"
	year = nowdate()[:4]
	if not frappe.db.exists("Holiday List", name):
		holiday_list = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": name,
				"from_date": year + "-01-01",
				"to_date": year + "-12-31",
				"weekly_off": "Sunday",
				"holidays": [
					{"holiday_date": year + "-01-26", "description": "Republic Day"},
					{"holiday_date": year + "-03-04", "description": "Holi"},
					{"holiday_date": year + "-08-15", "description": "Independence Day"},
					{"holiday_date": year + "-10-02", "description": "Gandhi Jayanti"},
					{"holiday_date": year + "-11-08", "description": "Diwali"},
				],
			}
		)
		holiday_list.flags.ignore_permissions = True
		holiday_list.insert()

	# db_set clears the cached Company document; a raw set_value leaves payroll reading the
	# old value and failing with "No Holiday List was found"
	if frappe.db.get_value("Company", company, "default_holiday_list") != name:
		company_doc = frappe.get_doc("Company", company)
		company_doc.flags.ignore_permissions = True
		company_doc.db_set("default_holiday_list", name)

	# HRMS 16 resolves holidays through submitted Holiday List Assignments, not through
	# Employee.holiday_list or Company.default_holiday_list
	if not frappe.db.exists(
		"Holiday List Assignment",
		{"applicable_for": "Company", "assigned_to": company, "docstatus": 1},
	):
		assignment = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"naming_series": "HR-HLA-.YYYY.-",
				"applicable_for": "Company",
				"assigned_to": company,
				"holiday_list": name,
				"from_date": year + "-01-01",
			}
		)
		assignment.flags.ignore_permissions = True
		assignment.insert()
		assignment.submit()

	for employee in frappe.get_all("Employee", filters={"company": company}, fields=["name", "holiday_list"]):
		if not employee.holiday_list:
			frappe.db.set_value("Employee", employee.name, "holiday_list", name, update_modified=False)
	return name


def seed_payroll(company=COMPANY):
	"""Salary structure, assignments and one month of salary slips.

	India payroll validates a lot, so each step is reported rather than aborting the run: a
	demo that shows nine employees and one honest error beats one that shows nothing.
	"""
	out = {"structure": None, "assignments": 0, "slips": 0, "errors": []}
	try:
		ensure_holiday_list(company)
		ensure_component("Basic", "BASIC", "Earning")
		ensure_component("House Rent Allowance", "HRA", "Earning")
		ensure_component("Conveyance Allowance", "CONV", "Earning")
		ensure_component("Provident Fund", "PF", "Deduction")

		structure_name = frappe.db.get_value(
			"Salary Structure", {"company": company, "is_active": "Yes"}, "name"
		)
		if not structure_name:
			structure = frappe.get_doc(
				{
					"doctype": "Salary Structure",
					"name": "Coach Works Monthly - UCW",
					"company": company,
					"currency": "INR",
					"payroll_frequency": "Monthly",
					"is_active": "Yes",
					"earnings": [
						{"salary_component": "Basic", "formula": "base * 0.5"},
						{"salary_component": "House Rent Allowance", "formula": "base * 0.2"},
						{"salary_component": "Conveyance Allowance", "formula": "base * 0.1"},
					],
					"deductions": [],
				}
			)
			structure.flags.ignore_permissions = True
			structure.insert()
			structure.submit()
			structure_name = structure.name
		out["structure"] = structure_name
	except Exception as error:
		out["errors"].append("structure: " + str(error)[:200])
		return out

	employees = frappe.get_all(
		"Employee",
		filters={"company": company, "status": "Active"},
		fields=["name", "designation"],
	)
	for employee in employees:
		try:
			if frappe.db.exists("Salary Structure Assignment", {"employee": employee.name, "docstatus": 1}):
				continue
			assignment = frappe.get_doc(
				{
					"doctype": "Salary Structure Assignment",
					"employee": employee.name,
					"salary_structure": structure_name,
					"company": company,
					"currency": "INR",
					"from_date": add_days(nowdate(), -60),
					"base": SALARIES.get(employee.designation) or 26000,
				}
			)
			assignment.flags.ignore_permissions = True
			assignment.insert()
			assignment.submit()
			out["assignments"] = out["assignments"] + 1
		except Exception as error:
			out["errors"].append("assignment " + employee.name + ": " + str(error)[:160])

	start = add_days(nowdate(), -30)
	end = add_days(nowdate(), -1)
	for employee in employees:
		try:
			if frappe.db.exists(
				"Salary Slip", {"employee": employee.name, "start_date": start, "docstatus": 1}
			):
				continue
			slip = frappe.get_doc(
				{
					"doctype": "Salary Slip",
					"employee": employee.name,
					"company": company,
					"start_date": start,
					"end_date": end,
					"posting_date": end,
					"payroll_frequency": "Monthly",
					"salary_structure": structure_name,
				}
			)
			slip.flags.ignore_permissions = True
			slip.insert()
			slip.submit()
			out["slips"] = out["slips"] + 1
		except Exception as error:
			out["errors"].append("slip " + employee.name + ": " + str(error)[:160])
	return out


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
	payroll = seed_payroll(company)
	return {
		"jobs": made,
		"totals_repaired": repaired,
		"invoices_paid": settled,
		"payroll": payroll,
	}


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
