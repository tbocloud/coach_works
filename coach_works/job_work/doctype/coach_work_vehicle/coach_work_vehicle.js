frappe.ui.form.on("Coach Work Vehicle", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("New Job"), () =>
			frappe.new_doc("Coach Work Order", {
				vehicle: frm.doc.name,
				customer: frm.doc.customer,
			})
		).addClass("btn-primary");
	},
});
