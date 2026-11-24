"""Numbers for the Coach Works dashboard page, in one read-only round trip."""

import frappe
from frappe.utils import add_days, flt, get_first_day, getdate, nowdate

LIST_LIMIT = 8


@frappe.whitelist()
def get_dashboard_data():
	frappe.has_permission("Coach Work Order", "read", throw=True)
	today = getdate(nowdate())

	stages = frappe.get_all(
		"Work Stage",
		fields=["name", "sequence", "job_status"],
		order_by="sequence asc",
	)
	# get_list, not get_all: a user limited to some customers sees only their jobs
	open_jobs = frappe.get_list(
		"Coach Work Order",
		filters={"status": "Open"},
		fields=[
			"name",
			"customer_name",
			"vehicle",
			"stage",
			"expected_delivery_date",
			"total_amount",
		],
		limit_page_length=0,
	)
	add_vehicle_names(open_jobs)

	late, due_soon = [], []
	for job in open_jobs:
		promised = job.expected_delivery_date and getdate(job.expected_delivery_date)
		if not promised:
			continue
		job.days = (promised - today).days
		if promised < today:
			late.append(job)
		elif promised <= add_days(today, 7):
			due_soon.append(job)
	late.sort(key=lambda job: job.days)
	due_soon.sort(key=lambda job: job.days)

	unpaid = unpaid_invoices(today)

	return {
		"tiles": {
			"in_progress": len(open_jobs),
			"ready": sum(1 for job in open_jobs if job.stage == "Ready"),
			"late": len(late),
			"to_collect": flt(sum(row.outstanding_amount for row in unpaid), 2),
			"open_value": flt(sum(flt(job.total_amount) for job in open_jobs), 2),
		},
		"stages": stage_board(stages, open_jobs),
		"late": [job_row(job) for job in late[:LIST_LIMIT]],
		"late_more": max(len(late) - LIST_LIMIT, 0),
		"due_soon": [job_row(job) for job in due_soon[:LIST_LIMIT]],
		"unpaid": [invoice_row(row, today) for row in unpaid[:LIST_LIMIT]],
		"unpaid_more": max(len(unpaid) - LIST_LIMIT, 0),
		"month": this_month(today),
	}


def add_vehicle_names(jobs):
	names = {job.vehicle for job in jobs if job.vehicle}
	if not names:
		return
	titles = dict(
		frappe.get_all(
			"Coach Work Vehicle",
			filters={"name": ("in", list(names))},
			fields=["name", "vehicle_name"],
			as_list=True,
		)
	)
	for job in jobs:
		job.vehicle_name = titles.get(job.vehicle) or job.vehicle


def stage_board(stages, open_jobs):
	board = {
		stage.name: {"stage": stage.name, "count": 0, "value": 0.0}
		for stage in stages
		if stage.job_status == "Open"
	}
	for job in open_jobs:
		cell = board.setdefault(job.stage or "", {"stage": job.stage or "", "count": 0, "value": 0.0})
		cell["count"] += 1
		cell["value"] += flt(job.total_amount)
	return [cell for cell in board.values() if cell["stage"]]


def job_row(job):
	return {
		"name": job.name,
		"customer_name": job.customer_name,
		"vehicle": job.vehicle_name,
		"stage": job.stage,
		"promised": str(job.expected_delivery_date),
		"days": job.days,
	}


def unpaid_invoices(today):
	filters = {"docstatus": 1, "outstanding_amount": (">", 0), "coach_work_order": ("is", "set")}
	if not frappe.has_permission("Sales Invoice", "read"):
		return []
	return frappe.get_list(
		"Sales Invoice",
		filters=filters,
		fields=["name", "customer_name", "outstanding_amount", "due_date", "coach_work_order"],
		order_by="due_date asc",
		limit_page_length=0,
	)


def invoice_row(row, today):
	return {
		"name": row.name,
		"customer_name": row.customer_name,
		"outstanding": flt(row.outstanding_amount, 2),
		"job": row.coach_work_order,
		"due_date": str(row.due_date) if row.due_date else None,
		"days_overdue": (today - getdate(row.due_date)).days if row.due_date else 0,
	}


def this_month(today):
	start = get_first_day(today)
	between = ("between", (start, today))
	received = len(
		frappe.get_list(
			"Coach Work Order", filters={"posting_date": between}, pluck="name", limit_page_length=0
		)
	)
	delivered_stages = frappe.get_all("Work Stage", filters={"job_status": "Closed"}, pluck="name")
	delivered = 0
	if delivered_stages:
		delivered = len(
			set(
				frappe.get_all(
					"Job Work Stage Log",
					filters={
						"parenttype": "Coach Work Order",
						"stage": ("in", delivered_stages),
						"moved_on": ("between", (start, add_days(today, 1))),
					},
					pluck="parent",
				)
			)
		)

	invoiced = collected = 0
	company = frappe.db.get_single_value("Coach Work Settings", "company")
	money_filters = {"docstatus": 1, "posting_date": between}
	if company:
		money_filters["company"] = company
	# invoiced and collected are the company's whole month, the figures an owner checks
	if frappe.has_permission("Sales Invoice", "read"):
		invoiced = sum(
			flt(v)
			for v in frappe.get_list(
				"Sales Invoice", filters=money_filters, pluck="grand_total", limit_page_length=0
			)
		)
	if frappe.has_permission("Payment Entry", "read"):
		collected = sum(
			flt(v)
			for v in frappe.get_list(
				"Payment Entry",
				filters={**money_filters, "payment_type": "Receive", "party_type": "Customer"},
				pluck="received_amount",
				limit_page_length=0,
			)
		)
	return {
		"received": received,
		"delivered": delivered,
		"invoiced": flt(invoiced, 2),
		"collected": flt(collected, 2),
		"from": str(start),
	}
