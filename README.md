# Automated Job Alert — disabledperson.com

A Python script that scrapes [disabledperson.com](https://www.disabledperson.com/jobs) daily for data-related job listings and sends a formatted email digest via SendGrid. Deployed on GitHub Actions — fully automated, zero manual effort after setup.

---

## How It Works

1. Searches disabledperson.com using keyword + location combinations
2. Filters results by job title relevance (include/exclude keyword lists)
3. Deduplicates against previously seen jobs to avoid repeat alerts
4. Sends a formatted HTML email via SendGrid if new jobs are found
5. Runs automatically every day at 9am CST via GitHub Actions

---

## Tech Stack

- **Python** — requests, BeautifulSoup, SendGrid SDK
- **SendGrid** — email delivery API
- **GitHub Actions** — scheduled daily automation (cron)

---

## Project Structure

```
job-alert/
├── .github/
│   └── workflows/
│       └── daily.yml       # GitHub Actions — runs daily at 9am CST
├── job_scraper.py          # Main script
├── requirements.txt        # Python dependencies
├── seen_jobs.json          # Tracks previously sent jobs (auto-updated)
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/JingYou-data/job-alert.git
cd job-alert
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory (never commit this):

```
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_SENDER=your_verified_sender@gmail.com
EMAIL_RECEIVER=your_inbox@gmail.com
```

- Get your SendGrid API key at [sendgrid.com](https://sendgrid.com) (free tier: 100 emails/day)
- Verify your sender email under **Settings → Sender Authentication**

### 4. Run locally

```bash
python job_scraper.py
```

---

## Deploy to GitHub Actions

### 1. Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add three secrets:

| Name | Value |
|------|-------|
| `SENDGRID_API_KEY` | Your SendGrid API key |
| `EMAIL_SENDER` | Your verified sender email |
| `EMAIL_RECEIVER` | Your recipient email |

### 2. Trigger manually to test

Go to **Actions → Daily Job Alert → Run workflow**

After a successful run, GitHub Actions will commit the updated `seen_jobs.json` back to the repo automatically.

---

## Customize

**Search terms** — edit `SEARCH_TERMS` in `job_scraper.py`:

```python
SEARCH_TERMS = [
    "data analytics",
    "data analysis",
    "data engineer",
]
```

**Locations** — edit `SEARCH_LOCATIONS`:

```python
SEARCH_LOCATIONS = [
    "Nashville, TN",
    "Seattle, WA",
    "remote",
]
```

**Keyword filters** — edit `INCLUDE_KEYWORDS` and `EXCLUDE_KEYWORDS` inside `filter_jobs()` to fine-tune relevance.

**Schedule** — edit the cron expression in `.github/workflows/daily.yml`:

```yaml
- cron: '0 14 * * *'   # 9am CST (UTC-5) = UTC 14:00
```

---

## Example Email

Subject: `[Job Alert] 3 new jobs on disabledperson.com — 2026-04-02`

Each job shows:
- Job title (linked to listing)
- Company name
- Search location used

---

## License

MIT
