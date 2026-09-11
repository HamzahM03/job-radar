from dataclasses import dataclass


@dataclass
class JobPosting:
    source: str  # "greenhouse", "lever", or "ashby"
    external_id: str  # the ID the ATS itself assigns to this posting
    title: str
    company: str
    location: str
    url: str
    description: str | None = None
