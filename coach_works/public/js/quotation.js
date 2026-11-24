// Quotations made for a Coach Works job: accept one to load its lines into the job.
frappe.ui.form.on("Quotation", {
	refresh(frm) {
		const job = frm.doc.coach_work_order;
		if (!job || frm.is_new()) return;

		frm.add_custom_button(__("Open Job"), () =>
			frappe.set_route("Form", "Coach Work Order", job)
		);

		if (frm.doc.docstatus !== 1 || frm.doc.status === "Lost") return;
		frappe.db
			.get_value("Coach Work Order", job, ["quotation", "sales_invoice"])
			.then(({ message }) => {
				if (!message || message.sales_invoice) return;
				if (message.quotation === frm.doc.name) {
					frm.dashboard.add_comment(
						__("This is the accepted quotation for job {0}.", [job]),
						"green",
						true
					);
					return;
				}
				frm.add_custom_button(__("Accept for Job"), () => {
					const replace = message.quotation
						? __("This replaces the accepted quotation {0}.", [message.quotation]) +
						  " "
						: "";
					frappe.confirm(
						replace + __("Copy these items into job {0} and mark it Approved?", [job]),
						() =>
							frappe
								.call({
									method: "coach_works.job_work.doctype.coach_work_order.coach_work_order.accept_quotation",
									args: { quotation: frm.doc.name },
									freeze: true,
								})
								.then(() => frappe.set_route("Form", "Coach Work Order", job))
					);
				}).addClass("btn-primary");
			});
	},
});
