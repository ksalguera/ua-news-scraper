import os
import discord
from discord.ext import tasks
from discord import app_commands
from dotenv import load_dotenv
from scraper import fetch_latest_articles
from db import setup_tables, set_channel, get_channel, get_recent_links, save_article_link

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    setup_tables()

    await tree.sync()
    print("✅ Synced commands with Discord.")

    post_new_articles.start()

@tree.command(name="setchannel", description="Set this channel to receive news updates.")
async def setchannel(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    channel_id = interaction.channel.id
    set_channel(guild_id, channel_id)
    await interaction.response.send_message(f"✅ Updates will be posted in <#{channel_id}>.", ephemeral=True)

@tasks.loop(minutes=60)
async def post_new_articles():
    latest_links = fetch_latest_articles()

    for guild in client.guilds:
        guild_id = str(guild.id)
        channel_id = get_channel(guild_id)

        if not channel_id:
            continue

        channel = await client.fetch_channel(int(channel_id))
        recent_links = get_recent_links(guild_id)

        new_links = [link for link in latest_links if link not in recent_links]

        for link in reversed(new_links):
            await channel.send(link)
            save_article_link(guild_id, link)
    
client.run(DISCORD_TOKEN)