from pathlib import Path

import yaml

from db import get_connection, has_seen, save_job
from fetchers import ashby, greenhouse, lever

COMPANIES_FILE = Path(__file__).parent / "companies.yaml"

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


def main() -> None:
    conn = get_connection()
    companies = load_companies()
    validate_sources(companies)

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
            save_job(conn, job)
            new_count += 1
            print(f"[NEW] {job.title} - {job.location}")
            print(f"  {job.url}")

        print(f"{source}/{board_token}: {len(jobs)} fetched, {new_count} new\n")

    conn.close()


if __name__ == "__main__":
    main()
