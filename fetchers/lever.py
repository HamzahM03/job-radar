import httpx

from fetchers.html_text import html_to_text
from models import JobPosting

BASE_URL = "https://api.lever.co/v0/postings/{board_token}?mode=json"


def _build_description(job: dict) -> str:
    # Lever splits a posting's text across three places: descriptionPlain
    # (the intro), lists (bulleted sections like "What We Require" - HTML,
    # unlike the other fields), and additionalPlain (benefits/EEO boilerplate).
    # None of these alone is the full posting, so they're stitched together.
    sections = [job.get("descriptionPlain", "")]

    for section in job.get("lists", []):
        heading = section.get("text", "")
        body = html_to_text(section.get("content", ""))
        sections.append(f"{heading}\n{body}" if heading else body)

    additional = job.get("additionalPlain", "")
    if additional:
        sections.append(additional)

    return "\n\n".join(section for section in sections if section)


def fetch_jobs(board_token: str, company_name: str) -> list[JobPosting]:
    response = httpx.get(BASE_URL.format(board_token=board_token))
    response.raise_for_status()
    data = response.json()

    jobs = []
    for job in data:
        try:
            description = _build_description(job)
        except Exception as e:
            print(f"  [WARN] lever/{board_token}: couldn't parse description for job {job.get('id')}: {e}")
            description = None

        jobs.append(
            JobPosting(
                source="lever",
                external_id=str(job["id"]),
                title=job["text"],
                # company_name is passed in explicitly (from companies.yaml)
                # because Lever's API doesn't include a company display name
                # in the payload at all.
                company=company_name,
                location=job["categories"].get("location", "Unknown"),
                url=job["hostedUrl"],
                description=description,
            )
        )
    return jobs
