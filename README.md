# Pharma Graduate Scheme Tracker (2027 intake)

This tracker checks the job boards of about 40 pharma companies, CROs and regulatory consultancies every three hours. It looks for UK graduate schemes and entry-level roles. **Regulatory affairs, medical affairs and clinical operations** come first. When a new role appears, it updates the tables below and alerts you.

It covers GSK, AstraZeneca, J&J, AbbVie, Vertex, Pfizer, Novartis, Roche, Sanofi, MSD, BMS, Takeda, Lilly, Amgen, Gilead, Biogen, Moderna, CSL, Ipsen, Daiichi Sankyo, Regeneron, Bayer, Boehringer Ingelheim, UCB and Haleon. It also covers Medpace, Hammersmith Medicines Research, IQVIA, ICON, Parexel, Syneos Health, Thermo Fisher (PPD), Fortrea, Labcorp, Worldwide Clinical Trials, Richmond Pharmacology, PSI, MAC Clinical Research, Quotient Sciences and Cencora PharmaLex. The full list is in [`config/companies.yaml`](config/companies.yaml).

## How it works

1. A GitHub Actions job runs every three hours. It reads each company's job board directly, filtered to UK roles.
2. Each role is sorted into an area (regulatory, medical, clinical operations, drug safety, clinical data, medical writing, or another graduate scheme) and a level:
   - **Graduate scheme:** the title says graduate, future leaders, early talent and so on.
   - **Entry level:** trainee, assistant, associate, "CRA I" and similar.
   - **Check seniority:** the title doesn't say. The tracker reads the full advert and flags roles that ask for 2+ years' experience.
3. It skips senior roles, internships, placements and PhD posts. It also skips graduate schemes in unrelated functions such as engineering, IT and finance.
4. Adverts naming an earlier intake, such as "Graduate Programme 2026", are moved to a separate section. That keeps 2027 roles at the top.
5. New roles trigger alerts. A role that disappears from its job board is marked closed.

The rules live in [`config/search.yaml`](config/search.yaml), which you can edit without touching any code.

## Getting alerts

- **GitHub issues (on by default).** Each run with new roles opens an issue listing them. GitHub emails you about it and it shows in the GitHub mobile app. If you don't get them, click **Watch → All activity** on this repository.
- **Phone push notifications (optional, free).** Install the [ntfy app](https://ntfy.sh) and subscribe to a hard-to-guess topic name, such as `grad-tracker-7f3k9q`. Then add a repository secret called `NTFY_TOPIC` with that name. Secrets live under **Settings → Secrets and variables → Actions**.
- **Email (optional).** Add the secrets `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` and `EMAIL_TO`. For Gmail, use `smtp.gmail.com`, port `587` and an [app password](https://support.google.com/accounts/answer/185833).
- **RSS.** Point any feed reader at `docs/feed.xml`, or at the dashboard's `feed.xml` once the dashboard is on.

## The dashboard

The dashboard lets you filter roles and record your own progress on each one, from "Interested" through "Applied", "Interview" and "Offer". To switch it on:

1. Go to **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**. Pick this repository's default branch and the **/docs** folder, then save.
3. After a minute it is live at <https://keerthanvemulapati.github.io/Grad-scheme-applications/>.

Your statuses and notes are saved in your browser. Use **Export backup** on the "My applications" tab to copy them to another device.

## Adding a company

Open any of the company's job adverts and look at the web address. Then add an entry to [`config/companies.yaml`](config/companies.yaml). The comments at the top of that file show the format for each job-board platform, and Workday (`myworkdayjobs.com`) is the most common. Commit the change and the tracker runs straight away. The "Job board status" table below shows whether it worked.

If you can't tell which platform a company uses, run the **Probe job boards** workflow from the Actions tab. It inspects every careers page and reports what it finds.

## Running it yourself

```bash
pip install -r requirements-dev.txt
python -m tracker run --no-notify     # check every board and update the files
python -m tracker run --only gsk,medpace --dry-run
python -m tracker render              # rebuild README and dashboard from saved data
python -m pytest -q                   # tests
```

You can also start a run from **Actions → Check for new roles → Run workflow**.

---

## Current openings

This section is rewritten automatically on every run.

<!-- TRACKER:START -->
_Waiting for the first run._
<!-- TRACKER:END -->
