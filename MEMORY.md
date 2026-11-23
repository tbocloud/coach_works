# coach_works

Frappe 16 app for Unicorn Coach Works (India): job-work flow from Enquiry to Delivered, with accounting left to ERPNext Sales Invoice.

## Stack
- Frappe 16.5x+ (demo site runs 16.60.2, ERPNext 16.60.0, hrms 16.60.0, india_compliance)
- Local bench `/Users/sammishthundiyil/frappe-bench-tbo` is Frappe **15** — no `Sidebar`/`Dock` DocTypes, so desk files can only be verified by migrate on a v16 site
- Demo site `https://coachworks-demo.tbocloud.in`, user `demo@tbocloud.in`, company `Unicorn Coach Works` (abbr `UCW`), INR
- No SSH to the demo host; everything is deployed over the REST API

## Desk layout (Frappe 16.5x paths)
- Dock: `coach_works/dock/coach_works/coach_works.json` (`name` = app, `standard: 1`, `user: ""`)
- Sidebars: `coach_works/<scrub(module)>/sidebar/<scrub(title)>/<scrub(title)>.json` — `name` = `title`
- Tile: `coach_works/desktop_icon/coach_works.json`
- Sidebar titles: exact own module name, or a name matching no module on the site; slug must be unique
- Regenerate with `python3 scripts/gen_desk.py` (its `SPEC` is the source of truth)
- `Workspace.type` is mandatory — an empty `type` leaves the page with a blank body
- Dashboard Charts: `chart_type` is the aggregation (`Sum`/`Group By`), `type` is the visual (`Line`/`Bar`/`Donut`)

## Deploy
- `scripts/deploy_remote.py --only module|doctypes|dashboard|reports|workspace|desk`
- `Module Def` "Job Work" must be `custom: 1`: the DocTypes are deployed over REST, so the module has no package on the server disk and desk raises `Module Job Work not found` otherwise
- `scripts/seed_demo_server_script.py` pushes `coach_works/demo.py` as a Server Script and runs it

## Server Script sandbox limits
- No `import`, no `__import__`, no underscore-prefixed names (`_make_order` → `SyntaxError`), no private attributes (`frappe.__version__`)
- No controller methods on deployed DocTypes — `set_totals`, `append_stage_log` etc. do not exist there; compute inline
- A Server Script runs in a transaction: call `frappe.db.commit()` or the writes roll back silently
- Use `frappe.utils.*` namespaced calls; the `frappe` module surface is partial (`get_module_path`, `has_permission`, `clear_cache`, `client.*` may be absent)

## Frappe 16 / API gotchas
- `frappe.client.submit` cannot submit over REST; set `doc.docstatus = 1; doc.save()` server-side instead
- Standard records (Report `is_standard`, Sidebar, Dock) cannot be written over the API unless the site is in developer mode — deploy as site-owned for Reports
- A submitted document cannot be saved again; child-table display values must go through `frappe.db.set_value`
- `db.set_value` leaves stale cached docs — use `doc.db_set` where payroll validation reads the value back
- Naming-series counters are not rolled back by a failed transaction; a duplicate `insert()` in the same flow causes `DuplicateEntryError`

## Domain rules
- DocTypes use spaced names: `Coach Work Order`, `Coach Work Vehicle` (NOT `Vehicle` — ERPNext owns that), `Job Work Estimate`, `Job Work Charge`, `Work Stage`, `Vehicle Type`, `Coach Work Settings`, `Job Work Stage Log`
- `Sales Invoice.coach_work_order` is a fixture Custom Field linking the invoice back to its job (Connections tab)
- HRMS 16 resolves holidays through a submitted `Holiday List Assignment`; `Employee.holiday_list` and `Company.default_holiday_list` are no longer read
- `india_compliance` enforces GSTIN check digits and a mandatory HSN/SAC on Items
- Never hand-write GL/Stock Ledger entries; post through Sales Invoice / Payment Entry

## Demo data
- 8 real Indian customers, 10 items (HSN `995729`/`998714`/`995461`/`995462`), 8 vehicles, 8 jobs across all stages, 8 estimates, 1 paid invoice, 10 employees with assignments and 10 submitted salary slips
- Seeder is re-runnable: existing jobs and invoices are skipped
