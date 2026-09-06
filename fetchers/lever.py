import httpx

from models import JobPosting

BASE_URL = "https://api.lever.co/v0/postings/{board_token}?mode=json"


def fetch_jobs(board_token: str) -> list[JobPosting]:
    response = httpx.get(BASE_URL.format(board_token=board_token))
    response.raise_for_status()
    data = response.json()

    return [
        JobPosting(
            source="lever",
            external_id=str(job["id"]),
            title=job["text"],
            # Lever doesn't return a company display name in the payload —
            # the board token is the only company identifier we have here.
            company=board_token,
            location=job["categories"].get("location", "Unknown"),
            url=job["hostedUrl"],
        )
        for job in data
    ]
