import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now


class CoachWorkOrder(Document):
	def validate(self):
		self.set_totals()
		self.set_status()
		self.validate_estimate()
		if not self.stage:
			self.stage = frappe.db.get_single_value("Coach Work Settings", "default_stage") or "Enquiry"

	def before_insert(self):
		self.append_stage_log(_("Job created"))

	def on_submit(self):
		if not self.stage_log:
			self.append_stage_log(_("Job confirmed"))
		self.db_set("status", "Open")

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	def set_totals(self):
		total = 0
		for row in self.get("charges") or []:
			row.amount = flt(row.qty) * flt(row.rate)
			total += row.amount
		self.total_amount = total

	def set_status(self):
		if self.docstatus == 2:
			self.status = "Cancelled"
			return
		if self.docstatus == 1:
			self.status = "Open"
			return
		self.status = self.status or "Open"

	def validate_estimate(self):
		if not self.estimate:
			return
		estimate = frappe.db.get_value(
			"Job Work Estimate", self.estimate, ["docstatus", "customer", "vehicle"], as_dict=True
		)
		if not estimate:
			frappe.throw(_("Estimate {0} does not exist").format(self.estimate))
		if estimate.customer != self.customer or estimate.vehicle != self.vehicle:
			frappe.throw(_("Estimate {0} belongs to a different customer or vehicle").format(self.estimate))
		approval_required = frappe.db.get_single_value("Coach Work Settings", "enable_estimate_approval")
		if approval_required and estimate.docstatus != 1:
			frappe.throw(
				_("Estimate {0} must be approved before the job can be submitted").format(self.estimate)
			)

	def append_stage_log(self, remarks=None):
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
		stage_status = frappe.db.get_value("Work Stage", stage, "job_status")
		if stage_status is None:
			frappe.throw(_("Work Stage {0} does not exist").format(stage))
		self.stage = stage
		self.status = stage_status
		self.append_stage_log(remarks)
		self.save()
		return self.status

	@frappe.whitelist()
	def make_sales_invoice(self):
		if self.docstatus != 1:
			frappe.throw(_("Submit the job before creating an invoice"))
		if self.sales_invoice:
			frappe.throw(_("Sales Invoice {0} already exists for this job").format(self.sales_invoice))
		if not self.get("charges"):
			frappe.throw(_("Add at least one charge before creating an invoice"))

		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

		order = frappe.new_doc("Sales Order")
		order.customer = self.customer
		order.company = frappe.db.get_single_value(
			"Coach Work Settings", "company"
		) or frappe.defaults.get_defaults().get("company")
		order.transaction_date = self.posting_date
		order.delivery_date = self.expected_delivery_date or self.posting_date
		order.po_no = self.name
		for row in self.charges:
			order.append(
				"items",
				{
					"item_code": row.charge,
					"description": row.description or frappe.db.get_value("Item", row.charge, "item_name"),
					"qty": row.qty,
					"rate": row.rate,
				},
			)
		order.flags.ignore_permissions = True
		order.insert()
		order.submit()

		invoice = make_sales_invoice(order.name)
		invoice.flags.ignore_permissions = True
		invoice.insert()

		self.db_set("sales_invoice", invoice.name)
		return invoice.name
