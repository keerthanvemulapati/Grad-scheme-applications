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

**Last refreshed:** 24 Sep 2026, 09:31 UTC · **64 open roles** at 20 companies · [Open the dashboard](https://keerthanvemulapati.github.io/Grad-scheme-applications/)

| | Regulatory Affairs | Medical Affairs | Clinical Operations | Other areas |
|---|---|---|---|---|
| Graduate scheme | 1 | 0 | 0 | 6 |
| Entry level | 1 | 1 | 21 | 3 |
| Check seniority | 3 | 10 | 14 | 4 |

### New in the last 7 days (64)

| Company | Role | Area | Level | Location | Found |
|---|---|---|---|---|---|
| GSK | [Regulatory Affairs Graduate Programme, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK--London--New-Oxford-Street/Regulatory-Affairs-Graduate-Programme--UK--2027_448376) <sub>2027</sub> | Regulatory Affairs | Graduate scheme | UK – London – New Oxford Street | 24 Sep |
| AstraZeneca | [Clinical Research Associate](https://astrazeneca.wd3.myworkdayjobs.com/en-US/Careers/job/Field-UK/Clinical-Research-Associate_R-260336) | Clinical Operations | Entry level | Field-UK | 24 Sep |
| Fortrea | [Clinical Research Associate I](https://fortrea.wd1.myworkdayjobs.com/en-US/Fortrea/job/Maidenhead/Clinical-Research-Associate-I_251342) | Clinical Operations | Entry level | Maidenhead | 24 Sep |
| Fortrea | [Unblinded CRA I](https://fortrea.wd1.myworkdayjobs.com/en-US/Fortrea/job/Maidenhead/Unblinded-CRA-I_264861-1) | Clinical Operations | Entry level | Maidenhead | 24 Sep |
| ICON | [Patient Recruitment Associate I](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Warwickshire/Patient-Recruitment-Associate-I_JR156686-1) | Clinical Operations | Entry level | UK, Warwickshire | 24 Sep |
| ICON | [Clinical Site Associate](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Reading/Clinical-Site-Associate_JR156896) | Clinical Operations | Entry level | UK, Reading | 24 Sep |
| ICON | [Clinical Site Contracting Coordinator](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/Regional-Great-Britain-Northern-Ireland/Clinical-Site-Contracting-Coordinator_JR157722) | Clinical Operations | Entry level | Regional Great Britain (Northern Irelan… | 24 Sep |
| IQVIA | [Clinical Research Associate](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Reading-Berkshire-United-Kingdom/Clinical-Research-Associate---Ireland_R1514135) | Clinical Operations | Entry level | Reading, Berkshire, United Kingdom; Oxf… | 24 Sep |
| MSD | [Clinical Research Associate - North West England](https://msd.wd5.myworkdayjobs.com/en-US/SearchJobs/job/GBR---London---London-Moorgate-WeWork/Clinical-Research-Associate---North-West-England_R416129) | Clinical Operations | Entry level | GBR - London - London (Moorgate WeWork) | 24 Sep |
| MSD | [Clinical Research Associate (CRA)](https://msd.wd5.myworkdayjobs.com/en-US/SearchJobs/job/AUS---New-South-Wales---Macquarie-Park/Clinical-Research-Associate--CRA-_R417178-1) | Clinical Operations | Entry level | AUS - New South Wales - Macquarie Park | 24 Sep |
| Novartis | [Project Coordinator - Global Clinical Operations](https://novartis.wd3.myworkdayjobs.com/en-US/Novartis_Careers/job/London-The-Westworks/Project-Coordinator---Global-Clinical-Operations_REQ-10087071-1) | Clinical Operations | Entry level | London (The Westworks) | 24 Sep |
| Regeneron | [Medical Specialist I-Allergy/ENT-Seattle, Tacoma, WA & Anchorage, AK](https://regeneron.wd1.myworkdayjobs.com/en-US/Careers/job/Remote---United-States/Medical-Specialist-I-Allergy-ENT-Seattle--Tacoma--WA---Anchorage--AK_R50509) <sub>location unclear</sub> | Medical Affairs | Entry level | Remote - United States; Seattle, WA; An… | 24 Sep |
| Thermo Fisher (PPD) | [Clinical Research Associate (CRA) - All Levels](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Turkey/Clinical-Research-Associate--CRA----All-Levels_R-01340398) <sub>location unclear</sub> | Clinical Operations | Entry level | Remote, Turkey | 24 Sep |
| Thermo Fisher (PPD) | [FSP Clinical Trial Coordinator I](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/FSP-Clinical-Trial-Coordinator-I_R-01362164) <sub>location unclear</sub> | Clinical Operations | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [FSP Regulatory Affairs Specialist - CMC Compliance Officer client dedicated](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Belgium/FSP-Regulatory-Affairs-Specialist---CMC-Compliance-Officer-client-dedicated_R-01364066) <sub>location unclear</sub> | Regulatory Affairs | Entry level | Remote, Belgium | 24 Sep |
| Thermo Fisher (PPD) | [Travel Clinical Research Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Minnesota-USA/Travel-Clinical-Research-Coordinator_R-01364928-1) <sub>location unclear</sub> | Clinical Operations | Entry level | Remote, Minnesota, USA | 24 Sep |
| Thermo Fisher (PPD) | [FSP Trial Delivery Specialist - Clinical Trial Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Mexico/FSP-Trial-Delivery-Specialist---Clinical-Trial-Coordinator_R-01366912) <sub>location unclear</sub> | Clinical Operations | Entry level | Remote, Mexico; Remote, Brazil; Remote,… | 24 Sep |
| Thermo Fisher (PPD) | [FSP Clinical Trial Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Serbia/FSP-Clinical-Trial-Coordinator_R-01368834) <sub>location unclear</sub> | Clinical Operations | Entry level | Remote, Serbia | 24 Sep |
| Thermo Fisher (PPD) | [DO NOT APPLY - TEST REQ - CRG - (DO NOT USE) CRA (Level I) - Budapest Hungary](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Hungary/DO-NOT-APPLY---TEST-REQ---CRG----DO-NOT-USE--CRA--Level-I----Budapest-Hungary_R-01369212) <sub>location unclear</sub> | Clinical Operations | Entry level | Remote, Hungary | 24 Sep |
| Worldwide Clinical Trials | [Clinical Trials Associate - UK or Serbia - Remote](https://worldwide.wd1.myworkdayjobs.com/en-US/External/job/Belgrade-Serbia/Clinical-Trials-Associate---UK-or-Serbia---Remote_JR102731-1) | Clinical Operations | Entry level | Belgrade, Serbia; England, United Kingd… | 24 Sep |
| Thermo Fisher (PPD) | [Assistant CRA](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-United-Kingdom/Assistant-CRA_R-01339167) | Clinical Operations | Entry level | Remote, United Kingdom | 24 Sep |
| Thermo Fisher (PPD) | [Clinical Trial Coordinator - Glasgow](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Bellshill-United-Kingdom/Clinical-Trial-Coordinator---Glasgow_R-01348797) | Clinical Operations | Entry level | Bellshill, United Kingdom | 24 Sep |
| Amgen | [Product Owner - Clinical Trial Supplier Enablement](https://amgen.wd1.myworkdayjobs.com/en-US/Careers/job/United-Kingdom---Cambridge/Product-Owner---Clinical-Trial-Supplier-Enablement_R-251395-1) | Clinical Operations | Check seniority | United Kingdom - Cambridge; United King… | 24 Sep |
| Amgen | [Snr Medical Science Liaison (Obesity)](https://amgen.wd1.myworkdayjobs.com/en-US/Careers/job/United-Kingdom---Cambridge/Snr-Medical-Science-Liaison--Obesity-_R-254067) | Medical Affairs | Check seniority | United Kingdom - Cambridge; United King… | 24 Sep |
| AstraZeneca | [Medical Science Liaison - Alexion](https://astrazeneca.wd3.myworkdayjobs.com/en-US/Careers/job/Field-UK/Medical-Science-Liaison---Alexion_R-260499) | Medical Affairs | Check seniority | Field-UK | 24 Sep |
| ICON | [CRA](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Reading/CRA_JR146722) | Clinical Operations | Check seniority | UK, Reading; UK, Livingston; UK, Swansea | 24 Sep |
| ICON | [Site Contract and Budget Specialist 4](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/Regional-Great-Britain-Northern-Ireland/Site-Contract-and-Budget-Specialist-4_JR159465) | Clinical Operations | Check seniority | Regional Great Britain (Northern Irelan… | 24 Sep |
| Ipsen | [Medical Science Liaison - Neuroscience](https://ipsen.wd103.myworkdayjobs.com/en-US/Ipsen_Careers/job/London-UK/Medical-Science-Liaison---Neuroscience_R-22038) | Medical Affairs | Check seniority | London (UK) | 24 Sep |
| IQVIA | [Experienced CRA - Single Sponsor Dedicated](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Reading-Berkshire-United-Kingdom/Experienced-CRA---Single-Sponsor-Dedicated_R1524544) | Clinical Operations | Check seniority | Reading, Berkshire, United Kingdom | 24 Sep |
| Moderna | [Field Medical Advisor, Oncology](https://modernatx.wd1.myworkdayjobs.com/en-US/M_tx/job/Remote---US/Field-Medical-Advisor--Oncology_R19547) <sub>location unclear</sub> | Medical Affairs | Check seniority | Remote - US; Medical Affairs | 24 Sep |
| Regeneron | [Clinical Study Specialist](https://regeneron.wd1.myworkdayjobs.com/en-US/Careers/job/Uxbridge1/Clinical-Study-Specialist_R50053) | Clinical Operations | Check seniority | Uxbridge1; Armonk; Warren | 24 Sep |
| Roche | [Clinical Development Leader](https://roche.wd3.myworkdayjobs.com/en-US/roche-ext/job/Indianapolis/Clinical-Development-Leader_202609-122666-1) | Clinical Operations | Check seniority | Indianapolis; Vienna; Sant Cugat del Va… | 24 Sep |
| Syneos Health | [CRA - Future Roles (UK)](https://syneoshealth.wd12.myworkdayjobs.com/en-US/Syneos_Health_External_Site/job/GBR-London-Hybrid/CRA---Future-Roles--UK-_25106983) | Clinical Operations | Check seniority | GBR-London-Hybrid | 24 Sep |
| Syneos Health | [CRA UK](https://syneoshealth.wd12.myworkdayjobs.com/en-US/Syneos_Health_External_Site/job/GBR-Remote/CRA-UK_25112022) | Clinical Operations | Check seniority | GBR-Remote | 24 Sep |
| Thermo Fisher (PPD) | [Trial Delivery Specialist/ Clinical Trial Coordination, FSP](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Poland/Clinical-Trial-Coordinator--FSP_R-01326868) <sub>location unclear</sub> | Clinical Operations | Check seniority | Remote, Poland; Remote, Bulgaria; Remot… | 24 Sep |
| Thermo Fisher (PPD) | [FSP Mananger Clinical Operations](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Mexico/FSP-Mananger-Clinical-Operations_R-01366921) <sub>location unclear</sub> | Clinical Operations | Check seniority | Remote, Mexico | 24 Sep |
| Astellas | [Medical Science Liaison, Lung](https://careers.astellas.com/job/Addlestone-Medical-Science-Liaison%2C-Lung-KT15-2NX/1430935400/) | Medical Affairs | Check seniority | Addlestone, GB, KT15 2NX | 24 Sep |
| Johnson & Johnson | [Medical Affairs Specialist](https://jj.wd5.myworkdayjobs.com/en-US/JJ/job/Brussels-Brussels-Capital-Region-Belgium/Medical-Affairs-Specialist_R-018387) | Medical Affairs | Check seniority | Brussels, Brussels-Capital Region, Belg… | 24 Sep |
| PSI CRO | [Clinical Trial Liaison (Oncology)](https://jobs.smartrecruiters.com/PSICRO/744000149413559) <sub>location unclear</sub> | Clinical Operations | Check seniority | Remote, REMOTE, United States | 24 Sep |
| Roche | [Country Study Start-Up Team Leader (cSTL)](https://roche.wd3.myworkdayjobs.com/en-US/roche-ext/job/Welwyn/Country-Study-Start-Up-Team-Leader--cSTL-_202603-107122-1) | Clinical Operations | Check seniority | Welwyn | 24 Sep |
| Roche | [Regulatory Innovation & Sustainment Leader](https://roche.wd3.myworkdayjobs.com/en-US/roche-ext/job/Welwyn/Regulatory-Innovation---Sustainment-Leader_202608-121489-1) | Regulatory Affairs | Check seniority | Welwyn; South San Francisco; Mississaug… | 24 Sep |
| Takeda | [MSL Plasma-derived Therapies](https://jobs.takeda.com/job/zurich/msl-plasma-derived-therapies/1113/100074859664) <sub>location unclear</sub> | Medical Affairs | Check seniority | Remote | 24 Sep |
| Takeda | [Medical Science Liaison, Rare Diseases](https://jobs.takeda.com/job/toronto/medical-science-liaison-rare-diseases/1113/100102263232) <sub>location unclear</sub> | Medical Affairs | Check seniority | Remote | 24 Sep |
| Takeda | [Medical Science Liaison, Dermatology (Central)](https://jobs.takeda.com/job/toronto/medical-science-liaison-dermatology-central/1113/90773933056) <sub>location unclear</sub> | Medical Affairs | Check seniority | Remote | 24 Sep |
| Takeda | [MSL, Medical Engagement, Japan Medical Office, JPBU / JPBU ジャパンメディカルオフィス メディカルエンゲージメント メデ…](https://jobs.takeda.com/job/tokyo/msl-medical-engagement-japan-medical-office-jpbu-jpbu-%e3%82%b7%e3%83%a3%e3%83%8f%e3%83%b3%e3%83%a1%e3%83%86%e3%82%a3%e3%82%ab%e3%83%ab%e3%82%aa%e3%83%95%e3%82%a3%e3%82%b9-%e3%83%a1%e3%83%86%e3%82%a3%e3%82%ab%e3%83%ab%e3%82%a8%e3%83%b3%e3%82%b1%e3%83%bc%e3%82%b7%e3%83%a1%e3%83%b3%e3%83%88-%e3%83%a1%e3%83%86%e3%82%a3%e3%82%ab%e3%83%ab%e3%82%b5%e3%82%a4%e3%82%a8%e3%83%b3%e3%82%b9%e3%83%aa%e3%82%a8%e3%82%bd%e3%83%b3-ms/1113/98699480816) <sub>location unclear</sub> | Medical Affairs | Check seniority | Multiple Locations | 24 Sep |
| ICON | [Clinical Research Associate](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Reading/CRA2---sponsor-dedicated_JR157317) <sub>asks for experience</sub> | Clinical Operations | Entry level | UK, Reading | 24 Sep |
| ICON | [Clinical Research Associate](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Livingston/Clinical-Research-Associate_JR157570) <sub>asks for experience</sub> | Clinical Operations | Entry level | UK, Livingston | 24 Sep |
| Haleon | [REGISTER YOUR INTEREST: Early Talent UK Opportunities, 2027](https://gsknch.wd3.myworkdayjobs.com/en-US/GSKCareers/job/UK---London/REGISTER-YOUR-INTEREST--Early-Talent-UK-Opportunities--2027_540127) <sub>2027, register interest</sub> | Other Graduate Scheme | Graduate scheme | UK - London | 24 Sep |
| GSK | [Communications and Government Affairs Graduate Programme, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK--London--New-Oxford-Street/Communications-and-Government-Affairs-Graduate-Programme--UK--2027_448163) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | UK – London – New Oxford Street | 24 Sep |
| GSK | [Quality Science Graduate Programme – Barnard Castle, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK---County-Durham---Barnard-Castle/Quality-Science-Graduate-Programme---Barnard-Castle--UK--2027_448225) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | UK - County Durham - Barnard Castle | 24 Sep |
| GSK | [Quality Science Graduate Programme – Ware, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK---Hertfordshire---Ware/Quality-Science-Graduate-Programme---Ware--UK--2027_448227) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | UK - Hertfordshire - Ware | 24 Sep |
| Johnson & Johnson | [Research & Development Leadership Development Program (RDLDP)- Full-Time Class of 2027](https://jj.wd5.myworkdayjobs.com/en-US/JJ/job/Santa-Clara-California-United-States-of-America/Research---Development-Leadership-Development-Program--RDLDP---Full-Time-Class-of-2027_R-096443) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | Santa Clara, California, United States… | 24 Sep |
| Johnson & Johnson | [2027 MedTech Marketing Leadership Development Program (MLDP)- Full-Time](https://jj.wd5.myworkdayjobs.com/en-US/JJ/job/Raritan-New-Jersey-United-States-of-America/XMLNAME-2027-MedTech-Marketing-Leadership-Development-Program--MLDP---Full-Time_R-100842) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | Raritan, New Jersey, United States of A… | 24 Sep |
| Fortrea | [Site Start-Up Specialist](https://fortrea.wd1.myworkdayjobs.com/en-US/Fortrea/job/Maidenhead/Site-Start-Up-Specialist_251030) <sub>asks for experience</sub> | Clinical Operations | Check seniority | Maidenhead; Warsaw; Dublin | 24 Sep |
| IQVIA | [Clinical Independent Rater for Clinical Trial - Polish Speaking](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Warsaw-Poland/Clinical-Independent-Rater---Polish-Speaking_R1565158) <sub>asks for experience</sub> | Clinical Operations | Check seniority | Warsaw, Poland; Noumea, France; Taucha,… | 24 Sep |
| IQVIA | [Freelance Site Activation Specialist (Study Start-Up / Regulatory Submissions) – UK Remote](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/London-United-Kingdom/Freelance-Site-Activation-Specialist--Study-Start-Up---Regulatory-Submissions----UK-Remote_R1565336) <sub>asks for experience</sub> | Regulatory Affairs | Check seniority | London, United Kingdom; Edinburgh, Scot… | 24 Sep |
| Thermo Fisher (PPD) | [FSP Regulatory Affairs Principle Specialist - Regulatory Liaison client dedicated](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Belgium/FSP-Regulatory-Affairs-Principle-Specialist---Regulatory-Liaison-client-dedicated_R-01361506) <sub>asks for experience, location unclear</sub> | Regulatory Affairs | Check seniority | Remote, Belgium | 24 Sep |
| Thermo Fisher (PPD) | [FSP Pharmacovigilance Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/FSP-Pharmacovigilance-Coordinator_R-01362190) <sub>location unclear</sub> | Drug Safety / PV | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [Drug Safety Reporting Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/Drug-Safety-Reporting-Coordinator_R-01364421) <sub>location unclear</sub> | Drug Safety / PV | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [FSP Pharmacovigilance Coordinator (Night Shift)](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/FSP-Pharmacovigilance-Coordinator_R-01369299) <sub>location unclear</sub> | Drug Safety / PV | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [Drug Safety Specialist (FSP) - Day Shift](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/Drug-Safety-Specialist--FSP----Day-Shift_R-01361157) <sub>location unclear</sub> | Drug Safety / PV | Check seniority | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [Drug Safety Specialist (Night Shift)](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/Drug-Safety-Specialist--Night-Shift-_R-01366361) <sub>location unclear</sub> | Drug Safety / PV | Check seniority | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [Qualified Person - PV, EU](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Bulgaria/Qualified-Person---PV--EMEA_R-01366514) <sub>location unclear</sub> | Drug Safety / PV | Check seniority | Remote, Bulgaria; Remote, Romania; Remo… | 24 Sep |
| Worldwide Clinical Trials | [Pharmacovigilance Specialist - US - Remote](https://worldwide.wd1.myworkdayjobs.com/en-US/External/job/Durham-North-Carolina/Pharmacovigilance-Specialist---US---Remote_JR102334) | Drug Safety / PV | Check seniority | Durham, North Carolina; Brasilia, Brazi… | 24 Sep |

### Regulatory Affairs (5)

| Company | Role | Level | Location | Found |
|---|---|---|---|---|
| GSK | [Regulatory Affairs Graduate Programme, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK--London--New-Oxford-Street/Regulatory-Affairs-Graduate-Programme--UK--2027_448376) <sub>2027</sub> | Graduate scheme | UK – London – New Oxford Street | 24 Sep |
| Thermo Fisher (PPD) | [FSP Regulatory Affairs Specialist - CMC Compliance Officer client dedicated](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Belgium/FSP-Regulatory-Affairs-Specialist---CMC-Compliance-Officer-client-dedicated_R-01364066) <sub>location unclear</sub> | Entry level | Remote, Belgium | 24 Sep |
| Roche | [Regulatory Innovation & Sustainment Leader](https://roche.wd3.myworkdayjobs.com/en-US/roche-ext/job/Welwyn/Regulatory-Innovation---Sustainment-Leader_202608-121489-1) | Check seniority | Welwyn; South San Francisco; Mississaug… | 24 Sep |
| IQVIA | [Freelance Site Activation Specialist (Study Start-Up / Regulatory Submissions) – UK Remote](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/London-United-Kingdom/Freelance-Site-Activation-Specialist--Study-Start-Up---Regulatory-Submissions----UK-Remote_R1565336) <sub>asks for experience</sub> | Check seniority | London, United Kingdom; Edinburgh, Scot… | 24 Sep |
| Thermo Fisher (PPD) | [FSP Regulatory Affairs Principle Specialist - Regulatory Liaison client dedicated](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Belgium/FSP-Regulatory-Affairs-Principle-Specialist---Regulatory-Liaison-client-dedicated_R-01361506) <sub>asks for experience, location unclear</sub> | Check seniority | Remote, Belgium | 24 Sep |

### Medical Affairs (11)

| Company | Role | Level | Location | Found |
|---|---|---|---|---|
| Regeneron | [Medical Specialist I-Allergy/ENT-Seattle, Tacoma, WA & Anchorage, AK](https://regeneron.wd1.myworkdayjobs.com/en-US/Careers/job/Remote---United-States/Medical-Specialist-I-Allergy-ENT-Seattle--Tacoma--WA---Anchorage--AK_R50509) <sub>location unclear</sub> | Entry level | Remote - United States; Seattle, WA; An… | 24 Sep |
| Amgen | [Snr Medical Science Liaison (Obesity)](https://amgen.wd1.myworkdayjobs.com/en-US/Careers/job/United-Kingdom---Cambridge/Snr-Medical-Science-Liaison--Obesity-_R-254067) | Check seniority | United Kingdom - Cambridge; United King… | 24 Sep |
| Astellas | [Medical Science Liaison, Lung](https://careers.astellas.com/job/Addlestone-Medical-Science-Liaison%2C-Lung-KT15-2NX/1430935400/) | Check seniority | Addlestone, GB, KT15 2NX | 24 Sep |
| AstraZeneca | [Medical Science Liaison - Alexion](https://astrazeneca.wd3.myworkdayjobs.com/en-US/Careers/job/Field-UK/Medical-Science-Liaison---Alexion_R-260499) | Check seniority | Field-UK | 24 Sep |
| Ipsen | [Medical Science Liaison - Neuroscience](https://ipsen.wd103.myworkdayjobs.com/en-US/Ipsen_Careers/job/London-UK/Medical-Science-Liaison---Neuroscience_R-22038) | Check seniority | London (UK) | 24 Sep |
| Johnson & Johnson | [Medical Affairs Specialist](https://jj.wd5.myworkdayjobs.com/en-US/JJ/job/Brussels-Brussels-Capital-Region-Belgium/Medical-Affairs-Specialist_R-018387) | Check seniority | Brussels, Brussels-Capital Region, Belg… | 24 Sep |
| Moderna | [Field Medical Advisor, Oncology](https://modernatx.wd1.myworkdayjobs.com/en-US/M_tx/job/Remote---US/Field-Medical-Advisor--Oncology_R19547) <sub>location unclear</sub> | Check seniority | Remote - US; Medical Affairs | 24 Sep |
| Takeda | [MSL Plasma-derived Therapies](https://jobs.takeda.com/job/zurich/msl-plasma-derived-therapies/1113/100074859664) <sub>location unclear</sub> | Check seniority | Remote | 24 Sep |
| Takeda | [MSL, Medical Engagement, Japan Medical Office, JPBU / JPBU ジャパンメディカルオフィス メディカルエンゲージメント メデ…](https://jobs.takeda.com/job/tokyo/msl-medical-engagement-japan-medical-office-jpbu-jpbu-%e3%82%b7%e3%83%a3%e3%83%8f%e3%83%b3%e3%83%a1%e3%83%86%e3%82%a3%e3%82%ab%e3%83%ab%e3%82%aa%e3%83%95%e3%82%a3%e3%82%b9-%e3%83%a1%e3%83%86%e3%82%a3%e3%82%ab%e3%83%ab%e3%82%a8%e3%83%b3%e3%82%b1%e3%83%bc%e3%82%b7%e3%83%a1%e3%83%b3%e3%83%88-%e3%83%a1%e3%83%86%e3%82%a3%e3%82%ab%e3%83%ab%e3%82%b5%e3%82%a4%e3%82%a8%e3%83%b3%e3%82%b9%e3%83%aa%e3%82%a8%e3%82%bd%e3%83%b3-ms/1113/98699480816) <sub>location unclear</sub> | Check seniority | Multiple Locations | 24 Sep |
| Takeda | [Medical Science Liaison, Dermatology (Central)](https://jobs.takeda.com/job/toronto/medical-science-liaison-dermatology-central/1113/90773933056) <sub>location unclear</sub> | Check seniority | Remote | 24 Sep |
| Takeda | [Medical Science Liaison, Rare Diseases](https://jobs.takeda.com/job/toronto/medical-science-liaison-rare-diseases/1113/100102263232) <sub>location unclear</sub> | Check seniority | Remote | 24 Sep |

### Clinical Operations (35)

| Company | Role | Level | Location | Found |
|---|---|---|---|---|
| AstraZeneca | [Clinical Research Associate](https://astrazeneca.wd3.myworkdayjobs.com/en-US/Careers/job/Field-UK/Clinical-Research-Associate_R-260336) | Entry level | Field-UK | 24 Sep |
| Fortrea | [Clinical Research Associate I](https://fortrea.wd1.myworkdayjobs.com/en-US/Fortrea/job/Maidenhead/Clinical-Research-Associate-I_251342) | Entry level | Maidenhead | 24 Sep |
| Fortrea | [Unblinded CRA I](https://fortrea.wd1.myworkdayjobs.com/en-US/Fortrea/job/Maidenhead/Unblinded-CRA-I_264861-1) | Entry level | Maidenhead | 24 Sep |
| ICON | [Clinical Site Associate](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Reading/Clinical-Site-Associate_JR156896) | Entry level | UK, Reading | 24 Sep |
| ICON | [Clinical Site Contracting Coordinator](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/Regional-Great-Britain-Northern-Ireland/Clinical-Site-Contracting-Coordinator_JR157722) | Entry level | Regional Great Britain (Northern Irelan… | 24 Sep |
| ICON | [Patient Recruitment Associate I](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Warwickshire/Patient-Recruitment-Associate-I_JR156686-1) | Entry level | UK, Warwickshire | 24 Sep |
| IQVIA | [Clinical Research Associate](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Reading-Berkshire-United-Kingdom/Clinical-Research-Associate---Ireland_R1514135) | Entry level | Reading, Berkshire, United Kingdom; Oxf… | 24 Sep |
| MSD | [Clinical Research Associate (CRA)](https://msd.wd5.myworkdayjobs.com/en-US/SearchJobs/job/AUS---New-South-Wales---Macquarie-Park/Clinical-Research-Associate--CRA-_R417178-1) | Entry level | AUS - New South Wales - Macquarie Park | 24 Sep |
| MSD | [Clinical Research Associate - North West England](https://msd.wd5.myworkdayjobs.com/en-US/SearchJobs/job/GBR---London---London-Moorgate-WeWork/Clinical-Research-Associate---North-West-England_R416129) | Entry level | GBR - London - London (Moorgate WeWork) | 24 Sep |
| Novartis | [Project Coordinator - Global Clinical Operations](https://novartis.wd3.myworkdayjobs.com/en-US/Novartis_Careers/job/London-The-Westworks/Project-Coordinator---Global-Clinical-Operations_REQ-10087071-1) | Entry level | London (The Westworks) | 24 Sep |
| Thermo Fisher (PPD) | [Assistant CRA](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-United-Kingdom/Assistant-CRA_R-01339167) | Entry level | Remote, United Kingdom | 24 Sep |
| Thermo Fisher (PPD) | [Clinical Research Associate (CRA) - All Levels](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Turkey/Clinical-Research-Associate--CRA----All-Levels_R-01340398) <sub>location unclear</sub> | Entry level | Remote, Turkey | 24 Sep |
| Thermo Fisher (PPD) | [Clinical Trial Coordinator - Glasgow](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Bellshill-United-Kingdom/Clinical-Trial-Coordinator---Glasgow_R-01348797) | Entry level | Bellshill, United Kingdom | 24 Sep |
| Thermo Fisher (PPD) | [DO NOT APPLY - TEST REQ - CRG - (DO NOT USE) CRA (Level I) - Budapest Hungary](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Hungary/DO-NOT-APPLY---TEST-REQ---CRG----DO-NOT-USE--CRA--Level-I----Budapest-Hungary_R-01369212) <sub>location unclear</sub> | Entry level | Remote, Hungary | 24 Sep |
| Thermo Fisher (PPD) | [FSP Clinical Trial Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Serbia/FSP-Clinical-Trial-Coordinator_R-01368834) <sub>location unclear</sub> | Entry level | Remote, Serbia | 24 Sep |
| Thermo Fisher (PPD) | [FSP Clinical Trial Coordinator I](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/FSP-Clinical-Trial-Coordinator-I_R-01362164) <sub>location unclear</sub> | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [FSP Trial Delivery Specialist - Clinical Trial Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Mexico/FSP-Trial-Delivery-Specialist---Clinical-Trial-Coordinator_R-01366912) <sub>location unclear</sub> | Entry level | Remote, Mexico; Remote, Brazil; Remote,… | 24 Sep |
| Thermo Fisher (PPD) | [Travel Clinical Research Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Minnesota-USA/Travel-Clinical-Research-Coordinator_R-01364928-1) <sub>location unclear</sub> | Entry level | Remote, Minnesota, USA | 24 Sep |
| Worldwide Clinical Trials | [Clinical Trials Associate - UK or Serbia - Remote](https://worldwide.wd1.myworkdayjobs.com/en-US/External/job/Belgrade-Serbia/Clinical-Trials-Associate---UK-or-Serbia---Remote_JR102731-1) | Entry level | Belgrade, Serbia; England, United Kingd… | 24 Sep |
| Amgen | [Product Owner - Clinical Trial Supplier Enablement](https://amgen.wd1.myworkdayjobs.com/en-US/Careers/job/United-Kingdom---Cambridge/Product-Owner---Clinical-Trial-Supplier-Enablement_R-251395-1) | Check seniority | United Kingdom - Cambridge; United King… | 24 Sep |
| ICON | [CRA](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Reading/CRA_JR146722) | Check seniority | UK, Reading; UK, Livingston; UK, Swansea | 24 Sep |
| ICON | [Site Contract and Budget Specialist 4](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/Regional-Great-Britain-Northern-Ireland/Site-Contract-and-Budget-Specialist-4_JR159465) | Check seniority | Regional Great Britain (Northern Irelan… | 24 Sep |
| IQVIA | [Experienced CRA - Single Sponsor Dedicated](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Reading-Berkshire-United-Kingdom/Experienced-CRA---Single-Sponsor-Dedicated_R1524544) | Check seniority | Reading, Berkshire, United Kingdom | 24 Sep |
| PSI CRO | [Clinical Trial Liaison (Oncology)](https://jobs.smartrecruiters.com/PSICRO/744000149413559) <sub>location unclear</sub> | Check seniority | Remote, REMOTE, United States | 24 Sep |
| Regeneron | [Clinical Study Specialist](https://regeneron.wd1.myworkdayjobs.com/en-US/Careers/job/Uxbridge1/Clinical-Study-Specialist_R50053) | Check seniority | Uxbridge1; Armonk; Warren | 24 Sep |
| Roche | [Clinical Development Leader](https://roche.wd3.myworkdayjobs.com/en-US/roche-ext/job/Indianapolis/Clinical-Development-Leader_202609-122666-1) | Check seniority | Indianapolis; Vienna; Sant Cugat del Va… | 24 Sep |
| Roche | [Country Study Start-Up Team Leader (cSTL)](https://roche.wd3.myworkdayjobs.com/en-US/roche-ext/job/Welwyn/Country-Study-Start-Up-Team-Leader--cSTL-_202603-107122-1) | Check seniority | Welwyn | 24 Sep |
| Syneos Health | [CRA - Future Roles (UK)](https://syneoshealth.wd12.myworkdayjobs.com/en-US/Syneos_Health_External_Site/job/GBR-London-Hybrid/CRA---Future-Roles--UK-_25106983) | Check seniority | GBR-London-Hybrid | 24 Sep |
| Syneos Health | [CRA UK](https://syneoshealth.wd12.myworkdayjobs.com/en-US/Syneos_Health_External_Site/job/GBR-Remote/CRA-UK_25112022) | Check seniority | GBR-Remote | 24 Sep |
| Thermo Fisher (PPD) | [FSP Mananger Clinical Operations](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Mexico/FSP-Mananger-Clinical-Operations_R-01366921) <sub>location unclear</sub> | Check seniority | Remote, Mexico | 24 Sep |
| Thermo Fisher (PPD) | [Trial Delivery Specialist/ Clinical Trial Coordination, FSP](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Poland/Clinical-Trial-Coordinator--FSP_R-01326868) <sub>location unclear</sub> | Check seniority | Remote, Poland; Remote, Bulgaria; Remot… | 24 Sep |
| ICON | [Clinical Research Associate](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Reading/CRA2---sponsor-dedicated_JR157317) <sub>asks for experience</sub> | Entry level | UK, Reading | 24 Sep |
| ICON | [Clinical Research Associate](https://icon.wd3.myworkdayjobs.com/en-US/broadbean_external/job/UK-Livingston/Clinical-Research-Associate_JR157570) <sub>asks for experience</sub> | Entry level | UK, Livingston | 24 Sep |
| Fortrea | [Site Start-Up Specialist](https://fortrea.wd1.myworkdayjobs.com/en-US/Fortrea/job/Maidenhead/Site-Start-Up-Specialist_251030) <sub>asks for experience</sub> | Check seniority | Maidenhead; Warsaw; Dublin | 24 Sep |
| IQVIA | [Clinical Independent Rater for Clinical Trial - Polish Speaking](https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Warsaw-Poland/Clinical-Independent-Rater---Polish-Speaking_R1565158) <sub>asks for experience</sub> | Check seniority | Warsaw, Poland; Noumea, France; Taucha,… | 24 Sep |

### Other roles worth a look (13)

<details><summary>Drug safety, clinical data, medical writing and other graduate schemes</summary>

| Company | Role | Area | Level | Location | Found |
|---|---|---|---|---|---|
| Haleon | [REGISTER YOUR INTEREST: Early Talent UK Opportunities, 2027](https://gsknch.wd3.myworkdayjobs.com/en-US/GSKCareers/job/UK---London/REGISTER-YOUR-INTEREST--Early-Talent-UK-Opportunities--2027_540127) <sub>2027, register interest</sub> | Other Graduate Scheme | Graduate scheme | UK - London | 24 Sep |
| GSK | [Communications and Government Affairs Graduate Programme, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK--London--New-Oxford-Street/Communications-and-Government-Affairs-Graduate-Programme--UK--2027_448163) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | UK – London – New Oxford Street | 24 Sep |
| GSK | [Quality Science Graduate Programme – Barnard Castle, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK---County-Durham---Barnard-Castle/Quality-Science-Graduate-Programme---Barnard-Castle--UK--2027_448225) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | UK - County Durham - Barnard Castle | 24 Sep |
| GSK | [Quality Science Graduate Programme – Ware, UK, 2027](https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers/job/UK---Hertfordshire---Ware/Quality-Science-Graduate-Programme---Ware--UK--2027_448227) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | UK - Hertfordshire - Ware | 24 Sep |
| Johnson & Johnson | [2027 MedTech Marketing Leadership Development Program (MLDP)- Full-Time](https://jj.wd5.myworkdayjobs.com/en-US/JJ/job/Raritan-New-Jersey-United-States-of-America/XMLNAME-2027-MedTech-Marketing-Leadership-Development-Program--MLDP---Full-Time_R-100842) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | Raritan, New Jersey, United States of A… | 24 Sep |
| Johnson & Johnson | [Research & Development Leadership Development Program (RDLDP)- Full-Time Class of 2027](https://jj.wd5.myworkdayjobs.com/en-US/JJ/job/Santa-Clara-California-United-States-of-America/Research---Development-Leadership-Development-Program--RDLDP---Full-Time-Class-of-2027_R-096443) <sub>2027</sub> | Other Graduate Scheme | Graduate scheme | Santa Clara, California, United States… | 24 Sep |
| Thermo Fisher (PPD) | [Drug Safety Reporting Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/Drug-Safety-Reporting-Coordinator_R-01364421) <sub>location unclear</sub> | Drug Safety / PV | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [FSP Pharmacovigilance Coordinator](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/FSP-Pharmacovigilance-Coordinator_R-01362190) <sub>location unclear</sub> | Drug Safety / PV | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [FSP Pharmacovigilance Coordinator (Night Shift)](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/FSP-Pharmacovigilance-Coordinator_R-01369299) <sub>location unclear</sub> | Drug Safety / PV | Entry level | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [Drug Safety Specialist (FSP) - Day Shift](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/Drug-Safety-Specialist--FSP----Day-Shift_R-01361157) <sub>location unclear</sub> | Drug Safety / PV | Check seniority | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [Drug Safety Specialist (Night Shift)](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Philippines/Drug-Safety-Specialist--Night-Shift-_R-01366361) <sub>location unclear</sub> | Drug Safety / PV | Check seniority | Remote, Philippines | 24 Sep |
| Thermo Fisher (PPD) | [Qualified Person - PV, EU](https://thermofisher.wd5.myworkdayjobs.com/en-US/ThermoFisherCareers/job/Remote-Bulgaria/Qualified-Person---PV--EMEA_R-01366514) <sub>location unclear</sub> | Drug Safety / PV | Check seniority | Remote, Bulgaria; Remote, Romania; Remo… | 24 Sep |
| Worldwide Clinical Trials | [Pharmacovigilance Specialist - US - Remote](https://worldwide.wd1.myworkdayjobs.com/en-US/External/job/Durham-North-Carolina/Pharmacovigilance-Specialist---US---Remote_JR102334) | Drug Safety / PV | Check seniority | Durham, North Carolina; Brasilia, Brazi… | 24 Sep |

</details>

### Programmes to watch

Schemes that open at set times of year or are advertised outside the job boards above. Check these by hand.

| Company | Programme | Area | Notes |
|---|---|---|---|
| GSK | [Regulatory Affairs Graduate Programme (UK)](https://www.gsk.com/en-gb/careers/early-careers/graduate-programme/research-development/) | Regulatory Affairs | A "Regulatory Affairs Graduate Programme, UK, 2027" advert (London, New Oxford Street) has been listed. Rotations across areas such as CMC, labelling and the UK & Ireland business. |
| MSD | [Regulatory Affairs Graduate Programme 2027 (register interest)](https://higherin.com/jobs/43279/msd/register-your-interest-regulatory-affairs-graduate-programme-2027) | Regulatory Affairs | 24 months, two 12-month rotations (International Regulatory CMC and Regulatory Affairs UK), Moorgate, London. For students finishing their degree 2025–2027. |
| MSD | [Medical Affairs Graduate Programme 2027 (register interest)](https://higherin.com/jobs/43280/msd/register-your-interest-medical-affairs-graduate-programme-2027) | Medical Affairs | 24-month rotational programme in the UK Medical Affairs team. |
| AstraZeneca | [Medical Graduate Programme](https://careers.astrazeneca.com/medical-graduate-programme) | Medical Affairs | Medical affairs work in specific therapy areas. AstraZeneca posts graduate adverts on its separate "Emerging Talent" job board, which this tracker checks. |
| AstraZeneca | [R&D Graduate Programme](https://careers.astrazeneca.com/r-and-d-graduate-programme) | Other (R&D) | Two years, three eight-month placements across R&D. |
| Takeda UK | [Graduate Leadership Development Programme](https://www.takeda.com/en-gb/careers/graduate-internship-programmes/) | Medical Affairs / commercial | Rotations can include Medical Affairs and Market Access. |
| Novartis | [Regulatory Affairs Postgraduate Program UK](https://www.novartis.com/careers/career-search/job/details/req-10078714-regulatory-affairs-postgraduate-program-uk) | Regulatory Affairs | Two years from January 2027, London. Asks for an MSc, PhD or PharmD, so check eligibility. |
| Bristol Myers Squibb | [Graduate Regulatory Affairs Programme](https://www.grb.uk.com/graduate-jobs/bristol-myers-squibb-graduate-regulatory-affairs-programme-uxbridge-34553) | Regulatory Affairs | Uxbridge, hybrid. The listing found was for an earlier intake; watch for the 2027 advert. |
| Novo Nordisk | [Global Graduate Programme](https://www.novonordisk.com/careers/early-career-programmes/graduate.html) | Various | Novo Nordisk's site says applications open 6 December 2026 and close 5 January 2027. |
| Medpace | [Entry Level Clinical Research Associate (PACE training)](https://www.medpace.com/careers/) | Clinical Operations | London office-based at first, with Medpace's CRA training programme. Also checked automatically. |
| Hammersmith Medicines Research | [Careers and apprenticeships](https://www.hmrlondon.com/careers) | Clinical Operations | Early-phase unit in London. Offers a Clinical Trials Specialist apprenticeship with the University of Kent. Its site blocks automated checks, so look at it by hand every week or two. |
| Parexel | [APEX Clinical Research Associate training programme](https://jobs.parexel.com/en/APEX-CRA-Program) | Clinical Operations | Six months of CRA training for recent life-science graduates, then a CRA I role. The UK intake needs the right to work in the UK without sponsorship. Parexel's early-careers page is https://jobs.parexel.com/en/emerging-talent. |
| Cencora PharmaLex | [Trainee, Regulatory Affairs](https://careers.cencora.com/us/en/united-kingdom-jobs) | Regulatory Affairs | Regulatory consultancy that hires trainees; its job board is checked automatically. |

**Other places to look:** [Bright Network pharma deadlines](https://www.brightnetwork.co.uk/application-deadlines/jobs/graduate-schemes/pharmaceuticals-science/) · [TARGETjobs medical & healthcare](https://targetjobs.co.uk/graduate-jobs/medical-healthcare) · [Prospects science graduate schemes](https://www.prospects.ac.uk/jobs-and-work-experience/job-sectors/science-and-pharmaceuticals/science-graduate-schemes/) · [TOPRA regulatory apprenticeships](https://www.topra.org/TOPRA/TOPRA_Member/Apprenticeships_in_Regulatory_Affairs.aspx)

### Job board status

<details><summary>40 of 42 job boards read successfully on the last run</summary>

| Company | Board | Status | Jobs read | Matches | Notes |
|---|---|---|---|---|---|
| Eli Lilly | workday | Failing (2x) | 0 | 0 | HTTPError: 422 Client Error: Unprocessable Entity for url: https://lilly.wd5.my… |
| Medpace | icims | Failing (1x) | 0 | 0 | No jobs found on the iCIMS portal |
| AbbVie | pagewatch | OK | 10 | 0 |  |
| Amgen | workday | OK | 13 | 2 | filtered by location (country) |
| Astellas | successfactors | OK | 8 | 1 | country filter |
| AstraZeneca | workday | OK | 80 | 2 | filtered by location (11 offices) |
| AstraZeneca | workday | OK | 18 | 0 | filtered by location (4 offices) |
| Bayer | eightfold | OK | 400 | 0 |  |
| BeOne Medicines | workday | OK | 4 | 0 | filtered by location (country) |
| Biogen | workday | OK | 1 | 0 | filtered by location (country) |
| Boehringer Ingelheim | successfactors | OK | 188 | 0 | location search |
| Bristol Myers Squibb | workday | OK | 29 | 0 | filtered by location (region) |
| Cencora PharmaLex | workday | OK | 109 | 0 | filtered by location (country) |
| CSL (incl. CSL Seqirus) | workday | OK | 27 | 0 | filtered by location (country) |
| Daiichi Sankyo | successfactors_csb | OK | 54 | 0 |  |
| Fortrea | workday | OK | 44 | 3 | filtered by location (country) |
| Gilead | workday | OK | 21 | 0 | filtered by location (4 offices) |
| GSK | workday | OK | 101 | 4 | filtered by location (country) |
| Haleon | workday | OK | 33 | 1 | filtered by location (country) |
| ICON | workday | OK | 105 | 7 | filtered by location (country) |
| Ipsen | workday | OK | 70 | 1 | filtered by location (country) |
| IQVIA | workday | OK | 249 | 4 | filtered by location (country) |
| Johnson & Johnson | workday | OK | 153 | 3 | filtered by location (13 offices) |
| Labcorp | workday | OK | 32 | 0 | filtered by location (12 offices) |
| MAC Clinical Research | pagewatch | OK | 20 | 0 |  |
| Moderna | workday | OK | 157 | 1 | keyword search (board has no country filter) |
| MSD | workday | OK | 146 | 2 | filtered by location (9 offices) |
| Novartis | workday | OK | 30 | 1 | filtered by location (country) |
| Novo Nordisk | successfactors | OK | 3 | 0 | country filter |
| Parexel | workday | OK | 35 | 0 | filtered by location (country) |
| Pfizer | workday | OK | 10 | 0 | filtered by location (country) |
| PSI CRO | smartrecruiters | OK | 217 | 1 |  |
| Regeneron | workday | OK | 27 | 0 | filtered by location (3 offices) |
| Richmond Pharmacology | pinpoint | OK | 4 | 0 |  |
| Roche | workday | OK | 36 | 3 | filtered by location (2 offices) |
| Sanofi | workday | OK | 3 | 0 | filtered by location (country) |
| Syneos Health | workday | OK | 55 | 2 | filtered by location (country) |
| Takeda | radancy | OK | 844 | 4 |  |
| Thermo Fisher (PPD) | workday | OK | 164 | 2 | filtered by location (27 offices) |
| UCB | phenom | OK | 50 | 0 |  |
| Vertex Pharmaceuticals | workday | OK | 10 | 0 | filtered by location (country) |
| Worldwide Clinical Trials | workday | OK | 33 | 2 | filtered by location (country) |

</details>

<!-- TRACKER:END -->
