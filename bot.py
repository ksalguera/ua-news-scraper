import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from scraper import fetch_latest_articles
from db import setup_tables, set_channel, get_channel, get_recent_links, save_article_link
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

scheduler = AsyncIOScheduler()

def parse_article_date(raw_date):
    cleaned = raw_date.replace(".", "")
    return datetime.strptime(cleaned, '%b %d, %Y')

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    setup_tables()

    await tree.sync()
    print("✅ Synced commands with Discord.")

    scheduler.add_job(post_new_articles, 'cron', hour=9, minute=0, timezone='US/Eastern')
    scheduler.start()
    print("✅ Scheduler started.")

@tree.command(name="setchannel", description="Set this channel to receive news updates.")
async def setchannel(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    guild_id = str(interaction.guild.id)
    set_channel(guild_id, str(channel_id))
    await interaction.response.send_message(f"✅ Updates will be posted in <#{channel_id}>.", ephemeral=True)

@tree.command(name="fetcharticles", description="Fetch and post up to five recent articles for this channel.")
async def fetcharticles(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild_id = str(interaction.guild.id)
    channel = interaction.channel

    await fetch_and_post_articles(guild_id, channel)
    await interaction.followup.send("✅ Articles fetched and posted.", ephemeral=True)

async def fetch_and_post_articles(guild_id, channel):
    latest_articles = fetch_latest_articles()[:5]
    recent_links = get_recent_links(guild_id)

    for article in latest_articles:
        try:
            article_date = parse_article_date(article['date'])
            if article['link'] not in recent_links:
                await channel.send(article['link'])
                save_article_link(guild_id, article['link'], article_date.date())
        except Exception as e:
            print(f"Error processing article: {e}")

async def post_new_articles():
    latest_articles = fetch_latest_articles()[:10]
    now = datetime.now(pytz.timezone('US/Eastern'))

    for guild in client.guilds:
        guild_id = str(guild.id)
        channel_id = get_channel(guild_id)
        if channel_id:
            channel = guild.get_channel(int(channel_id))
            if channel:
                recent_links = get_recent_links(guild_id)

                for article in latest_articles:
                    try:
                        article_date = parse_article_date(article['date'])
                        if article_date.date() == now.date() and article['link'] not in recent_links:
                            await channel.send(article['link'])
                            save_article_link(guild_id, article['link'], article_date.date())
                    except Exception as e:
                        print(f"Error processing article for guild {guild_id}: {e}")

client.run(DISCORD_TOKEN)