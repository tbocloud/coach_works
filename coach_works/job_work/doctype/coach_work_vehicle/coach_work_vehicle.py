import frappe
from frappe.model.document import Document


class CoachWorkVehicle(Document):
	def validate(self):
		if self.registration_no:
			self.registration_no = self.registration_no.strip().upper().replace(" ", "")
