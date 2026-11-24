"""Keep a job in step with the Quotations and Sales Invoices made for it."""

import frappe
from frappe import _

JOB = "Coach Work Order"


def linked_job(doc):
	name = doc.get("coach_work_order")
	if name and frappe.db.exists(JOB, name):
		return frappe.get_doc(JOB, name)
	return None


def quotation_on_submit(doc, method=None):
	"""A quote has gone to the customer: an enquiry becomes Quoted."""
	job = linked_job(doc)
	if not job or job.stage != "Enquiry" or not frappe.db.exists("Work Stage", "Quoted"):
		return
	job.flags.ignore_permissions = True
	job.stage = "Quoted"
	job.log_stage(_("Quotation {0} sent").format(doc.name))
	job.save()


def quotation_on_cancel(doc, method=None):
	job = linked_job(doc)
	if job and job.quotation == doc.name:
		job.db_set("quotation", None)
		job.add_comment("Info", _("Accepted quotation {0} was cancelled").format(doc.name))


def sales_invoice_on_submit(doc, method=None):
	job = linked_job(doc)
	if not job or doc.get("is_return"):
		# a credit note refers to the job's invoice; the job stays billed on the original
		return
	if job.sales_invoice and job.sales_invoice != doc.name:
		frappe.throw(_("Job {0} is already billed on Sales Invoice {1}.").format(job.name, job.sales_invoice))
	job.db_set("sales_invoice", doc.name)


def sales_invoice_on_cancel(doc, method=None):
	job = linked_job(doc)
	if job and not doc.get("is_return") and job.sales_invoice == doc.name:
		job.db_set("sales_invoice", None)
