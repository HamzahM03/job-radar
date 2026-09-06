# job-radar

## Coding conventions

- When mapping external API data into a dataclass (e.g. `JobPosting`), always
  cast each field to its declared type explicitly, even if the source data
  already matches that type (e.g. `external_id=str(job["id"])` even when
  `job["id"]` is already a string). This protects against an upstream API
  silently changing its response shape later.
- Comments should explain WHY, not WHAT. Don't comment on things the code
  already makes obvious (e.g. "assigns title"). Do comment when relying on
  something non-obvious about a real API's actual behavior (e.g. "Greenhouse
  always includes location.name, even for remote roles").

## Workflow rules

- Never add a new dependency without asking first and explaining why it's
  needed.
- Build one slice at a time. After finishing a slice, stop, summarize what
  was built and why, and wait for review before starting the next slice.
  Don't chain into the next slice automatically.
