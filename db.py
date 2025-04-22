import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    try:
        yield conn
    finally:
        conn.close()

def setup_tables():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS posted_articles (
                    id SERIAL PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    article_url TEXT NOT NULL,
                    posted_at TIMESTAMPTZ DEFAULT now()
                );
            """)
            conn.commit()

def set_channel(guild_id, channel_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO guild_settings (guild_id, channel_id)
                VALUES (%s, %s)
                ON CONFLICT (guild_id)
                DO UPDATE SET channel_id = EXCLUDED.channel_id;
            """, (guild_id, channel_id))
            conn.commit()

def get_channel(guild_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
            row = cur.fetchone()
            return row[0] if row else None

def get_recent_links(guild_id, limit=20):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT article_url FROM posted_articles
                WHERE guild_id = %s
                ORDER BY posted_at DESC
                LIMIT %s
            """, (guild_id, limit))
            return [row[0] for row in cur.fetchall()]

def save_article_link(guild_id, article_url):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO posted_articles (guild_id, article_url)
                VALUES (%s, %s)
            """, (guild_id, article_url))
            conn.commit()
