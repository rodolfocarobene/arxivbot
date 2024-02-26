"""Discord bot to fetch new arXiv papers."""

import datetime
import os
import textwrap

import arxiv
import discord
import pytz
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MAX_NUMBER_OF_RESULTS = 20
TIME = datetime.time(hour=7, minute=00, tzinfo=pytz.timezone("CET"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

today = True  # only fetch for today's articles
TODAY_ARXIV = {}

interests = {
    "categories": ["quant-ph"],
    "authors": ["Malnou", "Cancelo"],
    "keywords": ["TWPA", "RFSoC", "superconducting qubit"],
}


async def send_max_len(channel, text, width=2000):
    """Send a message splitting it in lines of max 2000 chars."""
    lines = textwrap.wrap(text, width, break_long_words=False, replace_whitespace=False)
    for line in lines:
        await channel.send(line)


@bot.event
async def on_ready():
    """Set bot with autofetch."""
    print("Bot started")
    await fetch_arxiv()
    # channel = bot.get_channel(CHANNEL_ID)
    # await print_arxiv(channel)
    await bot.add_cog(DailyFetch(bot))


class DailyFetch(commands.Cog):
    """Daily fetch of new articles."""

    def __init__(self, bot) -> None:
        """Initialize task."""
        self.bot = bot
        self.my_task.start()

    @tasks.loop(time=TIME)
    async def my_task(self) -> None:
        """Fetch for articles and print them."""
        await fetch_arxiv()
        await print_arxiv(self.bot.get_channel(CHANNEL_ID))


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
    return_str = f"""{TODAY_ARXIV[int(num)].title}

    {TODAY_ARXIV[int(num)].summary}
    """
    await channel.send(return_str)


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
        await channel.send(f"Parameter 1 cannot be {cat}")
    else:
        for key in keywords:
            interests[cat].append(key)
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
    return_str = f"Current queries:\n{interests}"
    await send_max_len(channel, return_str)


@bot.command()
async def clear_query(channel):
    """Remove all queries."""
    for cat in interests:
        interests[cat] = []
    return_str = f"Current queries:\n{interests}"
    await send_max_len(channel, return_str)


@bot.command()
async def max_results(channel, num):
    """Change max number of results to fetch.

    parameters
    -----------
    num: int
        The maximum number of results to output.
    """
    global MAX_NUMBER_OF_RESULTS
    MAX_NUMBER_OF_RESULTS = int(num)
    await channel.send(f"Current max number: {MAX_NUMBER_OF_RESULTS}")


async def print_arxiv(channel):
    """Format arXiv dictionary and print it."""
    today = datetime.datetime.today().strftime("%d/%m/%Y")
    if len(TODAY_ARXIV) == 0:
        await channel.send(
            f"(arXivBot update of the {today})\tNo interesting articles today :-("
        )
        return
    return_str = f"(arXivBot update of the {today})\tNew interesting paper published on arXiv today!\n"
    for i, r in enumerate(TODAY_ARXIV.values()):
        names = r.authors[0].name.split(" ")
        first_author = f"{names[0][0]} {names[-1]}"
        return_str += f"\n{i+1}: {r.title} ({first_author}): {r.pdf_url}"

    await send_max_len(channel, return_str)


async def fetch_arxiv():
    """Fetch arXiv for new articles matching interests."""
    global TODAY_ARXIV
    TODAY_ARXIV = {}
    client = arxiv.Client()

    queries = []
    queries.append(" OR ".join("ca:" + i for i in interests["categories"]))
    queries.append(" OR ".join("au:" + i for i in interests["authors"]))
    queries.append(" OR ".join(interests["keywords"]))

    query = " OR ".join(queries)

    search = arxiv.Search(
        query=query,
        max_results=MAX_NUMBER_OF_RESULTS,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    results = client.results(search)

    return_str = ""

    for i, r in enumerate(results):
        if today:
            if r.updated.date() != datetime.datetime.today().date():
                break
        return_str += f"\n{i+1}: {r.title} ({r.pdf_url})"
        TODAY_ARXIV[i + 1] = r


bot.run(TOKEN)
