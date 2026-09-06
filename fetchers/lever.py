import httpx

from models import JobPosting

BASE_URL = "https://api.lever.co/v0/postings/{board_token}?mode=json"


def fetch_jobs(board_token: str, company_name: str) -> list[JobPosting]:
    response = httpx.get(BASE_URL.format(board_token=board_token))
    response.raise_for_status()
    data = response.json()

    return [
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
        )
        for job in data
    ]
