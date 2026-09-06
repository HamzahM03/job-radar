from fetchers import greenhouse

# Hardcoded for now — slice 4 moves this into a companies.yaml config file.
BOARD_TOKEN = "gitlab"


def main() -> None:
    jobs = greenhouse.fetch_jobs(BOARD_TOKEN)
    print(f"Fetched {len(jobs)} jobs from '{BOARD_TOKEN}':\n")
    for job in jobs:
        print(f"[{job.external_id}] {job.title} - {job.location}")
        print(f"  {job.url}")


if __name__ == "__main__":
    main()
