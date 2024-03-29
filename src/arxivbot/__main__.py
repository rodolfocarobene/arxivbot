"""Discord bot functions."""

import datetime
import json
import os
import textwrap

import discord
import pytz
from discord.ext import commands, tasks
from dotenv import load_dotenv

from .utils import (
    authors_match,
    extract_papers_from_email,
    get_email_body,
    keywords_match,
)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

IMAP_SERVER = os.getenv("IMAP_SERVER")
PORT = int(os.getenv("PORT"))
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

TIME = datetime.time(hour=7, minute=00, tzinfo=pytz.timezone("CET"))
FILENAME = "interests.json"

TODAY_PAPERS = []
TODAY_NUMBER = 0

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

with open(FILENAME, encoding="utf-8") as openfile:
    interests = json.load(openfile)


class DailyFetch(commands.Cog):
    """Daily fetch of new articles."""

    def __init__(self, thisbot) -> None:
        """Initialize task."""
        self.bot = thisbot
        self.my_task.start()

    @tasks.loop(time=TIME)
    async def my_task(self) -> None:
        """Fetch for articles and print them."""
        await fetch_arxiv()
        await print_arxiv(self.bot.get_channel(CHANNEL_ID), True)


@bot.event
async def on_ready():
    """Set bot with autofetch."""
    print("Bot started")
    await fetch_arxiv()
    await bot.add_cog(DailyFetch(bot))


async def send_max_len(channel, text, width=2000):
    """Send a message splitting it in lines of max 2000 chars."""
    lines = textwrap.wrap(text, width, break_long_words=False, replace_whitespace=False)
    for line in lines:
        await channel.send(line)


async def fetch_arxiv():
    """Download email body and check for keywords matches."""
    global TODAY_PAPERS
    global TODAY_NUMBER

    body = get_email_body(IMAP_SERVER, PORT, EMAIL, PASSWORD)
    if body is None:
        print("No email fetched.")
        TODAY_NUMBER = 0
        TODAY_PAPERS = []
        return

    papers = extract_papers_from_email(body)
    TODAY_NUMBER = len(papers)
    TODAY_PAPERS = []

    for paper in papers:
        authors_match(interests["authors"], paper)
        keywords_match(interests["keywords"], paper)
        if len(paper.matching) != 0:
            TODAY_PAPERS.append(paper)
    print(f"Analyzed {TODAY_NUMBER}, {len(TODAY_PAPERS)} are interesting.")


async def print_arxiv(channel, automatic=False):
    """Format arXiv dictionary and print it."""
    datetoday = datetime.datetime.today().strftime("%d/%m/%Y")

    if automatic:
        if datetime.datetime.today().weekday() in (0, 6):
            print("Yesterday was not a working day, no notification!")
            return

    return_str = f"(arXivBot update of the {datetoday})"
    return_str += f"\tYesterday there were {TODAY_NUMBER} new papers, {len(TODAY_PAPERS)} were found interesting"
    await channel.send(return_str)
    if len(TODAY_PAPERS) == 0:
        return

    return_str = ""
    for idx, paper in enumerate(TODAY_PAPERS):
        return_str += f"\n{idx+1}. {paper}\n{paper.matching}"

    await send_max_len(channel, return_str)


# ----------------- BOT COMMANDS ------------------------ #


@bot.command()
async def fetch(channel):
    """Fetch arXiv for new articles."""
    await fetch_arxiv()
    await print_arxiv(channel)


@bot.command()
async def abstract(channel, num):
    """Print an abstract of one of the fetched papers.

    Parameters
    -----------
    num: int
        The number of the paper whose abstract you want to print.
    """
    paper = TODAY_PAPERS[int(num) - 1]

    return_str = f"{paper.title}\n\n{paper.abstract}"
    await send_max_len(channel, return_str)


@bot.command()
async def query(channel):
    """Return the registered queries."""
    await send_max_len(channel, str(interests))


@bot.command()
async def add_queries(channel, cat, *keywords):
    """Add keywords to query.

    Parameters
    -----------
    cat: str
        The category where to add the keywords (categories, authors, keywords).
    keywords: list(str)
        Keywords to add.
    """
    if cat not in interests.keys():
        await channel.send(f"Parameter cannot be {cat}")
    else:
        for key in keywords:
            if key not in interests[cat]:
                interests[cat].append(key)

        with open(FILENAME, "w", encoding="utf-8") as outfile:
            json.dump(interests, outfile)

        return_str = f"Current queries:\n{interests}"
        await send_max_len(channel, return_str)


@bot.command()
async def remove_queries(channel, *keywords):
    """Remove parameters from queries.

    parameters
    -----------
    keyword: list(str)
        The keywords to remove.
    """
    for key in keywords:
        for cat, vals in interests.items():
            interests[cat] = [val for val in vals if val != key]

    with open(FILENAME, "w", encoding="utf-8") as outfile:
        json.dump(interests, outfile)

    return_str = f"Current queries:\n{interests}"
    await send_max_len(channel, return_str)


@bot.command()
async def clear_query(channel):
    """Remove all queries."""
    for cat in interests:
        interests[cat] = []

    with open(FILENAME, "w", encoding="utf-8") as outfile:
        json.dump(interests, outfile)

    return_str = f"Current queries:\n{interests}"
    await send_max_len(channel, return_str)


# ----------------- BOT START ------------------------ #


bot.run(TOKEN)
