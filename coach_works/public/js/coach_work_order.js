frappe.ui.form.on("Coach Work Order", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		if (frm.doc.docstatus === 1 && !frm.doc.sales_invoice) {
			frm.add_custom_button(__("Sales Invoice"), () => {
				frappe.call({
					doc: frm.doc,
					method: "make_sales_invoice",
					freeze: true,
					freeze_message: __("Creating Sales Invoice..."),
					callback(r) {
						if (r.message) {
							frappe.show_alert({
								message: __("Sales Invoice {0} created", [r.message]),
								indicator: "green",
							});
							frm.reload_doc();
						}
					},
				});
			}).addClass("btn-primary");
		}

		if (frm.doc.docstatus !== 1) {
			return;
		}

		frappe.db
			.get_list("Work Stage", {
				fields: ["name"],
				limit_page_length: 0,
				order_by: "sequence asc",
			})
			.then((r) => {
				const stages = r.map((s) => s.name).filter((s) => s !== frm.doc.stage);
				if (!stages.length) {
					return;
				}
				stages.forEach((stage) => {
					frm.add_custom_button(
						__(stage),
						() => {
							frappe.call({
								doc: frm.doc,
								method: "move_to_stage",
								args: { stage },
								freeze: true,
								callback() {
									frm.reload_doc();
								},
							});
						},
						__("Move to Stage")
					);
				});
			});
	},
});
