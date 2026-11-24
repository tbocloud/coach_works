# Coach Works redesign

## Intent
Unicorn Coach Works builds and customises vehicles: food trucks, hearse vans, mobile ATMs, car customisation for disabled drivers, side wheel fitting. The first version of this app, built with another AI tool, works in places but is cluttered and partly broken. This redesign aims for a module that office staff and workshop supervisors (many of them older) can use without training, and that still looks professional. It keeps the normal Frappe appearance: no oversized buttons and no separate mobile screen.

## Decisions (from the conversation)
- Both office staff and supervisors use the normal desk.
- One left sidebar, **Coach Works**, with **Dashboard** first. The "Overview" workspace is removed.
- Quotes are ERPNext **Quotations**. A job can have several revised quotes. Accepting one copies its lines into the job.
- Deploying means pushing to `main` on `tbocloud/coach_works` and running Update in TBO Cloud. The app is installed properly, not pushed over REST.

## Approaches considered
- **A. Job + ERPNext Quotation** (chosen): GST, HSN, print and email already work in ERPNext. The job links to as many quotes as needed.
- B. Keep and fix the custom Job Work Estimate: we would have to build GST, print and email ourselves.
- C. One job holding quote versions inside it: revisions are hard to print or send separately.

## Design
### Job (`Coach Work Order`)
- No longer submittable. Older users should not have to understand Draft/Submit, and the submit step was what broke stage moves.
- The stage moves through buttons:
  - A primary **Move to <next stage>** button.
  - A **Change Stage** menu for any other stage.
  - Every move is written to the Stage History.
- Status (Open/Closed/Cancelled) follows the stage's `job_status`.
- A stage can be set to require an accepted quotation. The default is that **Build** requires one.
- **Create** buttons, each opening ERPNext's own form ready to review:
  - **Quotation**: as many as needed.
  - **Sales Invoice**: one per job, mapped directly. The hidden Sales Order is gone.
  - **Payment**: ERPNext's own payment entry flow.
- Connections tab: Quotations, Sales Invoices.
- Charges lock once the job is invoiced.

### Quotation and Sales Invoice
- A `coach_work_order` custom field on Quotation, alongside the existing one on Sales Invoice.
- Quotation:
  - Submitting one moves an Enquiry job to **Quoted**.
  - The **Accept for Job** button copies the quote's items into the job, links it, and moves the job to **Approved**.
  - Cancelling a quote unlinks it.
- Sales Invoice: submitting links it to the job, cancelling unlinks it.

### Vehicle
- Registration number is upper-cased and unique when given. A new build may only have a chassis number.
- The title is the registration (or chassis) number.
- A **New Job** button and a Jobs connection.
- The redundant Owner Name field is removed.

### Stages
Enquiry → Quoted → Approved → Build → Paint / Finishing → Ready → Delivered, plus Cancelled. The old stage "Estimate" is renamed to "Quoted".

### Desk
- One sidebar:
  1. Dashboard
  2. Jobs
  3. Quotations
  4. Vehicles
  5. Customers
  6. Invoices
  7. Payments
  8. Reports (Jobs In Progress, Ready for Delivery, Vehicle History)
  9. Setup (Work Stages, Vehicle Types, Items, Settings)
- One dock row.
- The app tile opens the Dashboard.
- Removed:
  - the Workspace, the Frappe Dashboard, its charts and number cards
  - the second sidebar
  - the empty `Coach Works` module
  - Job Work Estimate
  - the REST deploy and seed scripts

### Dashboard page
Normal Frappe styling, no filters to learn:
- Four counts: in progress, ready for delivery, overdue, amount to collect.
- A stage board you can click to open the filtered job list.
- An "Overdue" list and a "To collect" list.
- A "This month" strip.

### Migration (patches)
- pre: delete the empty `Coach Works` Module Def. A sidebar may not take another module's name.
- post:
  - Jobs go to docstatus 0; cancelled jobs get stage Cancelled.
  - Rename stage Estimate → Quoted.
  - Drop Job Work Estimate.
  - Drop the old desk records (workspace, dashboard, charts, cards, sidebars).

## Left to the builder
Field order, labels, colours, report columns.
