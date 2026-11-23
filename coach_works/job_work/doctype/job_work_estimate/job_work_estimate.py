import frappe
from frappe.model.document import Document
from frappe.utils import flt


class JobWorkEstimate(Document):
	def validate(self):
		self.set_totals()

	def set_totals(self):
		total = 0
		for row in self.get("work_details") or []:
			row.amount = flt(row.qty) * flt(row.rate)
			total += row.amount
		self.total_amount = total

	def on_submit(self):
		self.db_set("status", "Approved")

	def on_cancel(self):
		self.db_set("status", "Rejected")
