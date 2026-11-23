frappe.pages["coach-works-dashboard"].on_page_load = function (wrapper) {
	frappe.coach_works_dashboard = new CoachWorksDashboard(wrapper);
};

frappe.pages["coach-works-dashboard"].on_page_show = function () {
	if (frappe.coach_works_dashboard) {
		frappe.coach_works_dashboard.refresh();
	}
};

class CoachWorksDashboard {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Coach Works Dashboard"),
			single_column: true,
		});
		this.filters = {};
		this.make_filter_bar();
		this.make_body();
		this.refresh();
	}

	make_filter_bar() {
		const $bar = $(`
			<div class="cwdash-filters">
				<div class="cwdash-field">
					<label>${__("From")}</label>
					<input type="date" class="form-control cwdash-from">
				</div>
				<div class="cwdash-field">
					<label>${__("To")}</label>
					<input type="date" class="form-control cwdash-to">
				</div>
				<div class="cwdash-field cwdash-stage-control"></div>
				<div class="cwdash-field cwdash-type-control"></div>
				<button class="btn btn-primary btn-sm cwdash-apply">${__("Apply")}</button>
				<button class="btn btn-default btn-sm cwdash-reset">${__("Reset")}</button>
			</div>
		`).appendTo(this.page.body);

		const today = frappe.datetime.get_today();
		$bar.find(".cwdash-to").val(today);
		$bar.find(".cwdash-from").val(today.slice(0, 8) + "01");

		this.make_link_control($bar.find(".cwdash-stage-control"), __("Stage"), "Work Stage", "stage");
		this.make_link_control(
			$bar.find(".cwdash-type-control"),
			__("Vehicle Type"),
			"Vehicle Type",
			"vehicle_type"
		);

		$bar.find(".cwdash-apply").on("click", () => this.refresh());
		$bar.find(".cwdash-reset").on("click", () => {
			$bar.find(".cwdash-to").val(today);
			$bar.find(".cwdash-from").val(today.slice(0, 8) + "01");
			this.filters.stage.set_value("");
			this.filters.vehicle_type.set_value("");
			this.refresh();
		});
	}

	make_link_control($container, label, doctype, key) {
		$container.append(`<label>${label}</label>`);
		const $holder = $('<div class="cwdash-link"></div>').appendTo($container);
		this.filters[key] = frappe.ui.form.make_control({
			df: { fieldtype: "Link", options: doctype, fieldname: key, placeholder: label },
			parent: $holder,
			render_input: true,
		});
		this.filters[key].refresh();
	}

	make_body() {
		this.$body = $(`<div class="cwdash"></div>`).appendTo(this.page.body);
		this.add_styles();
	}

	add_styles() {
		if (document.getElementById("cwdash-styles")) return;
		$(`<style id="cwdash-styles">
			.cwdash-filters { display:flex; gap:12px; align-items:flex-end; flex-wrap:wrap; margin:8px 0 18px; }
			.cwdash-field { display:flex; flex-direction:column; gap:4px; min-width:150px; }
			.cwdash-field label { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--text-muted); margin:0; }
			.cwdash-link .frappe-control { margin:0 !important; }
			.cwdash { padding-bottom:32px; }
			.cwdash-panel { background:var(--card-bg); border:1px solid var(--border-color); border-radius:10px; padding:18px 20px; margin-bottom:16px; }
			.cwdash-panel h5 { font-size:15px; font-weight:600; margin:0 0 14px; }
			.cwdash-split { display:grid; grid-template-columns: 1.75fr 1fr; gap:16px; }
			@media (max-width: 1100px) { .cwdash-split { grid-template-columns: 1fr; } }
			.cwdash-stage-wrap { display:grid; grid-template-columns: 170px 1fr; gap:20px; align-items:center; }
			@media (max-width: 700px) { .cwdash-stage-wrap { grid-template-columns: 1fr; } }
			.cwdash-donut { width:150px; height:150px; border-radius:50%; display:flex; align-items:center; justify-content:center; position:relative; }
			.cwdash-donut::after { content:""; position:absolute; inset:22px; background:var(--card-bg); border-radius:50%; }
			.cwdash-donut-inner { position:relative; z-index:1; text-align:center; }
			.cwdash-donut-inner b { font-size:24px; display:block; line-height:1.1; }
			.cwdash-donut-inner span { font-size:11px; color:var(--text-muted); }
			.cwdash-tiles { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
			.cwdash-tile { border:1px solid var(--border-color); border-radius:8px; padding:10px 12px; }
			.cwdash-tile .cwdash-tile-label { font-size:12px; color:var(--text-muted); display:flex; align-items:center; gap:6px; }
			.cwdash-tile .cwdash-tile-value { font-size:20px; font-weight:600; margin-top:2px; }
			.cwdash-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
			.cwdash-look { display:flex; flex-direction:column; gap:10px; }
			.cwdash-look-row { display:flex; justify-content:space-between; align-items:center; border:1px solid var(--border-color); border-radius:8px; padding:10px 12px; }
			.cwdash-look-row .cwdash-look-label { display:flex; align-items:center; gap:10px; font-size:13px; }
			.cwdash-look-row .cwdash-look-value { font-size:18px; font-weight:600; }
			.cwdash-look-row .cwdash-look-note { font-size:12px; color:var(--text-muted); }
			.cwdash-strip { display:grid; grid-template-columns:repeat(5, 1fr); gap:12px; }
			@media (max-width: 1100px) { .cwdash-strip { grid-template-columns:repeat(2, 1fr); } }
			.cwdash-strip-item { border:1px solid var(--border-color); border-radius:8px; padding:12px 14px; }
			.cwdash-strip-item .cwdash-strip-label { font-size:12px; color:var(--text-muted); }
			.cwdash-strip-item .cwdash-strip-value { font-size:19px; font-weight:600; margin-top:2px; }
			.cwdash-table { width:100%; border-collapse:collapse; font-size:13px; }
			.cwdash-table th { text-align:left; font-weight:500; color:var(--text-muted); font-size:11px; text-transform:uppercase; letter-spacing:.04em; padding:8px 10px; border-bottom:1px solid var(--border-color); }
			.cwdash-table td { padding:9px 10px; border-bottom:1px solid var(--border-color); }
			.cwdash-table td.num, .cwdash-table th.num { text-align:right; font-variant-numeric:tabular-nums; }
			.cwdash-badge { display:inline-block; min-width:34px; text-align:center; padding:1px 8px; border-radius:10px; font-size:12px; font-weight:600; }
			.cwdash-list { display:flex; flex-direction:column; gap:8px; margin-top:10px; }
			.cwdash-list a { font-size:13px; }
			.cwdash-empty { color:var(--text-muted); font-size:13px; }
			.cwdash-bar { height:8px; border-radius:4px; background:var(--bg-color); display:flex; overflow:hidden; margin-top:12px; }
		</style>`).appendTo(document.head);
	}

	refresh() {
		const args = {
			from_date: this.$body ? this.page.body.find(".cwdash-from").val() : null,
			to_date: this.page.body.find(".cwdash-to").val(),
			stage: (this.filters.stage && this.filters.stage.get_value()) || "",
			vehicle_type: (this.filters.vehicle_type && this.filters.vehicle_type.get_value()) || "",
		};
		this.$body.html(`<div class="cwdash-panel"><span class="cwdash-empty">${__("Loading…")}</span></div>`);
		frappe.call({
			method: "coach_works.api.get_dashboard_data",
			args: args,
		}).then((r) => {
			if (r.message) this.render(r.message);
		});
	}

	render(data) {
		const fmt = (value) => frappe.format(value, { fieldtype: "Currency" });
		const esc = frappe.utils.escape_html;

		this.$body.html(`
			<div class="cwdash-split">
				<div class="cwdash-panel">
					<h5>${__("Where the work is")}</h5>
					<div class="cwdash-stage-wrap">
						${this.donut(data)}
						<div class="cwdash-tiles">
							${this.tile(__("In progress"), data.tiles.active, "#2490ef")}
							${this.tile(__("Ready for delivery"), data.tiles.ready, "#28a745")}
							${this.tile(__("Delivered"), data.tiles.delivered, "#0b7285")}
							${this.tile(__("Open job value"), fmt(data.tiles.open_value), "#ff8d00")}
						</div>
					</div>
					<div class="cwdash-bar">
						${(data.by_stage || [])
							.map(
								(row) =>
									`<div style="width:${row.percent}%;background:${row.color}" title="${esc(
										row.stage
									)}: ${row.count}"></div>`
							)
							.join("")}
					</div>
				</div>
				<div class="cwdash-panel">
					<h5>${__("Needs a look")}</h5>
					${this.needs_look(data.needs_look)}
				</div>
			</div>

			<div class="cwdash-panel">
				<h5>${__("This month so far")} <span class="text-muted" style="font-weight:400;font-size:12px">
					${frappe.datetime.str_to_user(data.from_date)} – ${frappe.datetime.str_to_user(data.to_date)}
				</span></h5>
				<div class="cwdash-strip">
					${this.strip(__("Jobs created"), data.period.jobs_created)}
					${this.strip(__("Jobs delivered"), data.period.jobs_delivered)}
					${this.strip(__("New job value"), fmt(data.period.jobs_value))}
					${this.strip(__("Invoiced"), fmt(data.period.invoiced))}
					${this.strip(__("Collected"), fmt(data.period.collected))}
				</div>
			</div>

			<div class="cwdash-panel">
				<h5>${__("By vehicle type")}</h5>
				${this.vehicle_table(data.by_vehicle_type, fmt, esc)}
			</div>
		`);
	}

	donut(data) {
		const rows = data.by_stage || [];
		const total = rows.reduce((sum, row) => sum + row.count, 0);
		let cursor = 0;
		const stops = rows
			.map((row) => {
				const start = cursor;
				cursor += row.percent;
				return `${row.color} ${start}% ${cursor}%`;
			})
			.join(", ");
		const background = stops || "var(--bg-color) 0% 100%";
		return `
			<div class="cwdash-donut" style="background: conic-gradient(${background})">
				<div class="cwdash-donut-inner">
					<b>${total}</b>
					<span>${__("open jobs")}</span>
				</div>
			</div>
		`;
	}

	tile(label, value, color) {
		return `
			<div class="cwdash-tile">
				<div class="cwdash-tile-label"><span class="cwdash-dot" style="background:${color}"></span>${label}</div>
				<div class="cwdash-tile-value">${value}</div>
			</div>
		`;
	}

	strip(label, value) {
		return `
			<div class="cwdash-strip-item">
				<div class="cwdash-strip-label">${label}</div>
				<div class="cwdash-strip-value">${value}</div>
			</div>
		`;
	}

	needs_look(look) {
		const rows = [
			{
				label: __("Overdue past planned delivery"),
				value: look.overdue_count,
				note: look.overdue_count ? __("behind schedule") : __("All on time"),
				color: "#e24c4c",
				items: look.overdue,
				render: (job) =>
					`<a href="/desk/coach-work-order/${encodeURIComponent(job.name)}">${frappe.utils.escape_html(
						job.name
					)}</a> <span class="text-muted">· ${frappe.utils.escape_html(
						job.customer_name || ""
					)} · ${job.days_late}d</span>`,
			},
			{
				label: __("Jobs with no estimate"),
				value: look.no_estimate_count,
				note: look.no_estimate_count ? __("price not quoted") : __("All quoted"),
				color: "#f59e0b",
				items: [],
			},
			{
				label: __("Unpaid invoices"),
				value: look.unpaid_count,
				note: look.unpaid_amount
					? frappe.format(look.unpaid_amount, { fieldtype: "Currency" }) + " " + __("outstanding")
					: __("All settled"),
				color: "#7c3aed",
				items: look.unpaid,
				render: (inv) =>
					`<a href="/desk/sales-invoice/${encodeURIComponent(inv.name)}">${frappe.utils.escape_html(
						inv.name
					)}</a> <span class="text-muted">· ${frappe.utils.escape_html(
						inv.customer_name || ""
					)} · ${frappe.format(inv.outstanding_amount, { fieldtype: "Currency" })}</span>`,
			},
		];

		return `
			<div class="cwdash-look">
				${rows
					.map(
						(row) => `
					<div class="cwdash-look-row">
						<div class="cwdash-look-label">
							<span class="cwdash-dot" style="background:${row.color}"></span>
							<div>
								<div>${row.label}</div>
								<div class="cwdash-look-note">${row.note}</div>
							</div>
						</div>
						<div class="cwdash-look-value">${row.value}</div>
					</div>
					${row.items && row.items.length && row.render
						? `<div class="cwdash-list">${row.items.map(row.render).join("")}</div>`
						: ""}
				`
					)
					.join("")}
			</div>
		`;
	}

	vehicle_table(rows, fmt, esc) {
		if (!rows || !rows.length) {
			return `<div class="cwdash-empty">${__("No vehicles yet.")}</div>`;
		}
		return `
			<table class="cwdash-table">
				<thead>
					<tr>
						<th>${__("Vehicle type")}</th>
						<th class="num">${__("Jobs")}</th>
						<th class="num">${__("Open")}</th>
						<th class="num">${__("Delivered")}</th>
						<th class="num">${__("Open value")}</th>
					</tr>
				</thead>
				<tbody>
					${rows
						.map(
							(row) => `
						<tr>
							<td>${esc(row.vehicle_type)}</td>
							<td class="num">${row.jobs}</td>
							<td class="num"><span class="cwdash-badge" style="background:#e6f4ff;color:#0b5cad">${row.open}</span></td>
							<td class="num"><span class="cwdash-badge" style="background:#e7f7ec;color:#1b7c3c">${row.delivered}</span></td>
							<td class="num">${fmt(row.open_value)}</td>
						</tr>`
						)
						.join("")}
				</tbody>
			</table>
		`;
	}
}
