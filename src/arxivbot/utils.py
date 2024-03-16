"""Utility functions for email fetching."""

import email
import imaplib
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Union

import pytz


@dataclass
class Paper:
    """Paper class."""

    arxiv_id: str
    title: str
    authors: list[str]
    categories: str
    abstract: str
    link: str
    matching: Optional[list[str]] = None

    def __post_init__(self):
        """Correctly initialize empty matching list."""
        if self.matching is None:
            self.matching = []

    def __str__(self):
        """Return string representation."""
        names = self.authors[0].split(" ")
        author_str = f"{names[0][0]} {names[-1]}"
        if len(self.authors) != 1:
            author_str += " et al."
        return f"{self.title}, {author_str} (<{self.link}>)"


def extract_email_from_id(mail, id):
    """Return email message from email id."""
    _, email_data = mail.fetch(id, "(RFC822)")
    return email.message_from_bytes(email_data[0][1])


def convert_to_datetime(date_str) -> Union[datetime, None]:
    """Take email date and convert it to datetime obj."""
    date_obj = email.utils.parsedate_tz(date_str)
    if date_obj:
        timestamp = email.utils.mktime_tz(date_obj)
        return datetime.fromtimestamp(timestamp, tz=pytz.timezone("CET"))

    return None


def extract_papers_from_email(email_body):
    """Return list of paper objects from email body."""
    papers = []
    # Regular expression pattern for extracting paper information
    pattern = re.compile(
        r"\\\narXiv:(.*?)\nDate:(.*?)\n\nTitle:(.*?)\nAuthors:(.*?)\nCategories:(.*?)\n(?s:.*?)\\\n\s(.*?)\\\s\(\s(.*?)\s",
        re.DOTALL,
    )

    matches = pattern.findall(email_body)

    for match in matches:
        arxiv_id = match[0].strip()
        title = re.sub(" +", " ", match[2].strip().replace("\n", " "))
        authors = match[3].strip().replace("\n", " ")
        categories = match[4].strip()
        abstract = re.sub(" +", " ", match[5].strip().replace("\n", " "))
        link = match[6].strip()

        authors = authors.replace(" and ", ", ")
        authors = re.sub(" +", " ", authors)
        authors = authors.split(", ")

        paper = Paper(arxiv_id, title, authors, categories, abstract, link)
        papers.append(paper)

    return papers


def get_email_body(IMAP_SERVER, PORT, EMAIL, PASSWORD):
    """Connect to email and return body of the correct arxiv email from today."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, PORT)
    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")
    _, email_ids = mail.search(None, '(SUBJECT "quant-ph daily")')

    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        latest_email_id = email_ids[0].split()[-1]
        msg = extract_email_from_id(mail, latest_email_id)
        received_date = convert_to_datetime(msg.get("Date")).date()

        if received_date == today:
            print("Found newer email")
            latest_email_id = email_ids[0].split()[-2]
            msg = extract_email_from_id(mail, latest_email_id)
            received_date = convert_to_datetime(msg.get("Date")).date()

        if received_date == yesterday:
            print("The email was received yesterday.")
            mail.logout()

            body = msg.get_payload(decode=True).decode()
            body = re.sub(" +", " ", body)
            body = re.sub("\r", "", body)

            return body
        else:
            print("The email was not received yesterday.")
            mail.logout()
            return None
    except Exception as e:
        print(e)
        mail.logout()
        return None


def authors_match(authors_of_interest, paper):
    """Check if authors of interest are present in a specific paper.

    If they are, add it to the matching parameter of the paper object.
    """
    surnames_of_interest = [
        f"{name.split(' ')[0][0]} {name.split(' ')[-1]}" for name in authors_of_interest
    ]
    surnames_paper = [
        f"{name.split(' ')[0][0]} {name.split(' ')[-1]}" for name in paper.authors
    ]

    for idx, surname in enumerate(surnames_of_interest):
        if surname in surnames_paper:
            paper.matching.append(authors_of_interest[idx])


def keywords_match(keywords_of_interest, paper):
    """Check if keywords of interest are present in a specific paper.

    If they are, add it to the matching parameter of the paper object.
    """
    title = paper.title
    abstract = paper.abstract

    lower_keywords = [key.lower() for key in keywords_of_interest]
    lower_title = title.lower()
    lower_abstract = abstract.lower()

    for idx, key in enumerate(lower_keywords):
        if key in lower_title or key in lower_abstract:
            paper.matching.append(keywords_of_interest[idx])
