import re
from dataclasses import dataclass
from enum import Enum

from models import JobPosting


class Verdict(Enum):
    REJECT = "REJECT"
    ACCEPT = "ACCEPT"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass
class FilterResult:
    verdict: Verdict
    reason: str


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(r"\b" + re.escape(phrase) + r"\b", text, re.IGNORECASE) is not None


def _find_reject_term(title: str, reject_terms: list[str]) -> str | None:
    for term in reject_terms:
        if _contains_phrase(title, term):
            return term
    return None


def _match_title(title: str, target_titles: list[str]) -> FilterResult:
    for target in target_titles:
        if _contains_phrase(title, target):
            return FilterResult(Verdict.ACCEPT, f"title matches target '{target}'")

    # No clean phrase match. Check word overlap before giving up, e.g. "Backend
    # Infrastructure Engineer" shares every word with "backend engineer" but
    # isn't a contiguous phrase match - that's a partial hit, not a clear miss.
    title_words = set(re.findall(r"[a-z0-9]+", title.lower()))
    for target in target_titles:
        shared = set(target.lower().split()) & title_words
        if shared:
            return FilterResult(
                Verdict.AMBIGUOUS,
                f"title shares word(s) {sorted(shared)} with target '{target}' "
                "but isn't a clean match",
            )

    return FilterResult(Verdict.REJECT, "title doesn't match any target title")


def _match_location(location: str, target_locations: list[str]) -> FilterResult:
    # "Unknown" is the fetcher's own fallback for a missing location (see
    # fetchers/lever.py) - treat it as unresolved, not a mismatch.
    if location.strip().lower() in ("", "unknown"):
        return FilterResult(Verdict.AMBIGUOUS, "location is unknown - can't confirm a match")

    for target in target_locations:
        if _contains_phrase(location, target):
            return FilterResult(Verdict.ACCEPT, f"location matches target '{target}'")

    return FilterResult(Verdict.REJECT, f"location '{location}' isn't in target locations")


def _match_experience() -> FilterResult:
    # Fetchers only pull title/location/url/id today - no job description is
    # available to check years of experience against, so this is always
    # unresolved until a later slice fetches descriptions.
    return FilterResult(
        Verdict.AMBIGUOUS,
        "years of experience not available - job descriptions aren't fetched yet",
    )


def classify_job(job: JobPosting, preferences: dict) -> FilterResult:
    reject_term = _find_reject_term(job.title, preferences.get("reject_title_terms") or [])
    if reject_term:
        return FilterResult(Verdict.REJECT, f"title contains reject term '{reject_term}'")

    location_result = _match_location(job.location, preferences["locations"])
    if location_result.verdict == Verdict.REJECT:
        return location_result

    title_result = _match_title(job.title, preferences["target_titles"])
    if title_result.verdict == Verdict.REJECT:
        return title_result

    experience_result = _match_experience()

    ambiguous_reasons = [
        result.reason
        for result in (location_result, title_result, experience_result)
        if result.verdict == Verdict.AMBIGUOUS
    ]
    if ambiguous_reasons:
        return FilterResult(Verdict.AMBIGUOUS, "; ".join(ambiguous_reasons))

    return FilterResult(Verdict.ACCEPT, "title, location, and experience all match preferences")
