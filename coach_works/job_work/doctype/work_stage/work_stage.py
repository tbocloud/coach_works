import frappe
from frappe import _
from frappe.model.document import Document


class WorkStage(Document):
	def validate(self):
		if self.job_status == "Cancelled" and self.requires_quotation:
			self.requires_quotation = 0

	def on_trash(self):
		if frappe.db.exists("Coach Work Order", {"stage": self.name}):
			frappe.throw(_("Jobs are still in stage {0}. Move them before deleting it.").format(self.name))
