app_name = "coach_works"
app_title = "Coach Works"
app_publisher = "TBO Cloud"
app_description = "Job management for coach builders: enquiry, quotation, build, delivery and billing"
app_email = "sammish.thundiyil@gmail.com"
app_license = "mit"

required_apps = ["erpnext"]

add_to_apps_screen = [
	{
		"name": "coach_works",
		"logo": "/assets/coach_works/logo.svg",
		"title": "Coach Works",
		"route": "/desk/coach-works-dashboard",
	}
]

after_install = "coach_works.install.after_install"
after_migrate = "coach_works.install.after_migrate"

fixtures = [
	{"dt": "Role", "filters": [["role", "in", ["Job Work Manager", "Job Work User"]]]},
	{
		"dt": "Custom Field",
		"filters": [
			["dt", "in", ["Sales Invoice", "Quotation"]],
			["fieldname", "=", "coach_work_order"],
		],
	},
]

doctype_js = {"Quotation": "public/js/quotation.js"}

doc_events = {
	"Quotation": {
		"on_submit": "coach_works.events.quotation_on_submit",
		"on_cancel": "coach_works.events.quotation_on_cancel",
	},
	"Sales Invoice": {
		"on_submit": "coach_works.events.sales_invoice_on_submit",
		"on_cancel": "coach_works.events.sales_invoice_on_cancel",
	},
}
