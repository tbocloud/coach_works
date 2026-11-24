import frappe
from frappe import _
from frappe.model.document import Document


def vehicle_title(doc):
	"""How a vehicle is shown everywhere: its registration, else its chassis, else its model."""
	return doc.get("registration_no") or doc.get("chassis_no") or doc.get("make_model") or doc.get("name")


class CoachWorkVehicle(Document):
	def validate(self):
		self.registration_no = clean(self.registration_no)
		self.chassis_no = clean(self.chassis_no)
		if not (self.registration_no or self.chassis_no):
			frappe.throw(_("Enter the registration number, or the chassis number for a new build."))
		self.check_duplicate("registration_no", _("Registration No"))
		self.check_duplicate("chassis_no", _("Chassis No"))
		self.vehicle_name = vehicle_title(self)

	def check_duplicate(self, fieldname, label):
		value = self.get(fieldname)
		if not value:
			return
		other = frappe.db.get_value(
			"Coach Work Vehicle", {fieldname: value, "name": ("!=", self.name)}, "name"
		)
		if other:
			frappe.throw(
				_("{0} {1} is already saved as vehicle {2}.").format(
					label, frappe.bold(value), frappe.utils.get_link_to_form("Coach Work Vehicle", other)
				),
				title=_("Vehicle already exists"),
			)


def clean(value):
	return (value or "").strip().upper().replace(" ", "") or None
