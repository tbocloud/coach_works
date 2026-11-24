# coach_works

Frappe 16 app for Unicorn Coach Works (India): one job per vehicle visit, from enquiry to delivery. Quotes, invoices and payments are ERPNext documents linked back to the job.

## Stack
- Frappe / ERPNext 16, with hrms and india_compliance on the demo site
- The local bench `/Users/sammishthundiyil/frappe-bench-tbo` runs Frappe **15**, which has no `Sidebar` or `Dock`. Use `~/frappe-bench-16` to read v16 source.
- Demo site `https://coachworks-demo.tbocloud.in`: company `Unicorn Coach Works` (abbr `UCW`), INR

## Deploy
- The app is installed on the demo site from `tbocloud/coach_works`, branch `main`.
- To deploy: push to `main`, then click **Update** on the site in the TBO Cloud dashboard. That runs migrate.
- There is no REST deployment anymore. The old `deploy_remote.py` and seed scripts are gone.

## Desk layout (Frappe 16.5x)
- One sidebar, `Coach Works` (module `Job Work`), with Dashboard first. Regenerate it with `python3 scripts/gen_desk.py`; its `SPEC` is the source of truth for the sidebar, dock and desktop tile.
- A sidebar title may not be another module's name. That is why the empty `Coach Works` module was removed.
- Migrate reaps orphaned standard Workspaces, Sidebars, Dashboards, Pages and Reports, and orphaned DocTypes. It does not reap Dashboard Charts or Number Cards.
- An app's sidebar JSON is imported with `ignore_validate`, so title rules are not enforced at import.

## Domain model
- **Coach Work Order** (shown as "Jobs") is **not submittable**.
  - The stage changes only through `move_to_stage`, and every move is appended to `stage_log`.
  - `status` follows `Work Stage.job_status`.
  - A stage with `requires_quotation` (Build by default) needs `job.quotation` to be set first.
- Quotes are ERPNext **Quotations**, linked by the custom field `coach_work_order`.
  - Submitting one moves an Enquiry job to Quoted.
  - **Accept for Job** (`accept_quotation`) copies the quote's items into the job's charges and moves the job to Approved.
- **Sales Invoice** is mapped straight from the job (`make_sales_invoice`), with no Sales Order. Submitting it sets `job.sales_invoice`, and cancelling clears it. Charges lock once the job is billed.
- **Coach Work Vehicle**: the title is `vehicle_name` (registration, else chassis). Registration and chassis numbers are upper-cased and kept unique in `validate`.
- Roles: `Job Work Manager` (everything), `Job Work User` (create and edit jobs and vehicles, read setup).

## Gotchas
- `india_compliance` enforces GSTIN check digits and a mandatory HSN/SAC on Items.
- Never hand-write GL or Stock Ledger entries. Post through Sales Invoice or Payment Entry.
- HRMS 16 resolves holidays through a submitted `Holiday List Assignment`.

## Demo data
`coach_works.demo.load_demo_data` (System Manager only) creates jobs for the demo vehicles that have none, and quotations for jobs past Enquiry. It is safe to re-run.
