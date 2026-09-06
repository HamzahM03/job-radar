import httpx

from models import JobPosting

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


def fetch_jobs(board_token: str, company_name: str) -> list[JobPosting]:
    response = httpx.get(BASE_URL.format(board_token=board_token))
    response.raise_for_status()
    data = response.json()

    return [
        JobPosting(
            source="greenhouse",
            external_id=str(job["id"]),
            title=job["title"],
            # company_name comes from companies.yaml, not job["company_name"],
            # so all three sources report a company name the same way.
            company=company_name,
            location=job["location"]["name"],
            url=job["absolute_url"],
        )
        for job in data["jobs"]
    ]
