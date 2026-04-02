import requests
from bs4 import BeautifulSoup
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import json
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────
SEARCH_TERMS = [
    "data analytics",
    "data analysis",
    "data engineer",
]

SEARCH_LOCATIONS = [
    "Nashville, TN",
    "Brentwood, TN",
    "Franklin, TN",
    "Seattle, WA",
    "Redmond, WA",
    "Bellevue, WA",
    "remote",
]

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
EMAIL_SENDER     = os.environ.get("EMAIL_SENDER")
EMAIL_RECEIVER   = os.environ.get("EMAIL_RECEIVER")

SEEN_FILE = "seen_jobs.json"
# ──────────────────────────────────────────────────────


def fetch_jobs():
    """Fetch jobs from disabledperson.com using keyword + location combinations."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    jobs = []
    seen_links = set()

    for term in SEARCH_TERMS:
        for location in SEARCH_LOCATIONS:
            page = 1
            while True:
                url = (
                    f"https://www.disabledperson.com/jobs"
                    f"?utf8=%E2%9C%93"
                    f"&term={term.replace(' ', '+')}"
                    f"&location={location.replace(' ', '+').replace(',', '%2C')}"
                    f"&page={page}"
                )
                print(f"[FETCH] {term} | {location} | page {page}")

                try:
                    resp = requests.get(url, headers=headers, timeout=15)
                    resp.raise_for_status()
                except requests.RequestException as e:
                    print(f"[ERROR] Request failed: {e}")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")

                job_links = soup.find_all(
                    "a",
                    href=lambda h: h and "/jobs/" in h
                        and "/locations/" not in h
                        and "/search" not in h
                        and "/categories/" not in h
                )

                if not job_links:
                    break

                new_found = 0
                for a in job_links:
                    link = a["href"]
                    if not link.startswith("http"):
                        link = "https://www.disabledperson.com" + link
                    if link in seen_links:
                        continue
                    seen_links.add(link)

                    title = a.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    parent = a.find_parent(["li", "div", "article"])
                    company = ""
                    if parent:
                        comp_el = parent.find(class_=lambda c: c and "company" in c.lower())
                        company = comp_el.get_text(strip=True) if comp_el else ""

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                    })
                    new_found += 1

                if new_found == 0:
                    break

                next_btn = soup.find("a", string=lambda s: s and "next" in s.lower())
                if not next_btn:
                    break
                page += 1
                if page > 5:
                    break

    print(f"[INFO] Total jobs fetched: {len(jobs)}")
    return jobs


def filter_jobs(jobs):
    """Filter jobs by relevance — must match an include keyword, must not match an exclude keyword."""
    INCLUDE_KEYWORDS = [
        "data analyst",
        "data analysis",
        "data engineer",
        "analytics engineer",
        "business intelligence",
        "bi analyst",
        "reporting analyst",
        "insights analyst",
        "marketing analyst",
        "data scientist",
        "data warehouse",
        "etl",
        "sql analyst",
    ]

    EXCLUDE_KEYWORDS = [
        "software engineer",
        "firmware",
        "devsecops",
        "front end",
        "frontend",
        "android",
        "ios",
        "devops",
        "cybersecurity",
        "network engineer",
        "mechanical",
        "electrical",
        "hardware",
        "nurse",
        "clinical",
        "job categories",
        "post jobs",
        "sales engineer",
        "middleware",
        "ai engineer",
    ]

    matched = []
    for job in jobs:
        title_lower = job["title"].lower()

        if any(ex in title_lower for ex in EXCLUDE_KEYWORDS):
            continue

        if any(kw in title_lower for kw in INCLUDE_KEYWORDS):
            matched.append(job)

    print(f"[INFO] Jobs after filtering: {len(matched)}")
    return matched


def load_seen():
    """Load previously seen job links to avoid duplicate alerts."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_links):
    """Save seen job links to disk."""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_links), f)


def send_email(new_jobs):
    """Send job alert email via SendGrid."""
    if not new_jobs:
        print("[INFO] No new jobs found — skipping email.")
        return

    today = date.today().strftime("%Y-%m-%d")
    subject = f"[Job Alert] {len(new_jobs)} new jobs on disabledperson.com — {today}"

    html_rows = ""
    for job in new_jobs:
        loc_part = f"&nbsp;·&nbsp;<span style='color:#888;font-size:13px;'>{job['location']}</span>" if job['location'] else ""
        html_rows += f"""
        <tr>
            <td style="padding:10px 8px;border-bottom:1px solid #eee;">
                <a href="{job['link']}" style="color:#1a56db;font-weight:600;text-decoration:none;">
                    {job['title']}
                </a><br>
                <span style="color:#555;font-size:13px;">{job['company']}</span>
                {loc_part}
            </td>
        </tr>"""

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;">
        <h2 style="color:#1a56db;">Job Alert — {today}</h2>
        <p style="color:#555;">Found <strong>{len(new_jobs)}</strong> new matching jobs on
            <a href="https://www.disabledperson.com/jobs">disabledperson.com</a>
        </p>
        <table width="100%" cellpadding="0" cellspacing="0">{html_rows}</table>
        <p style="color:#aaa;font-size:12px;margin-top:24px;">
            Keywords: {', '.join(SEARCH_TERMS)}<br>
            Locations: {', '.join(SEARCH_LOCATIONS)}
        </p>
    </body></html>
    """

    message = Mail(
        from_email=EMAIL_SENDER,
        to_emails=EMAIL_RECEIVER,
        subject=subject,
        html_content=html_body,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"[INFO] Email sent — status: {response.status_code}, jobs: {len(new_jobs)}")
    except Exception as e:
        print(f"[ERROR] Email failed: {e}")
        raise


def main():
    print(f"[START] {date.today()} job scraper running...")

    all_jobs = fetch_jobs()
    matched  = filter_jobs(all_jobs)
    seen     = load_seen()

    new_jobs = [j for j in matched if j["link"] not in seen]
    print(f"[INFO] New jobs after dedup: {len(new_jobs)}")

    send_email(new_jobs)

    seen.update(j["link"] for j in matched)
    save_seen(seen)

    print("[DONE]")


if __name__ == "__main__":
    main()