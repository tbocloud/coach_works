#!/usr/bin/env python3
"""Seed Unicorn Coach Works demo data on a live site over the REST API.

The counterpart of ``coach_works/demo.py`` for sites where the app can be reached only through
HTTP. Records are created with the framework's own documents (Sales Order, Sales Invoice,
Payroll Entry), so the ledgers stay consistent.

Usage::

	COACH_TOKEN=<api_key>:<api_secret> python3 scripts/seed_demo_remote.py
	COACH_TOKEN=... python3 scripts/seed_demo_remote.py --only employees --only payroll
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = os.environ.get("COACH_SITE", "https://coachworks-demo.tbocloud.in").rstrip("/")
TOKEN = os.environ.get("COACH_TOKEN", "")
COMPANY = "Unicorn Coach Works"

CUSTOMERS = [
	(
		"Sharma Caterers",
		"Rohit",
		"Sharma",
		"rohit.sharma@sharmacaterers.in",
		"9820011223",
		"14, Link Road, Andheri West",
		"Mumbai",
		"Maharashtra",
		"400053",
		"27AABCS1429B1ZU",
	),
	(
		"Anand Foods Pvt Ltd",
		"Priya",
		"Anand",
		"priya@anandfoods.co.in",
		"9845098450",
		"22, Anna Salai, Teynampet",
		"Chennai",
		"Tamil Nadu",
		"600018",
		"33AAGCA2587K1ZI",
	),
	(
		"Nair Event Services",
		"Bala",
		"Nair",
		"bala@nairevents.in",
		"9947001122",
		"8, MG Road",
		"Kochi",
		"Kerala",
		"682016",
		"32AACCN1463M1ZI",
	),
	(
		"Gill Transport",
		"Harpreet",
		"Gill",
		"harpreet@gilltransport.in",
		"9815567890",
		"Plot 44, GT Road",
		"Ludhiana",
		"Punjab",
		"141001",
		"03AADCG7311P1ZK",
	),
	(
		"Iyer Sweets & Snacks",
		"Meenakshi",
		"Iyer",
		"meenakshi@iyersweets.in",
		"9900123456",
		"31, Jayanagar 4th Block",
		"Bengaluru",
		"Karnataka",
		"560011",
		"29AAECI4802Q1Z3",
	),
	(
		"Bose Mobile Banking",
		"Arindam",
		"Bose",
		"arindam@bosemobile.in",
		"9830214567",
		"7, Park Street",
		"Kolkata",
		"West Bengal",
		"700016",
		"19AAFCB6193R1ZS",
	),
	(
		"Patel Wedding Planners",
		"Jignesh",
		"Patel",
		"jignesh@patelweddings.in",
		"9925012334",
		"12, CG Road",
		"Ahmedabad",
		"Gujarat",
		"380009",
		"24AAKCP9054L1ZW",
	),
	(
		"Khan Hospitality",
		"Imran",
		"Khan",
		"imran@khanhospitality.in",
		"9871234560",
		"56, Banjara Hills",
		"Hyderabad",
		"Telangana",
		"500034",
		"36AAMCK3391N1ZU",
	),
]

ITEMS = [
	("CW-FOODTRUCK-BUILD", "Food Truck Body Build", 185000, "995729"),
	("CW-HEARSE-BUILD", "Hearse Van Conversion", 225000, "995729"),
	("CW-MOBILE-ATM", "Mobile ATM Van Fitout", 340000, "995729"),
	("CW-SIDEWHEEL", "Side Wheel Fixing", 18500, "998714"),
	("CW-PAINT", "Panel Painting and Finishing", 42000, "995461"),
	("CW-INTERIOR", "Interior Fabrication and Fitout", 98000, "995462"),
	("CW-ELECTRICAL", "Electrical and Lighting Work", 26000, "995461"),
	("CW-GASLINE", "Commercial Gas Line Fitting", 32000, "995461"),
	("CW-AC-SERVICE", "Air Conditioning Service", 8500, "998714"),
	("CW-BODY-REPAIR", "Denting and Body Repair", 24000, "998714"),
]

VEHICLES = [
	("MH-02-CD-4412", "Food Truck", "Tata Winger 3200", "Sharma Caterers", "Rohit Sharma", 2019),
	("MH-01-KL-8890", "Food Truck", "Force Traveller 3350", "Anand Foods Pvt Ltd", "Priya Anand", 2021),
	("TN-09-BE-1123", "Hearse Van", "Toyota Innova Crysta", "Nair Event Services", "Bala Nair", 2020),
	("PB-10-AF-7721", "Side Wheel Fixing", "Mahindra Bolero Pickup", "Gill Transport", "Harpreet Gill", 2018),
	("KA-05-MJ-3390", "Mini Food Truck", "Maruti Eeco", "Iyer Sweets & Snacks", "Meenakshi Iyer", 2022),
	("WB-02-AL-5567", "Mobile ATM", "Ashok Leyland Dost", "Bose Mobile Banking", "Arindam Bose", 2021),
	("GJ-01-RT-2204", "Car Customization", "Mahindra Thar", "Patel Wedding Planners", "Jignesh Patel", 2023),
	("TS-09-EF-9081", "Food Truck", "Tata Ace Gold", "Khan Hospitality", "Imran Khan", 2020),
]

JOBS = [
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
		"KA-05-MJ-3390",
		"Iyer Sweets & Snacks",
		"Enquiry",
		"Mini food truck fitout with cold storage counter.",
		[("CW-INTERIOR", 1), ("CW-AC-SERVICE", 1)],
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
	("Arjun", "Menon", "9820112233", "arjun.menon@unicorncoachworks.in", "Production Manager", "2019-06-10"),
	(
		"Sneha",
		"Kulkarni",
		"9820445566",
		"sneha.kulkarni@unicorncoachworks.in",
		"Senior Fabricator",
		"2020-02-17",
	),
	("Rakesh", "Yadav", "9811223344", "rakesh.yadav@unicorncoachworks.in", "Painter", "2021-08-02"),
	(
		"Divya",
		"Pillai",
		"9847008899",
		"divya.pillai@unicorncoachworks.in",
		"Accounts Executive",
		"2020-11-05",
	),
	("Manoj", "Verma", "9910334455", "manoj.verma@unicorncoachworks.in", "Electrician", "2022-01-24"),
	("Fatima", "Sheikh", "9873556677", "fatima.sheikh@unicorncoachworks.in", "Store Keeper", "2021-04-12"),
	("Vikram", "Singh", "9876501234", "vikram.singh@unicorncoachworks.in", "Upholsterer", "2022-09-19"),
	("Lakshmi", "Raman", "9840112233", "lakshmi.raman@unicorncoachworks.in", "HR Executive", "2023-03-06"),
	("Sohail", "Ansari", "9820778899", "sohail.ansari@unicorncoachworks.in", "Welder", "2021-10-11"),
	(
		"Nisha",
		"Choudhary",
		"9829112233",
		"nisha.choudhary@unicorncoachworks.in",
		"Sales Coordinator",
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


def call(method, path, payload=None):
	url = f"{SITE}{path}"
	data = json.dumps(payload).encode() if payload is not None else None
	req = urllib.request.Request(url, data=data, method=method)
	req.add_header("Authorization", f"token {TOKEN}")
	req.add_header("Content-Type", "application/json")
	req.add_header("Accept", "application/json")
	try:
		with urllib.request.urlopen(req, timeout=240) as resp:
			return 200, json.loads(resp.read().decode() or "{}")
	except urllib.error.HTTPError as e:
		body = e.read().decode()
		try:
			return e.code, json.loads(body)
		except ValueError:
			return e.code, {"_raw": body[:300]}


def api(method, path, payload=None):
	code, data = call(method, path, payload)
	if code not in (200, 201):
		raise RuntimeError(f"{method} {path} -> {code}: {str(data)[:400]}")
	return data.get("data", data.get("message", data))


def rq(path, **params):
	q = urllib.parse.urlencode(
		{k: json.dumps(v) if isinstance(v, list | dict) else v for k, v in params.items()}
	)
	return api("GET", f"{path}?{q}")


def resource(doctype):
	return f"/api/resource/{urllib.parse.quote(doctype, safe='')}"


def create(doctype, doc):
	return api("POST", resource(doctype), doc)


def submit(doctype, name):
	"""Submit a job-work document by name.

	`frappe.client.submit` reloads the document from the client payload, which drops the
	stored fields, and `docstatus` is not writable over the API, so submission goes through
	the app's own endpoint.
	"""
	code, data = call(
		"POST",
		"/api/method/coach_works.job_work.doctype.coach_work_order.coach_work_order.submit_external",
		{"doctype": doctype, "name": name},
	)
	if code not in (200, 201):
		raise RuntimeError(f"submit {doctype} {name} -> {code}: {str(data)[:300]}")
	return data.get("message")


def exists(doctype, filters):
	rows = rq(
		"/api/method/frappe.client.get_list",
		doctype=doctype,
		fields=["name"],
		filters=filters,
		limit_page_length=1,
	)
	return rows[0]["name"] if rows else None


def today(offset=0):
	import datetime

	return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()


def ensure_customers():
	print("Customers:")
	for name, first, last, email, phone, line, city, state, pin, gstin in CUSTOMERS:
		if exists("Customer", [["customer_name", "=", name]]):
			print(f"  have {name}")
			continue
		cust = create(
			"Customer",
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": "Commercial"
				if exists("Customer Group", [["name", "=", "Commercial"]])
				else "All Customer Groups",
				"territory": "India",
				"gst_category": "Registered Regular",
				"tax_id": gstin,
			},
		)
		print(f"  created {name}")
		contact = create(
			"Contact",
			{
				"doctype": "Contact",
				"first_name": first,
				"last_name": last,
				"email_ids": [{"email_id": email, "is_primary": 1}],
				"phone_nos": [{"phone": phone, "is_primary_mobile_no": 1}],
				"links": [{"link_doctype": "Customer", "link_name": cust["name"]}],
			},
		)
		create(
			"Address",
			{
				"doctype": "Address",
				"address_title": name,
				"address_type": "Billing",
				"address_line1": line,
				"city": city,
				"state": state,
				"country": "India",
				"pincode": pin,
				"gstin": gstin,
				"is_primary_address": 1,
				"links": [{"link_doctype": "Customer", "link_name": cust["name"]}],
			},
		)
		_ = contact


HSN_CODES = {
	"995729": "Maintenance and repair services of motor vehicles - other vehicles",
	"998714": "Maintenance and repair of other motor vehicles",
	"995461": "Electrical installation services",
	"995462": "Fabrication and installation of interior fittings",
}


def ensure_hsn():
	print("HSN/SAC:")
	for code, description in HSN_CODES.items():
		if exists("GST HSN Code", [["name", "=", code]]):
			print(f"  have {code}")
			continue
		create("GST HSN Code", {"doctype": "GST HSN Code", "hsn_code": code, "description": description})
		print(f"  created {code}")


def ensure_items():
	print("Items:")
	ensure_hsn()
	group = exists("Item Group", [["is_group", "=", 0]]) or "All Item Groups"
	for code, name, rate, hsn in ITEMS:
		if exists("Item", [["item_code", "=", code]]):
			print(f"  have {code}")
			continue
		create(
			"Item",
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": name,
				"item_group": group,
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
				"include_item_in_manufacturing": 0,
				"standard_rate": rate,
				"gst_hsn_code": hsn,
			},
		)
		print(f"  created {code}")


def ensure_vehicles():
	print("Vehicles:")
	for reg, vtype, make_model, customer, owner, year in VEHICLES:
		if exists("Coach Work Vehicle", [["registration_no", "=", reg]]):
			print(f"  have {reg}")
			continue
		create(
			"Coach Work Vehicle",
			{
				"doctype": "Coach Work Vehicle",
				"registration_no": reg,
				"vehicle_type": vtype,
				"make_model": make_model,
				"customer": customer,
				"owner_name": owner,
				"registration_year": year,
				"fuel_type": "Diesel",
			},
		)
		print(f"  created {reg}")


def ensure_estimates():
	print("Estimates:")
	rates = {code: rate for code, _n, rate, _h in ITEMS}
	for reg, customer, _stage, description, charges in JOBS:
		vehicle = exists("Coach Work Vehicle", [["registration_no", "=", reg]])
		if not vehicle or exists("Job Work Estimate", [["vehicle", "=", vehicle], ["docstatus", "=", 1]]):
			continue
		doc = create(
			"Job Work Estimate",
			{
				"doctype": "Job Work Estimate",
				"customer": customer,
				"vehicle": vehicle,
				"posting_date": today(-14),
				"valid_till": today(16),
				"remarks": description,
				"work_details": [{"charge": code, "qty": qty, "rate": rates[code]} for code, qty in charges],
			},
		)
		submit("Job Work Estimate", doc["name"])
		print(f"  created {doc['name']} for {reg}")


def ensure_jobs():
	print("Job Work:")
	rates = {code: rate for code, _n, rate, _h in ITEMS}
	for reg, customer, stage, description, charges in JOBS:
		vehicle = exists("Coach Work Vehicle", [["registration_no", "=", reg]])
		if not vehicle or exists("Coach Work Order", [["vehicle", "=", vehicle], ["docstatus", "=", 1]]):
			continue
		estimate = exists("Job Work Estimate", [["vehicle", "=", vehicle], ["docstatus", "=", 1]])
		doc = create(
			"Coach Work Order",
			{
				"doctype": "Coach Work Order",
				"customer": customer,
				"vehicle": vehicle,
				"posting_date": today(-10),
				"expected_delivery_date": today(-3 if stage == "Delivered" else 4),
				"stage": stage,
				"estimate": estimate,
				"work_description": description,
				"charges": [{"charge": code, "qty": qty, "rate": rates[code]} for code, qty in charges],
			},
		)
		submit("Coach Work Order", doc["name"])
		print(f"  created {doc['name']} ({stage})")


def ensure_employees():
	print("Employees:")
	for first, last, phone, email, designation, joining in EMPLOYEES:
		if exists("Employee", [["company_email", "=", email]]):
			print(f"  have {first} {last}")
			continue
		create(
			"Employee",
			{
				"doctype": "Employee",
				"first_name": first,
				"last_name": last,
				"employee_name": f"{first} {last}",
				"company": COMPANY,
				"gender": "Female" if first in ("Sneha", "Divya", "Fatima", "Lakshmi", "Nisha") else "Male",
				"date_of_birth": "1991-04-18",
				"date_of_joining": joining,
				"status": "Active",
				"designation": designation if exists("Designation", [["name", "=", designation]]) else None,
				"department": "Production" if exists("Department", [["name", "=", "Production"]]) else None,
				"company_email": email,
				"cell_number": phone,
			},
		)
		print(f"  created {first} {last} ({designation})")


def ensure_payroll():
	print("Payroll:")
	for first, last, _p, email, _d, _j in EMPLOYEES:
		employee = exists("Employee", [["company_email", "=", email]])
		if employee and not exists(
			"Salary Structure Assignment", [["employee", "=", employee], ["docstatus", "=", 1]]
		):
			print(f"  needs salary structure assignment: {first} {last}")
	print("  salary structures are created from the desk (HR > Payroll) on this site")


STEPS = {
	"customers": ensure_customers,
	"items": ensure_items,
	"vehicles": ensure_vehicles,
	"estimates": ensure_estimates,
	"jobs": ensure_jobs,
	"employees": ensure_employees,
	"payroll": ensure_payroll,
}


def main():
	global SITE, TOKEN
	parser = argparse.ArgumentParser()
	parser.add_argument("--only", choices=sorted(STEPS), action="append")
	parser.add_argument("--site")
	parser.add_argument("--token")
	args = parser.parse_args()
	if args.site:
		SITE = args.site.rstrip("/")
	if args.token:
		TOKEN = args.token
	if not TOKEN:
		sys.exit("Set COACH_TOKEN=<api_key>:<api_secret> or pass --token")

	code, me = call("GET", "/api/method/frappe.auth.get_logged_user")
	print(f"seeding {SITE} as {me.get('message')}")
	if code != 200:
		sys.exit(f"auth failed: {me}")

	for name in args.only or ["customers", "items", "vehicles", "estimates", "jobs", "employees"]:
		STEPS[name]()


if __name__ == "__main__":
	main()
