// Coach Works dashboard: what is in the workshop, what is late, and what is owed.
// Plain Frappe styling, no filters to learn; every number opens the list behind it.

const CW_STAGE_COLOR = {
	Enquiry: "gray",
	Quoted: "purple",
	Approved: "blue",
	Build: "orange",
	"Paint / Finishing": "yellow",
	Ready: "cyan",
	Delivered: "green",
	Cancelled: "red",
};

frappe.pages["coach-works-dashboard"].on_page_load = function (wrapper) {
	frappe.coach_works_dashboard = new CoachWorksDashboard(wrapper);
};

frappe.pages["coach-works-dashboard"].on_page_show = function () {
	frappe.coach_works_dashboard && frappe.coach_works_dashboard.refresh();
};

class CoachWorksDashboard {
	constructor(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Dashboard"),
			single_column: true,
		});
		this.page.set_primary_action(
			__("New Job"),
			() => frappe.new_doc("Coach Work Order"),
			"add"
		);
		this.page.set_secondary_action(__("Refresh"), () => this.refresh(), "refresh");
		this.$body = $(`<div class="cwd"></div>`).appendTo(this.page.main);
		this.add_styles();
		this.$body.on("click", "[data-route]", (e) => {
			e.preventDefault();
			const route = $(e.currentTarget).data("route");
			frappe.route_options = $(e.currentTarget).data("filters") || null;
			frappe.set_route(...route);
		});
	}

	refresh() {
		frappe.call("coach_works.api.get_dashboard_data").then(({ message }) => {
			if (message) this.render(message);
		});
	}

	render(d) {
		const money = (v) => format_currency(v);
		this.$body.html(`
			<div class="cwd-tiles">
				${this.tile(
					__("Jobs in progress"),
					d.tiles.in_progress,
					__("Worth {0}", [money(d.tiles.open_value)]),
					["List", "Coach Work Order"],
					{ status: "Open" }
				)}
				${this.tile(
					__("Ready for delivery"),
					d.tiles.ready,
					__("Call the customer"),
					["List", "Coach Work Order"],
					{ status: "Open", stage: "Ready" }
				)}
				${this.tile(
					__("Late jobs"),
					d.tiles.late,
					d.tiles.late ? __("Past promised delivery") : __("All on time"),
					["List", "Coach Work Order"],
					{ status: "Open", expected_delivery_date: ["<", frappe.datetime.get_today()] },
					d.tiles.late ? "text-danger" : ""
				)}
				${this.tile(
					__("To collect"),
					money(d.tiles.to_collect),
					__("Unpaid job invoices"),
					["List", "Sales Invoice"],
					{ docstatus: 1, outstanding_amount: [">", 0], coach_work_order: ["is", "set"] }
				)}
			</div>

			<div class="cwd-card">
				<div class="cwd-title">${__("Jobs by stage")}</div>
				<div class="cwd-stages">${d.stages.map((s) => this.stage(s, money)).join("")}</div>
			</div>

			<div class="cwd-grid">
				<div class="cwd-card">
					<div class="cwd-title">${__("Late jobs")}</div>
					${this.job_table(
						d.late,
						(j) =>
							`<span class="text-danger">${__("{0} days late", [-j.days])}</span>`,
						__("No late jobs."),
						d.late_more
					)}
				</div>
				<div class="cwd-card">
					<div class="cwd-title">${__("Due in the next 7 days")}</div>
					${this.job_table(
						d.due_soon,
						(j) => (j.days === 0 ? __("Today") : __("In {0} days", [j.days])),
						__("Nothing due this week.")
					)}
				</div>
			</div>

			<div class="cwd-grid">
				<div class="cwd-card">
					<div class="cwd-title">${__("Money to collect")}</div>
					${this.invoice_table(d.unpaid, money, d.unpaid_more)}
				</div>
				<div class="cwd-card">
					<div class="cwd-title">${__("This month")}</div>
					<div class="cwd-month">
						${this.stat(__("Jobs received"), d.month.received)}
						${this.stat(__("Jobs delivered"), d.month.delivered)}
						${this.stat(__("Invoiced"), money(d.month.invoiced))}
						${this.stat(__("Collected"), money(d.month.collected))}
					</div>
				</div>
			</div>
		`);
	}

	link_attrs(route, filters) {
		const esc = frappe.utils.escape_html;
		return `data-route='${esc(JSON.stringify(route))}' data-filters='${esc(
			JSON.stringify(filters || null)
		)}'`;
	}

	tile(label, value, note, route, filters, value_class = "") {
		return `
			<a class="cwd-tile cwd-card" href="#" ${this.link_attrs(route, filters)}>
				<div class="cwd-label">${label}</div>
				<div class="cwd-value ${value_class}">${value}</div>
				<div class="cwd-note">${note}</div>
			</a>`;
	}

	stage(s, money) {
		const esc = frappe.utils.escape_html;
		return `
			<a class="cwd-stage" href="#" ${this.link_attrs(["List", "Coach Work Order"], {
				status: "Open",
				stage: s.stage,
			})}>
				<span class="indicator-pill ${CW_STAGE_COLOR[s.stage] || "gray"}">${esc(__(s.stage))}</span>
				<div class="cwd-value">${s.count}</div>
				<div class="cwd-note">${s.count ? money(s.value) : "&nbsp;"}</div>
			</a>`;
	}

	stat(label, value) {
		return `<div><div class="cwd-label">${label}</div><div class="cwd-stat">${value}</div></div>`;
	}

	job_table(rows, when, empty, more) {
		if (!rows.length) return `<div class="cwd-empty">${empty}</div>`;
		const esc = frappe.utils.escape_html;
		return `
			<table class="table table-sm cwd-table">
				<thead><tr>
					<th>${__("Job")}</th><th>${__("Customer")}</th><th>${__("Vehicle")}</th>
					<th>${__("Stage")}</th><th class="text-right">${__("Promised")}</th>
				</tr></thead>
				<tbody>${rows
					.map(
						(j) => `<tr>
						<td><a href="#" ${this.link_attrs(["Form", "Coach Work Order", j.name])}>${esc(j.name)}</a></td>
						<td>${esc(j.customer_name || "")}</td>
						<td>${esc(j.vehicle || "")}</td>
						<td><span class="indicator-pill ${CW_STAGE_COLOR[j.stage] || "gray"}">${esc(
							__(j.stage || "")
						)}</span></td>
						<td class="text-right">${frappe.datetime.str_to_user(j.promised)}<div class="cwd-note">${when(
							j
						)}</div></td>
					</tr>`
					)
					.join("")}</tbody>
			</table>
			${more ? `<div class="cwd-note">${__("and {0} more", [more])}</div>` : ""}`;
	}

	invoice_table(rows, money, more) {
		if (!rows.length) return `<div class="cwd-empty">${__("Everything is paid.")}</div>`;
		const esc = frappe.utils.escape_html;
		return `
			<table class="table table-sm cwd-table">
				<thead><tr>
					<th>${__("Invoice")}</th><th>${__("Customer")}</th><th>${__("Job")}</th>
					<th class="text-right">${__("Amount due")}</th>
				</tr></thead>
				<tbody>${rows
					.map(
						(r) => `<tr>
						<td><a href="#" ${this.link_attrs(["Form", "Sales Invoice", r.name])}>${esc(r.name)}</a></td>
						<td>${esc(r.customer_name || "")}</td>
						<td>${
							r.job
								? `<a href="#" ${this.link_attrs([
										"Form",
										"Coach Work Order",
										r.job,
								  ])}>${esc(r.job)}</a>`
								: ""
						}</td>
						<td class="text-right">${money(r.outstanding)}
							<div class="cwd-note ${r.days_overdue > 0 ? "text-danger" : ""}">${
							r.days_overdue > 0
								? __("{0} days overdue", [r.days_overdue])
								: r.due_date
								? __("Due {0}", [frappe.datetime.str_to_user(r.due_date)])
								: ""
						}</div>
						</td>
					</tr>`
					)
					.join("")}</tbody>
			</table>
			${more ? `<div class="cwd-note">${__("and {0} more", [more])}</div>` : ""}`;
	}

	add_styles() {
		if (document.getElementById("cwd-styles")) return;
		$(`<style id="cwd-styles">
			.cwd { padding: var(--padding-md) 0 var(--padding-xl); }
			.cwd-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--border-radius-md);
				padding: var(--padding-md) var(--padding-lg); margin-bottom: var(--margin-md); }
			.cwd-title { font-weight: 600; font-size: var(--text-md); margin-bottom: var(--margin-sm); }
			.cwd-tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--margin-md); }
			.cwd-tile { display: block; color: inherit; text-decoration: none !important; margin-bottom: var(--margin-md); }
			.cwd-tile:hover, .cwd-stage:hover { border-color: var(--gray-500); }
			.cwd-label { color: var(--text-muted); font-size: var(--text-sm); }
			.cwd-value { font-size: 1.6rem; font-weight: 600; line-height: 1.3; font-variant-numeric: tabular-nums; }
			.cwd-note { color: var(--text-muted); font-size: var(--text-xs); }
			.cwd-stages { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: var(--margin-sm); }
			.cwd-stage { display: block; color: inherit; text-decoration: none !important; border: 1px solid var(--border-color);
				border-radius: var(--border-radius); padding: var(--padding-sm) var(--padding-md); }
			.cwd-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--margin-md); }
			.cwd-table { margin: 0; font-size: var(--text-sm); }
			.cwd-table th { color: var(--text-muted); font-weight: 500; border-top: 0 !important; }
			.cwd-month { display: grid; grid-template-columns: 1fr 1fr; gap: var(--margin-md); }
			.cwd-stat { font-size: var(--text-xl); font-weight: 600; font-variant-numeric: tabular-nums; }
			.cwd-empty { color: var(--text-muted); padding: var(--padding-sm) 0; }
			@media (max-width: 991px) { .cwd-tiles { grid-template-columns: 1fr 1fr; } .cwd-grid { grid-template-columns: 1fr; } }
		</style>`).appendTo(document.head);
	}
}
