from pathlib import Path

import yaml

from db import get_connection, has_seen, save_job
from fetchers import ashby, greenhouse, lever
from filters import Verdict, classify_job

COMPANIES_FILE = Path(__file__).parent / "companies.yaml"
PREFERENCES_FILE = Path(__file__).parent / "preferences.yaml"

FETCH_BY_SOURCE = {
    "greenhouse": greenhouse.fetch_jobs,
    "lever": lever.fetch_jobs,
    "ashby": ashby.fetch_jobs,
}


def load_companies() -> list[dict]:
    with open(COMPANIES_FILE) as f:
        return yaml.safe_load(f)


def validate_sources(companies: list[dict]) -> None:
    invalid = [
        (company["name"], company["source"])
        for company in companies
        if company["source"] not in FETCH_BY_SOURCE
    ]
    if not invalid:
        return

    valid_sources = ", ".join(FETCH_BY_SOURCE)
    problems = "; ".join(f"'{name}' has source '{source}'" for name, source in invalid)
    raise ValueError(
        f"Invalid source(s) in companies.yaml - must be one of: "
        f"{valid_sources}. Problems: {problems}"
    )


def load_preferences() -> dict:
    with open(PREFERENCES_FILE) as f:
        return yaml.safe_load(f)


def validate_preferences(preferences: dict) -> None:
    problems = []
    if not preferences.get("target_titles"):
        problems.append("target_titles must be a non-empty list")
    if not preferences.get("locations"):
        problems.append("locations must be a non-empty list")
    if preferences.get("max_years_experience") is None:
        problems.append("max_years_experience is required")

    if problems:
        raise ValueError(f"Invalid preferences.yaml - {'; '.join(problems)}")


def main() -> None:
    conn = get_connection()
    companies = load_companies()
    validate_sources(companies)
    preferences = load_preferences()
    validate_preferences(preferences)

    for company in companies:
        name = company["name"]
        source = company["source"]
        board_token = company["board_token"]

        fetch_jobs = FETCH_BY_SOURCE[source]
        jobs = fetch_jobs(board_token, name)
        new_count = 0

        for job in jobs:
            if has_seen(conn, job.source, job.external_id):
                continue

            result = classify_job(job, preferences)
            # Only survivors of the cheap filters get a stored description -
            # REJECTed jobs never need one, even though it was already parsed
            # in memory above (it came from the same bulk fetch either way).
            description = job.description if result.verdict != Verdict.REJECT else None
            save_job(conn, job, description=description)
            new_count += 1

            print(f"[{result.verdict.value}] {job.title} - {job.location}")
            print(f"  reason: {result.reason}")
            print(f"  {job.url}")

        print(f"{source}/{board_token}: {len(jobs)} fetched, {new_count} new\n")

    conn.close()


if __name__ == "__main__":
    main()
