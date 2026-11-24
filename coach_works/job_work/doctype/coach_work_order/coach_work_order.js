const JOB_METHODS = "coach_works.job_work.doctype.coach_work_order.coach_work_order";

frappe.ui.form.on("Coach Work Order", {
	setup(frm) {
		frm.set_query("vehicle", () => {
			const filters = { disabled: 0 };
			if (frm.doc.customer) filters.customer = frm.doc.customer;
			return { filters };
		});
		frm.set_query("charge", "charges", () => ({ filters: { disabled: 0, is_sales_item: 1 } }));
	},

	async refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(
				__("Pick the customer and vehicle, describe the work, then save."),
				"blue"
			);
			return;
		}
		frm.set_intro("");
		// a second refresh while the stages load must not add the buttons twice
		const token = (frm._cw_refresh = (frm._cw_refresh || 0) + 1);
		const stages = await coach_works.get_stages();
		if (token !== frm._cw_refresh) return;
		coach_works.show_stage_track(frm, stages);
		coach_works.add_stage_buttons(frm, stages);
		coach_works.add_create_buttons(frm);
	},

	async vehicle(frm) {
		if (!frm.doc.vehicle || frm.doc.customer) return;
		const { message } = await frappe.db.get_value(
			"Coach Work Vehicle",
			frm.doc.vehicle,
			"customer"
		);
		if (message && message.customer) frm.set_value("customer", message.customer);
	},

	customer(frm) {
		if (frm.doc.vehicle) {
			frappe.db
				.get_value("Coach Work Vehicle", frm.doc.vehicle, "customer")
				.then(({ message }) => {
					if (message && message.customer && message.customer !== frm.doc.customer) {
						frm.set_value("vehicle", "");
					}
				});
		}
	},
});

frappe.ui.form.on("Job Work Charge", {
	qty: (frm, cdt, cdn) => coach_works.update_amount(frm, cdt, cdn),
	rate: (frm, cdt, cdn) => coach_works.update_amount(frm, cdt, cdn),
	charges_remove: (frm) => coach_works.update_total(frm),
});

frappe.provide("coach_works");

Object.assign(coach_works, {
	_stages: null,

	async get_stages() {
		if (!this._stages) {
			this._stages = await frappe.db.get_list("Work Stage", {
				fields: ["name", "sequence", "job_status", "color", "requires_quotation"],
				order_by: "sequence asc",
				limit: 0,
			});
		}
		return this._stages;
	},

	next_stage(frm, stages) {
		const current = stages.find((s) => s.name === frm.doc.stage);
		if (!current || current.job_status !== "Open") return null;
		return (
			stages.find((s) => s.sequence > current.sequence && s.job_status !== "Cancelled") ||
			null
		);
	},

	show_stage_track(frm, stages) {
		const current = stages.find((s) => s.name === frm.doc.stage);
		const flow = stages.filter((s) => s.job_status !== "Cancelled");
		const esc = frappe.utils.escape_html;
		let html;
		if (current && current.job_status === "Cancelled") {
			html = `<span class="indicator-pill red">${__("Cancelled")}</span>`;
		} else {
			html = flow
				.map((s) => {
					const done = current && s.sequence < current.sequence;
					const now = current && s.name === current.name;
					const style = now
						? "font-weight:600;color:var(--text-color)"
						: done
						? "color:var(--text-muted)"
						: "color:var(--text-light)";
					const mark = done ? "✓ " : now ? "● " : "";
					return `<span style="${style}">${mark}${esc(__(s.name))}</span>`;
				})
				.join(`<span class="text-muted" style="margin:0 8px">›</span>`);
		}

		const late = this.days_late(frm);
		if (late > 0) {
			html += `<div class="text-danger" style="margin-top:6px">${__(
				"Promised delivery was {0} ({1} days ago).",
				[frappe.datetime.str_to_user(frm.doc.expected_delivery_date), late]
			)}</div>`;
		}
		frm.dashboard.set_headline_alert(`<div style="line-height:1.8">${html}</div>`);
	},

	days_late(frm) {
		if (!frm.doc.expected_delivery_date || frm.doc.status !== "Open") return 0;
		return frappe.datetime.get_day_diff(
			frappe.datetime.get_today(),
			frm.doc.expected_delivery_date
		);
	},

	add_stage_buttons(frm, stages) {
		const next = this.next_stage(frm, stages);
		if (next) {
			frm.add_custom_button(__("Move to {0}", [__(next.name)]), () =>
				this.move(frm, next)
			).addClass("btn-primary");
		}
		stages
			.filter((s) => s.name !== frm.doc.stage)
			.forEach((s) => {
				frm.add_custom_button(
					__(s.name),
					() => this.move(frm, s, true),
					__("Change Stage")
				);
			});
	},

	async move(frm, stage, ask_note) {
		if (stage.requires_quotation && !frm.doc.quotation) {
			frappe.msgprint({
				title: __("Quotation needed"),
				message: __(
					"Make a quotation for this job, submit it, and press <b>Accept for Job</b> on it before moving to {0}.",
					[__(stage.name)]
				),
				indicator: "orange",
			});
			return;
		}
		if (frm.is_dirty()) await frm.save();

		const run = (remarks) =>
			frm.call("move_to_stage", { stage: stage.name, remarks: remarks || null }).then(() => {
				frappe.show_alert({
					message: __("Moved to {0}", [__(stage.name)]),
					indicator: "green",
				});
				frm.reload_doc();
			});

		if (!ask_note) return run();
		frappe.prompt(
			{ fieldname: "remarks", fieldtype: "Small Text", label: __("Note (optional)") },
			(values) => run(values.remarks),
			__("Move to {0}", [__(stage.name)]),
			__("Move")
		);
	},

	add_create_buttons(frm) {
		const open = frm.doc.status === "Open";
		if (open && !frm.doc.sales_invoice) {
			frm.add_custom_button(
				__("Quotation"),
				() =>
					frappe.model.open_mapped_doc({ method: `${JOB_METHODS}.make_quotation`, frm }),
				__("Create")
			);
		}
		if (
			!frm.doc.sales_invoice &&
			(frm.doc.charges || []).length &&
			frm.doc.status !== "Cancelled"
		) {
			frm.add_custom_button(
				__("Sales Invoice"),
				() =>
					frappe.model.open_mapped_doc({
						method: `${JOB_METHODS}.make_sales_invoice`,
						frm,
					}),
				__("Create")
			);
		}
		if (frm.doc.sales_invoice) {
			frappe
				.call(`${JOB_METHODS}.get_billing_summary`, { job: frm.doc.name })
				.then(({ message }) => {
					if (!message) return;
					const fmt = (v) => format_currency(v);
					const settled = message.outstanding_amount <= 0 && message.docstatus === 1;
					frm.dashboard.add_comment(
						message.docstatus === 0
							? __("Invoice {0} is still a draft.", [message.name])
							: settled
							? __("Invoice {0}: {1}, fully paid.", [
									message.name,
									fmt(message.grand_total),
							  ])
							: __("Invoice {0}: {1}, {2} still to collect.", [
									message.name,
									fmt(message.grand_total),
									fmt(message.outstanding_amount),
							  ]),
						settled ? "green" : "orange",
						true
					);
					if (message.docstatus === 1 && message.outstanding_amount > 0) {
						frm.add_custom_button(
							__("Payment"),
							() => this.make_payment(message.name),
							__("Create")
						);
					}
				});
		}
	},

	make_payment(invoice) {
		frappe.call({
			method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
			args: { dt: "Sales Invoice", dn: invoice },
			freeze: true,
			callback({ message }) {
				const doc = frappe.model.sync(message)[0];
				frappe.set_route("Form", doc.doctype, doc.name);
			},
		});
	},

	update_amount(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
		this.update_total(frm);
	},

	update_total(frm) {
		const total = (frm.doc.charges || []).reduce((sum, row) => sum + flt(row.amount), 0);
		frm.set_value("total_amount", total);
	},
});
