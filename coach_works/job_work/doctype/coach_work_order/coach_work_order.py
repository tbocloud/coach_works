"""A job: one vehicle visit, from enquiry to delivery.

The job is never submitted. It moves through Work Stages, every move is written to the stage
history, and its status (Open / Closed / Cancelled) follows the stage. Money lives in ERPNext:
quotes are Quotations, billing is a Sales Invoice, both linked back by `coach_work_order`.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, now

CANCELLED = "Cancelled"


class CoachWorkOrder(Document):
	def before_insert(self):
		if not self.stage:
			self.stage = default_stage()
		self.set("stage_log", [])
		self.log_stage(_("Job created"))

	def validate(self):
		if not self.stage:
			self.stage = default_stage()
		self.set_totals()
		self.set_status()
		self.check_vehicle_owner()
		self.check_invoiced_charges()

	def on_trash(self):
		if self.sales_invoice:
			frappe.throw(
				_(
					"Job {0} is billed on Sales Invoice {1} and cannot be deleted. Set its stage to Cancelled instead."
				).format(self.name, self.sales_invoice)
			)

	def set_totals(self):
		total = 0
		for row in self.get("charges") or []:
			row.qty = flt(row.qty) or 1
			row.amount = flt(row.qty * flt(row.rate), row.precision("amount"))
			total += row.amount
		self.total_amount = flt(total, self.precision("total_amount"))

	def set_status(self):
		self.status = frappe.db.get_value("Work Stage", self.stage, "job_status") or "Open"

	def check_vehicle_owner(self):
		owner = frappe.db.get_value("Coach Work Vehicle", self.vehicle, "customer")
		if owner and owner != self.customer:
			frappe.msgprint(
				_("Vehicle {0} is registered to another customer ({1}).").format(
					frappe.bold(self.vehicle), owner
				),
				indicator="orange",
				alert=True,
			)

	def check_invoiced_charges(self):
		if self.is_new() or not self.sales_invoice:
			return
		before = self.get_doc_before_save()
		if before and flt(before.total_amount) != flt(self.total_amount):
			frappe.throw(
				_(
					"This job is already billed on {0}. Cancel or amend the invoice before changing the charges."
				).format(self.sales_invoice)
			)

	def log_stage(self, remarks=None):
		self.append(
			"stage_log",
			{
				"stage": self.stage,
				"moved_on": now(),
				"moved_by": frappe.session.user,
				"remarks": remarks,
			},
		)

	@frappe.whitelist()
	def move_to_stage(self, stage, remarks=None):
		self.check_permission("write")
		if stage == self.stage:
			return self.stage
		target = frappe.db.get_value(
			"Work Stage", stage, ["name", "job_status", "requires_quotation"], as_dict=True
		)
		if not target:
			frappe.throw(_("Work Stage {0} does not exist").format(stage))
		# read from the database: the client sends the whole form, and this rule must not trust it
		accepted = frappe.db.get_value(self.doctype, self.name, "quotation")
		if target.requires_quotation and not accepted:
			frappe.throw(
				_("Accept a quotation for this job before moving it to {0}.").format(frappe.bold(stage)),
				title=_("Quotation needed"),
			)
		self.stage = stage
		self.log_stage(remarks)
		self.save()
		return self.stage

	def accept_quotation(self, quotation):
		"""Take the accepted quote's lines as the job's charges and move the job to Approved."""
		if self.sales_invoice:
			frappe.throw(_("This job is already billed on {0}.").format(self.sales_invoice))
		if self.status != "Open":
			frappe.throw(
				_("Job {0} is {1}; a quotation can only be accepted for an open job.").format(
					self.name, frappe.bold(self.stage)
				)
			)
		self.set("charges", [])
		for item in quotation.items:
			if item.get("is_alternative"):
				continue
			self.append(
				"charges",
				{
					"charge": item.item_code,
					"description": item.item_name,
					"qty": item.qty,
					"uom": item.uom,
					"rate": item.net_rate or item.rate,
				},
			)
		self.quotation = quotation.name
		note = _("Quotation {0} accepted").format(quotation.name)
		approved = frappe.db.get_value("Work Stage", "Approved", ["name", "sequence"], as_dict=True)
		if approved and stage_sequence(self.stage) < approved.sequence:
			self.stage = approved.name
		self.log_stage(note)
		self.save()


def default_stage():
	stage = frappe.db.get_single_value("Coach Work Settings", "default_stage")
	if stage:
		return stage
	first = frappe.get_all(
		"Work Stage", filters={"job_status": "Open"}, order_by="sequence asc", pluck="name", limit=1
	)
	return first[0] if first else None


def stage_sequence(stage):
	return frappe.db.get_value("Work Stage", stage, "sequence") or 0


def job_company():
	return frappe.db.get_single_value("Coach Work Settings", "company") or frappe.defaults.get_user_default(
		"Company"
	)


def charge_rows_map(target_doctype):
	return {
		"doctype": target_doctype,
		"field_map": {"charge": "item_code", "description": "description", "qty": "qty", "rate": "rate"},
		"field_no_map": ["amount"],
	}


def fill_and_total(target):
	"""What ERPNext's own mappers do: default sales taxes, item details, then totals.

	`set_missing_values` only applies a tax template a Tax Rule picks, and the form skips its
	default for a mapped document, so the company's default template is applied here, as
	ERPNext's Opportunity -> Quotation mapper does.
	"""
	from erpnext.controllers.accounts_controller import _get_default_taxes_and_charges

	if not target.get("taxes_and_charges") and not target.get("taxes"):
		taxes = _get_default_taxes_and_charges("Sales Taxes and Charges Template", company=target.company)
		if taxes and taxes.get("taxes"):
			target.update(taxes)
	target.run_method("set_missing_values")
	target.run_method("calculate_taxes_and_totals")


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	job = frappe.get_doc("Coach Work Order", source_name)
	job.check_permission("read")
	if job.sales_invoice:
		frappe.throw(_("This job is already billed on {0}.").format(job.sales_invoice))

	def postprocess(source, target):
		target.quotation_to = "Customer"
		target.party_name = source.customer
		target.company = job_company()
		target.coach_work_order = source.name
		fill_and_total(target)

	return get_mapped_doc(
		"Coach Work Order",
		source_name,
		{
			"Coach Work Order": {"doctype": "Quotation", "field_no_map": ["naming_series", "status"]},
			"Job Work Charge": charge_rows_map("Quotation Item"),
		},
		target_doc,
		postprocess,
	)


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	job = frappe.get_doc("Coach Work Order", source_name)
	job.check_permission("read")
	existing = frappe.db.get_value(
		"Sales Invoice", {"coach_work_order": job.name, "docstatus": ("<", 2)}, "name"
	)
	if existing:
		frappe.throw(_("Sales Invoice {0} already exists for this job.").format(existing))
	if not job.charges:
		frappe.throw(_("Add the charges for this job before making the invoice."))

	def postprocess(source, target):
		target.customer = source.customer
		target.company = job_company()
		target.coach_work_order = source.name
		target.po_no = source.name
		fill_and_total(target)

	return get_mapped_doc(
		"Coach Work Order",
		source_name,
		{
			"Coach Work Order": {
				"doctype": "Sales Invoice",
				"field_no_map": ["naming_series", "status", "posting_date"],
			},
			"Job Work Charge": charge_rows_map("Sales Invoice Item"),
		},
		target_doc,
		postprocess,
	)


@frappe.whitelist()
def accept_quotation(quotation):
	"""Called from the Quotation form: this quote is the one the customer agreed to."""
	quote = frappe.get_doc("Quotation", quotation)
	quote.check_permission("read")
	if quote.docstatus != 1:
		frappe.throw(_("Submit the quotation before accepting it."))
	if not quote.get("coach_work_order"):
		frappe.throw(_("Quotation {0} is not linked to a job.").format(quote.name))
	job = frappe.get_doc("Coach Work Order", quote.coach_work_order)
	job.check_permission("write")
	job.accept_quotation(quote)
	return job.name


@frappe.whitelist()
def get_billing_summary(job):
	"""Invoice totals for the job form's headline."""
	frappe.has_permission("Coach Work Order", "read", job, throw=True)
	invoice = frappe.db.get_value("Coach Work Order", job, "sales_invoice")
	if not invoice or not frappe.has_permission("Sales Invoice", "read", invoice):
		return None
	return frappe.db.get_value(
		"Sales Invoice",
		invoice,
		["name", "grand_total", "outstanding_amount", "status", "docstatus"],
		as_dict=True,
	)
