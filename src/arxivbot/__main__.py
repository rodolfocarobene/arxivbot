"""Retrieve papers."""

import os

from dotenv import load_dotenv

from .utils import (
    authors_match,
    extract_papers_from_email,
    get_email_body,
    keywords_match,
)

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
PORT = int(os.getenv("PORT"))
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

interests = {
    "authors": ["Nicolas Roch"],
    "keywords": [
        "superconducting qubit",
        "TWPA",
        "parametric amplifier",
        "qudits",
        "RFSoC",
        "fluxonium",
    ],
}


def main():
    """Execute main function."""
    body = get_email_body(IMAP_SERVER, PORT, EMAIL, PASSWORD)
    if body is None:
        print("Failed to fetch emails.")
        return

    papers = extract_papers_from_email(body)

    matching_papers = []
    for paper in papers:
        authors_match(interests["authors"], paper)
        keywords_match(interests["keywords"], paper)
        if len(paper.matching) != 0:
            matching_papers.append(paper)

    print(
        f"\nOf {len(papers)} new papers, {len(matching_papers)} matched your keywords"
    )

    for idx, paper in enumerate(matching_papers):
        print(f"\n{idx+1}. {paper}")
        print(f"Matches: {paper.matching}")


if __name__ == "__main__":
    main()
