import httpx

from models import JobPosting

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board_token}"


def fetch_jobs(board_token: str) -> list[JobPosting]:
    response = httpx.get(BASE_URL.format(board_token=board_token))
    response.raise_for_status()
    data = response.json()

    return [
        JobPosting(
            source="ashby",
            external_id=str(job["id"]),
            title=job["title"],
            # Ashby doesn't return a company display name in the payload —
            # the board token is the only company identifier we have here.
            company=board_token,
            location=job["location"],
            url=job["jobUrl"],
        )
        for job in data["jobs"]
    ]
