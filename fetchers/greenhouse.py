import httpx

from fetchers.html_text import html_to_text
from models import JobPosting

# content=true is required to get the job description in the list response -
# without it, Greenhouse omits it entirely rather than requiring a separate
# per-job call.
BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"


def fetch_jobs(board_token: str, company_name: str) -> list[JobPosting]:
    response = httpx.get(BASE_URL.format(board_token=board_token))
    response.raise_for_status()
    data = response.json()

    jobs = []
    for job in data["jobs"]:
        try:
            description = html_to_text(job["content"])
        except Exception as e:
            print(f"  [WARN] greenhouse/{board_token}: couldn't parse description for job {job.get('id')}: {e}")
            description = None

        jobs.append(
            JobPosting(
                source="greenhouse",
                external_id=str(job["id"]),
                title=job["title"],
                # company_name comes from companies.yaml, not job["company_name"],
                # so all three sources report a company name the same way.
                company=company_name,
                location=job["location"]["name"],
                url=job["absolute_url"],
                description=description,
            )
        )
    return jobs
