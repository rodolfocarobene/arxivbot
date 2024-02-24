# ArXiv Discord Bot

This Discord bot is designed to fetch new arXiv papers based on specified
interests and share them in a designated channel. It utilizes the arXiv API to
search for papers matching provided categories, authors, and keywords, then
presents the results in the Discord server.

## Installation

To run this bot, ensure the requirements are met by installing it:

```bash
pip install .
```

## Setup

1. Clone this repository to your local machine.
2. Obtain a Discord bot token from the Discord Developer Portal.
3. Create a `.env` file in the project directory and add your Discord bot token:

   ```plaintext
   DISCORD_TOKEN=your_discord_bot_token_here
   GUILD_ID=your_discord_guild_id_here
   CHANNEL_ID=your_discord_channel_id_here
   ```

4. Customize the bot's interests by modifying the `interests` dictionary in the
   script.
5. Adjust other configurations like `MAX_NUMBER_OF_RESULTS` and `TIME` if
   needed.
6. Invite the bot to your Discord server using the OAuth2 URL generated from the
   Discord Developer Portal.

## Usage

Run the bot using:

```bash
python bot.py
```

Once the bot is set up and running, you can use the following commands:

- `!fetch`: Fetches arXiv for new articles and prints them in the specified
  channel.
- `!abstract <num>`: Prints the abstract of a fetched paper based on its number.
- `!query`: Returns the registered queries.
- `!add_queries <cat> <keywords>`: Adds keywords to the specified category
  (categories, authors, keywords).
- `!remove_query <keyword>`: Removes a parameter from the queries.
- `!clear_query`: Removes all queries.
- `!max_results <num>`: Changes the maximum number of results to fetch.

## Note

- The bot fetches papers daily at the specified time (`TIME` variable in the
  script).
- Papers fetched will be from the current day.
- Make sure to set up appropriate permissions for the bot in your Discord
  server.
