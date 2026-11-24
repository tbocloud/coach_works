const STAGE_INDICATOR = {
	Enquiry: "gray",
	Quoted: "purple",
	Approved: "blue",
	Build: "orange",
	"Paint / Finishing": "yellow",
	Ready: "cyan",
	Delivered: "green",
	Cancelled: "red",
};

frappe.listview_settings["Coach Work Order"] = {
	add_fields: ["stage", "status", "expected_delivery_date", "customer_name", "sales_invoice"],
	filters: [["status", "=", "Open"]],

	get_indicator(doc) {
		const stage = doc.stage || __("Enquiry");
		const late =
			doc.status === "Open" &&
			doc.expected_delivery_date &&
			doc.expected_delivery_date < frappe.datetime.get_today();
		if (late && doc.stage !== "Ready") {
			return [__("{0} · Late", [__(stage)]), "red", `stage,=,${stage}`];
		}
		return [__(stage), STAGE_INDICATOR[stage] || "orange", `stage,=,${stage}`];
	},
};
