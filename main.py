from fetchers import ashby, greenhouse, lever

# Hardcoded for now — slice 4 moves this into a companies.yaml config file.
# One company per ATS, just to prove all three fetchers behave the same way.
COMPANIES = [
    ("greenhouse", "gitlab"),
    ("lever", "palantir"),
    ("ashby", "linear"),
]

FETCH_BY_SOURCE = {
    "greenhouse": greenhouse.fetch_jobs,
    "lever": lever.fetch_jobs,
    "ashby": ashby.fetch_jobs,
}


def main() -> None:
    for source, board_token in COMPANIES:
        fetch_jobs = FETCH_BY_SOURCE[source]
        jobs = fetch_jobs(board_token)
        print(f"Fetched {len(jobs)} jobs from {source}/{board_token}:\n")
        for job in jobs:
            print(f"[{job.external_id}] {job.title} - {job.location}")
            print(f"  {job.url}")
        print()


if __name__ == "__main__":
    main()
