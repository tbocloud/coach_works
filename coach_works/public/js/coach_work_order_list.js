frappe.listview_settings["Coach Work Order"] = {
	add_fields: ["customer_name", "stage", "status", "expected_delivery_date", "total_amount"],
	get_indicator(doc) {
		if (doc.status === "Closed") {
			return [__("Delivered"), "green", "status,=,Closed"];
		}
		if (doc.status === "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		}
		if (doc.stage === "Ready") {
			return [__(doc.stage), "blue", "stage,=,Ready"];
		}
		return [__(doc.stage || "Open"), "orange", `stage,=,${doc.stage || "Open"}`];
	},
};
