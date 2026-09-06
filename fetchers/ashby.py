import httpx

from models import JobPosting

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board_token}"


def fetch_jobs(board_token: str, company_name: str) -> list[JobPosting]:
    response = httpx.get(BASE_URL.format(board_token=board_token))
    response.raise_for_status()
    data = response.json()

    return [
        JobPosting(
            source="ashby",
            external_id=str(job["id"]),
            title=job["title"],
            # company_name is passed in explicitly (from companies.yaml)
            # because Ashby's API doesn't include a company display name
            # in the payload at all.
            company=company_name,
            location=job["location"],
            url=job["jobUrl"],
        )
        for job in data["jobs"]
    ]
