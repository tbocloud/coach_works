"""Aggregates for the Coach Works dashboard page.

One round trip returns everything the page draws: the stage mix, the four headline tiles,
"Needs a look", "This month so far" and the per-vehicle-type table. The page is read-only, so
this is a plain whitelisted read -- no writes, no GL, no stock.
"""

import frappe
from frappe.utils import flt, getdate, nowdate

STAGES = [
	"Enquiry",
	"Estimate",
	"Approved",
	"Build",
	"Paint / Finishing",
	"Ready",
	"Delivered",
]

STAGE_COLORS = {
	"Enquiry": "#98a2b3",
	"Estimate": "#7c3aed",
	"Approved": "#2490ef",
	"Build": "#f59e0b",
	"Paint / Finishing": "#ec4899",
	"Ready": "#28a745",
	"Delivered": "#0b7285",
}


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None, stage=None, vehicle_type=None):
	"""Dashboard payload for the given period, optionally narrowed to one stage / vehicle type."""
	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or nowdate())
	if from_date > to_date:
		from_date, to_date = to_date, from_date
	month_start = getdate(to_date).replace(day=1)

	jobs = frappe.get_all(
		"Coach Work Order",
		filters={"docstatus": 1},
		fields=[
			"name",
			"customer_name",
			"stage",
			"status",
			"posting_date",
			"expected_delivery_date",
			"total_amount",
			"estimate",
			"sales_invoice",
			"vehicle",
		],
		limit_page_length=0,
		order_by="posting_date desc",
	)
	vehicles = _vehicle_types()
	for job in jobs:
		job["vehicle_type"] = vehicles.get(job.vehicle) or "Not set"

	if stage:
		jobs = [job for job in jobs if job.stage == stage]
	if vehicle_type:
		jobs = [job for job in jobs if job["vehicle_type"] == vehicle_type]

	open_jobs = [job for job in jobs if job.status == "Open"]

	return {
		"as_on": str(to_date),
		"from_date": str(from_date),
		"to_date": str(to_date),
		"stage_colors": STAGE_COLORS,
		"stages": STAGES,
		"tiles": _tiles(jobs, open_jobs),
		"by_stage": _by_stage(open_jobs),
		"needs_look": _needs_look(open_jobs, to_date),
		"period": _period(month_start, to_date),
		"by_vehicle_type": _by_vehicle_type(jobs, open_jobs),
		"filters": {"stage": stage, "vehicle_type": vehicle_type},
	}


def _vehicle_types():
	return {
		row.name: row.vehicle_type or "Not set"
		for row in frappe.get_all(
			"Coach Work Vehicle",
			fields=["name", "vehicle_type"],
			limit_page_length=0,
		)
	}


def _tiles(jobs, open_jobs):
	ready = [job for job in open_jobs if job.stage == "Ready"]
	delivered = [job for job in jobs if job.stage == "Delivered"]
	return {
		"active": len(open_jobs),
		"ready": len(ready),
		"delivered": len(delivered),
		"open_value": flt(sum(flt(job.total_amount) for job in open_jobs), 2),
		"active_count": len(jobs),
	}


def _by_stage(open_jobs):
	counts = {stage: [0, 0.0] for stage in STAGES}
	for job in open_jobs:
		bucket = counts.setdefault(job.stage or "Enquiry", [0, 0.0])
		bucket[0] += 1
		bucket[1] += flt(job.total_amount)

	total = sum(bucket[0] for bucket in counts.values()) or 1
	rows = [
		{
			"stage": stage,
			"count": bucket[0],
			"amount": flt(bucket[1], 2),
			"percent": round(bucket[0] * 100.0 / total, 1),
			"color": STAGE_COLORS.get(stage, "#98a2b3"),
		}
		for stage, bucket in counts.items()
		if bucket[0]
	]
	rows.sort(key=lambda row: STAGES.index(row["stage"]) if row["stage"] in STAGES else 99)
	return rows


def _needs_look(open_jobs, as_on):
	overdue = [job for job in open_jobs if job.expected_delivery_date and getdate(job.expected_delivery_date) < as_on]
	overdue.sort(key=lambda job: job.expected_delivery_date)
	no_estimate = [job for job in open_jobs if not job.estimate]

	unpaid = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "outstanding_amount": (">", 0)},
		fields=["name", "customer_name", "outstanding_amount", "due_date"],
		limit_page_length=0,
		order_by="due_date asc",
	)

	return {
		"overdue_count": len(overdue),
		"overdue": [
			{
				"name": job.name,
				"customer_name": job.customer_name,
				"stage": job.stage,
				"expected_delivery_date": str(job.expected_delivery_date),
				"days_late": (as_on - getdate(job.expected_delivery_date)).days,
			}
			for job in overdue[:6]
		],
		"no_estimate_count": len(no_estimate),
		"unpaid_count": len(unpaid),
		"unpaid_amount": flt(sum(flt(row.outstanding_amount) for row in unpaid), 2),
		"unpaid": [
			{
				"name": row.name,
				"customer_name": row.customer_name,
				"outstanding_amount": flt(row.outstanding_amount, 2),
				"due_date": str(row.due_date) if row.due_date else None,
			}
			for row in unpaid[:6]
		],
	}


def _period(from_date, to_date):
	created = frappe.get_all(
		"Coach Work Order",
		filters={"docstatus": 1, "posting_date": ("between", (from_date, to_date))},
		fields=["name", "total_amount"],
		limit_page_length=0,
	)
	delivered = frappe.get_all(
		"Coach Work Order",
		filters={
			"docstatus": 1,
			"stage": "Delivered",
			"posting_date": ("between", (from_date, to_date)),
		},
		pluck="name",
	)
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "posting_date": ("between", (from_date, to_date))},
		fields=["grand_total"],
		limit_page_length=0,
	)
	payments = frappe.get_all(
		"Payment Entry",
		filters={"docstatus": 1, "posting_date": ("between", (from_date, to_date))},
		fields=["paid_amount"],
		limit_page_length=0,
	)

	return {
		"jobs_created": len(created),
		"jobs_value": flt(sum(flt(row.total_amount) for row in created), 2),
		"jobs_delivered": len(delivered),
		"invoiced": flt(sum(flt(row.grand_total) for row in invoices), 2),
		"collected": flt(sum(flt(row.paid_amount) for row in payments), 2),
	}


def _by_vehicle_type(jobs, open_jobs):
	buckets = {}
	for job in jobs:
		bucket = buckets.setdefault(
			job["vehicle_type"], {"jobs": 0, "open": 0, "open_value": 0.0, "delivered": 0}
		)
		bucket["jobs"] += 1
		if job.stage == "Delivered":
			bucket["delivered"] += 1
	for job in open_jobs:
		bucket = buckets[job["vehicle_type"]]
		bucket["open"] += 1
		bucket["open_value"] += flt(job.total_amount)

	rows = [
		{
			"vehicle_type": vehicle_type,
			"jobs": bucket["jobs"],
			"open": bucket["open"],
			"open_value": flt(bucket["open_value"], 2),
			"delivered": bucket["delivered"],
		}
		for vehicle_type, bucket in buckets.items()
	]
	rows.sort(key=lambda row: (-row["jobs"], row["vehicle_type"]))
	return rows
