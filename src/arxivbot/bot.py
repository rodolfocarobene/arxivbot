"""Discord bot to fetch new arXiv papers."""

import os
import arxiv
import discord
import datetime
from discord.ext import commands, tasks

from dotenv import load_dotenv

import pytz

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MAX_NUMBER_OF_RESULTS = 20
TIME = datetime.time(hour=7, minute=00, tzinfo=pytz.timezone("CET"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TODAY_ARXIV = {}

interests = {
    "categories": ["quant-ph"],
    "authors": ["Giachero"],
    "keywords": ["TWPA", "RFSoC"],
}


@bot.event
async def on_ready():
    """Set bot with autofetch."""
    print("Bot started")
    channel = bot.get_channel(CHANNEL_ID)
    await fetch_arxiv()
    await print_arxiv(channel)

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
    await channel.send(str(interests))


@bot.command()
async def add_queries(channel, cat, *keywords):
    """Add keywords to query.

    Parameters
    -----------
    cat: str
        Te category where to add the keywords (categories, authors, keywords).
    keywords: list(str)
        Keywords to add.
    """
    if cat not in interests.keys():
        await channel.send(f"Parameter 1 cannot be {cat}")
    else:
        for key in keywords:
            interests[cat].append(key)
        await channel.send(f"Current queries:\n{interests}")


@bot.command()
async def remove_query(channel, keyword):
    """Remove a parameter from queries.

    parameters
    -----------
    keyword: str
        The keyword to remove.
    """
    for cat, vals in interests.items():
        interests[cat] = [val for val in vals if val != keyword]
    await channel.send(f"Current queries:\n{interests}")


@bot.command()
async def clear_query(channel):
    """Remove all queries."""
    for cat in interests:
        interests[cat] = []
    await channel.send(f"Current queries:\n{interests}")


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
    await channel.send(return_str)


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
        if r.updated.date() != datetime.datetime.today().date():
            break
        return_str += f"\n{i+1}: {r.title} ({r.pdf_url})"
        TODAY_ARXIV[i + 1] = r


bot.run(TOKEN)
