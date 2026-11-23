"""Demo data for Unicorn Coach Works (India).

Run with::

	bench --site <site> execute coach_works.demo.load_demo_data

Everything is created through the ERPNext framework (Sales Order, Sales Invoice,
Payroll Entry), so the general ledger and stock ledger stay balanced.
"""

import frappe
from frappe.utils import add_days, nowdate

COMPANY = "Unicorn Coach Works"

CUSTOMERS = [
	(
		"Sharma Caterers",
		"Rohit Sharma",
		"rohit.sharma@sharmacaterers.in",
		"9820011223",
		"14, Link Road, Andheri West, Mumbai 400053",
		"Maharashtra",
		"27AABCS1429B1ZU",
	),
	(
		"Anand Foods Pvt Ltd",
		"Priya Anand",
		"priya@anandfoods.co.in",
		"9845098450",
		"22, Anna Salai, Teynampet, Chennai 600018",
		"Tamil Nadu",
		"33AAGCA2587K1ZI",
	),
	(
		"Nair Event Services",
		"Bala Nair",
		"bala@nairevents.in",
		"9947001122",
		"8, MG Road, Kochi 682016",
		"Kerala",
		"32AACCN1463M1ZI",
	),
	(
		"Gill Transport",
		"Harpreet Gill",
		"harpreet@gilltransport.in",
		"9815567890",
		"Plot 44, GT Road, Ludhiana 141001",
		"Punjab",
		"03AADCG7311P1ZK",
	),
	(
		"Iyer Sweets & Snacks",
		"Meenakshi Iyer",
		"meenakshi@iyersweets.in",
		"9900123456",
		"31, Jayanagar 4th Block, Bengaluru 560011",
		"Karnataka",
		"29AAECI4802Q1Z3",
	),
	(
		"Bose Mobile Banking",
		"Arindam Bose",
		"arindam@bosemobile.in",
		"9830214567",
		"7, Park Street, Kolkata 700016",
		"West Bengal",
		"19AAFCB6193R1ZS",
	),
	(
		"Patel Wedding Planners",
		"Jignesh Patel",
		"jignesh@patelweddings.in",
		"9925012334",
		"12, CG Road, Ahmedabad 380009",
		"Gujarat",
		"24AAKCP9054L1ZW",
	),
	(
		"Khan Hospitality",
		"Imran Khan",
		"imran@khanhospitality.in",
		"9871234560",
		"56, Banjara Hills, Hyderabad 500034",
		"Telangana",
		"36AAMCK3391N1ZU",
	),
]

ITEMS = [
	("CW-FOODTRUCK-BUILD", "Food Truck Body Build", "Services", "Nos", 185000),
	("CW-HEARSE-BUILD", "Hearse Van Conversion", "Services", "Nos", 225000),
	("CW-MOBILE-ATM", "Mobile ATM Van Fitout", "Services", "Nos", 340000),
	("CW-SIDEWHEEL", "Side Wheel Fixing", "Services", "Nos", 18500),
	("CW-PAINT", "Panel Painting and Finishing", "Services", "Nos", 42000),
	("CW-INTERIOR", "Interior Fabrication and Fitout", "Services", "Nos", 98000),
	("CW-ELECTRICAL", "Electrical and Lighting Work", "Services", "Nos", 26000),
	("CW-GASLINE", "Commercial Gas Line Fitting", "Services", "Nos", 32000),
	("CW-AC-SERVICE", "Air Conditioning Service", "Services", "Nos", 8500),
	("CW-BODY-REPAIR", "Denting and Body Repair", "Services", "Nos", 24000),
]

VEHICLES = [
	("MH-02-CD-4412", "Food Truck", "Tata Winger 3200", "Sharma Caterers", "Rohit Sharma", 2019, "Diesel"),
	(
		"MH-01-KL-8890",
		"Food Truck",
		"Force Traveller 3350",
		"Anand Foods Pvt Ltd",
		"Priya Anand",
		2021,
		"Diesel",
	),
	(
		"TN-09-BE-1123",
		"Hearse Van",
		"Toyota Innova Crysta",
		"Nair Event Services",
		"Bala Nair",
		2020,
		"Diesel",
	),
	(
		"PB-10-AF-7721",
		"Side Wheel Fixing",
		"Mahindra Bolero Pickup",
		"Gill Transport",
		"Harpreet Gill",
		2018,
		"Diesel",
	),
	(
		"KA-05-MJ-3390",
		"Mini Food Truck",
		"Maruti Eeco",
		"Iyer Sweets & Snacks",
		"Meenakshi Iyer",
		2022,
		"Petrol",
	),
	(
		"WB-02-AL-5567",
		"Mobile ATM",
		"Ashok Leyland Dost",
		"Bose Mobile Banking",
		"Arindam Bose",
		2021,
		"Diesel",
	),
	(
		"GJ-01-RT-2204",
		"Car Customization",
		"Mahindra Thar",
		"Patel Wedding Planners",
		"Jignesh Patel",
		2023,
		"Diesel",
	),
	("TS-09-EF-9081", "Food Truck", "Tata Ace Gold", "Khan Hospitality", "Imran Khan", 2020, "CNG"),
]

JOBS = [
	(
		"KA-05-MJ-3390",
		"Iyer Sweets & Snacks",
		"Enquiry",
		"Mini food truck fitout with cold storage counter.",
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
		"Thar interior customisation and lighting upgrade.",
		[("CW-INTERIOR", 1), ("CW-ELECTRICAL", 1)],
	),
	(
		"TS-09-EF-9081",
		"Khan Hospitality",
		"Delivered",
		"Food truck build delivered and invoiced.",
		[("CW-FOODTRUCK-BUILD", 1)],
	),
]

EMPLOYEES = [
	(
		"Arjun Menon",
		"9820112233",
		"arjun.menon@unicorncoachworks.in",
		"Production Manager",
		"Operations",
		"2019-06-10",
	),
	(
		"Sneha Kulkarni",
		"9820445566",
		"sneha.kulkarni@unicorncoachworks.in",
		"Senior Fabricator",
		"Production",
		"2020-02-17",
	),
	(
		"Rakesh Yadav",
		"9811223344",
		"rakesh.yadav@unicorncoachworks.in",
		"Painter",
		"Paint Shop",
		"2021-08-02",
	),
	(
		"Divya Pillai",
		"9847008899",
		"divya.pillai@unicorncoachworks.in",
		"Accounts Executive",
		"Accounts",
		"2020-11-05",
	),
	(
		"Manoj Verma",
		"9910334455",
		"manoj.verma@unicorncoachworks.in",
		"Electrician",
		"Production",
		"2022-01-24",
	),
	(
		"Fatima Sheikh",
		"9873556677",
		"fatima.sheikh@unicorncoachworks.in",
		"Store Keeper",
		"Stores",
		"2021-04-12",
	),
	(
		"Vikram Singh",
		"9876501234",
		"vikram.singh@unicorncoachworks.in",
		"Upholsterer",
		"Production",
		"2022-09-19",
	),
	(
		"Lakshmi Raman",
		"9840112233",
		"lakshmi.raman@unicorncoachworks.in",
		"HR Executive",
		"Human Resources",
		"2023-03-06",
	),
	(
		"Sohail Ansari",
		"9820778899",
		"sohail.ansari@unicorncoachworks.in",
		"Welder",
		"Production",
		"2021-10-11",
	),
	(
		"Nisha Choudhary",
		"9829112233",
		"nisha.choudhary@unicorncoachworks.in",
		"Sales Coordinator",
		"Sales",
		"2023-07-03",
	),
]

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


def load_demo_data(company=COMPANY):
	company = company if frappe.db.exists("Company", company) else frappe.db.get_default("company")
	if not company:
		frappe.throw("No company found. Create the company first.")

	_set_defaults(company)
	customers = _make_customers()
	items = _make_items()
	vehicles = _make_vehicles(company, customers)
	_make_estimates(customers, vehicles, items)
	_make_jobs(customers, vehicles, items)
	_make_employees(company)
	_make_salary_and_payroll(company)
	frappe.db.commit()
	return {"customers": len(customers), "items": len(items), "vehicles": len(vehicles)}


def _set_defaults(company):
	settings = frappe.get_doc("Coach Work Settings")
	settings.company = company
	settings.default_stage = (
		"Enquiry" if frappe.db.exists("Work Stage", "Enquiry") else settings.default_stage
	)
	settings.default_warehouse = frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
	settings.enable_estimate_approval = 0
	settings.save(ignore_permissions=True)


def _make_customers():
	created = []
	group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups"
	territory = (
		"India"
		if frappe.db.exists("Territory", "India")
		else frappe.db.get_value("Territory", {"is_group": 0}, "name")
	)
	for name, contact, email, phone, address, state, gstin in CUSTOMERS:
		if frappe.db.exists("Customer", name):
			created.append(name)
			continue
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": group,
				"territory": territory,
				"gst_category": "Registered Regular",
				"tax_id": gstin,
			}
		)
		customer.flags.ignore_permissions = True
		customer.insert()
		created.append(customer.name)
		_add_contact(customer.name, contact, email, phone)
		_add_address(customer.name, name, address, state, gstin)
	return created


def _add_contact(link_name, person, email, phone):
	doc = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": person.split(" ")[0],
			"last_name": " ".join(person.split(" ")[1:]),
			"email_ids": [{"email_id": email, "is_primary": 1}],
			"phone_nos": [{"phone": phone, "is_primary_mobile_no": 1}],
			"links": [{"link_doctype": "Customer", "link_name": link_name}],
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()


def _add_address(link_name, title, address, state, gstin):
	doc = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": title,
			"address_type": "Billing",
			"address_line1": address,
			"city": address.split(",")[-1].strip() or "Mumbai",
			"state": state,
			"country": "India",
			"pincode": "400001",
			"gstin": gstin,
			"is_primary_address": 1,
			"links": [{"link_doctype": "Customer", "link_name": link_name}],
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()


def _make_items():
	created = []
	group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
	for code, name, _kind, uom, rate in ITEMS:
		if not frappe.db.exists("Item", code):
			item = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": code,
					"item_name": name,
					"item_group": group,
					"stock_uom": uom,
					"is_stock_item": 0,
					"include_item_in_manufacturing": 0,
					"is_sales_item": 1,
					"is_service_item": 1,
					"standard_rate": rate,
				}
			)
			item.flags.ignore_permissions = True
			item.insert()
		created.append(code)
	return created


def _make_vehicles(company, customers):
	created = []
	for reg, vtype, make_model, customer, owner, year, fuel in VEHICLES:
		if frappe.db.exists("Coach Work Vehicle", {"registration_no": reg}):
			created.append(frappe.db.get_value("Coach Work Vehicle", {"registration_no": reg}, "name"))
			continue
		vehicle = frappe.get_doc(
			{
				"doctype": "Coach Work Vehicle",
				"registration_no": reg,
				"vehicle_type": vtype,
				"make_model": make_model,
				"customer": customer if customer in customers else None,
				"owner_name": owner,
				"registration_year": year,
				"fuel_type": fuel,
			}
		)
		vehicle.flags.ignore_permissions = True
		vehicle.insert()
		created.append(vehicle.name)
	return created


def _make_estimates(customers, vehicles, items):
	for reg, customer, _stage, description, charges in JOBS:
		vehicle = frappe.db.get_value("Coach Work Vehicle", {"registration_no": reg}, "name")
		if not vehicle:
			continue
		if frappe.db.exists("Job Work Estimate", {"vehicle": vehicle, "docstatus": 1}):
			continue
		estimate = frappe.get_doc(
			{
				"doctype": "Job Work Estimate",
				"customer": customer,
				"vehicle": vehicle,
				"posting_date": add_days(nowdate(), -14),
				"valid_till": add_days(nowdate(), 16),
				"remarks": description,
				"work_details": [
					{
						"charge": code,
						"description": frappe.db.get_value("Item", code, "item_name"),
						"qty": qty,
						"rate": dict((c, r) for c, _n, _k, _u, r in ITEMS)[code],
					}
					for code, qty in charges
				],
			}
		)
		estimate.flags.ignore_permissions = True
		estimate.insert()
		estimate.submit()


def _make_jobs(customers, vehicles, items):
	rates = dict((c, r) for c, _n, _k, _u, r in ITEMS)
	made = []
	for reg, customer, stage, description, charges in JOBS:
		vehicle = frappe.db.get_value("Coach Work Vehicle", {"registration_no": reg}, "name")
		if not vehicle or frappe.db.exists("Coach Work Order", {"vehicle": vehicle, "docstatus": 1}):
			continue
		estimate = frappe.db.get_value("Job Work Estimate", {"vehicle": vehicle, "docstatus": 1}, "name")
		job = frappe.get_doc(
			{
				"doctype": "Coach Work Order",
				"customer": customer,
				"vehicle": vehicle,
				"posting_date": add_days(nowdate(), -10),
				"expected_delivery_date": add_days(nowdate(), 4 if stage != "Delivered" else -3),
				"stage": stage,
				"estimate": estimate,
				"work_description": description,
				"charges": [
					{
						"charge": code,
						"description": frappe.db.get_value("Item", code, "item_name"),
						"qty": qty,
						"rate": rates[code],
					}
					for code, qty in charges
				],
			}
		)
		job.flags.ignore_permissions = True
		job.insert()
		job.submit()
		made.append(job.name)
		if stage == "Delivered":
			_invoice_job(job)
	return made


def _invoice_job(job):
	invoice_name = job.make_sales_invoice()
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	invoice.posting_date = add_days(nowdate(), -3)
	invoice.flags.ignore_permissions = True
	invoice.submit()
	if frappe.db.exists("Mode of Payment", "Bank Draft"):
		payment = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": invoice.customer,
				"company": invoice.company,
				"posting_date": add_days(nowdate(), -2),
				"paid_amount": invoice.grand_total,
				"received_amount": invoice.grand_total,
				"mode_of_payment": "Bank Draft",
				"paid_to": frappe.db.get_value(
					"Account",
					{"company": invoice.company, "account_type": "Bank", "is_group": 0},
					"name",
				),
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


def _make_employees(company):
	for full_name, phone, email, designation, department, joining in EMPLOYEES:
		if frappe.db.exists("Employee", {"employee_name": full_name}):
			continue
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": full_name.split(" ")[0],
				"last_name": " ".join(full_name.split(" ")[1:]),
				"employee_name": full_name,
				"company": company,
				"gender": "Female"
				if full_name.split(" ")[0]
				in ("Sneha", "Divya", "Fatima", "Lakshmi", "Nisha", "Meenakshi", "Priya")
				else "Male",
				"date_of_birth": "1990-05-14",
				"date_of_joining": joining,
				"status": "Active",
				"designation": designation if frappe.db.exists("Designation", designation) else None,
				"department": department if frappe.db.exists("Department", department) else None,
				"company_email": email,
				"cell_number": phone,
			}
		)
		employee.flags.ignore_permissions = True
		employee.insert()


def _make_salary_and_payroll(company):
	structure_name = "Coach Works Monthly - India"
	if not frappe.db.exists("Salary Structure", structure_name):
		earnings = []
		components = [("Basic", 50), ("House Rent Allowance", 20), ("Conveyance Allowance", 10)]
		for component, share in components:
			if not frappe.db.exists("Salary Component", component):
				frappe.get_doc(
					{
						"doctype": "Salary Component",
						"salary_component": component,
						"salary_component_abbr": component[:4].upper().replace(" ", ""),
						"type": "Earning",
					}
				).insert(ignore_permissions=True)
			earnings.append({"salary_component": component, "formula": f"base * {share / 100:.2f}"})
		structure = frappe.get_doc(
			{
				"doctype": "Salary Structure",
				"name": structure_name,
				"company": company,
				"currency": "INR",
				"is_active": "Yes",
				"payroll_frequency": "Monthly",
				"earnings": earnings,
				"deductions": [],
				"salary_slip_based_on_timesheet": 0,
			}
		)
		structure.flags.ignore_permissions = True
		structure.insert()
		structure.submit() if hasattr(structure, "submit") and structure.docstatus == 0 else None

	for full_name, _phone, _email, designation, _dept, _joining in EMPLOYEES:
		employee = frappe.db.get_value("Employee", {"employee_name": full_name}, "name")
		if not employee:
			continue
		if frappe.db.exists("Salary Structure Assignment", {"employee": employee, "docstatus": 1}):
			continue
		assignment = frappe.get_doc(
			{
				"doctype": "Salary Structure Assignment",
				"employee": employee,
				"salary_structure": structure_name,
				"company": company,
				"from_date": add_days(nowdate(), -60),
				"base": SALARIES.get(designation, 25000),
				"income_tax_slab": None,
			}
		)
		assignment.flags.ignore_permissions = True
		assignment.insert()
		assignment.submit()

	start = add_days(nowdate(), -30)
	end = add_days(nowdate(), -1)
	if frappe.db.exists("Payroll Entry", {"company": company, "start_date": start, "end_date": end}):
		return
	payroll = frappe.get_doc(
		{
			"doctype": "Payroll Entry",
			"company": company,
			"payroll_frequency": "Monthly",
			"start_date": start,
			"end_date": end,
			"posting_date": end,
			"salary_structure": structure_name,
			"payment_account": frappe.db.get_value(
				"Account", {"company": company, "account_type": "Bank", "is_group": 0}, "name"
			),
		}
	)
	payroll.flags.ignore_permissions = True
	payroll.insert()
	payroll.submit()
	payroll.create_salary_slips()
	payroll.submit_salary_slips()
