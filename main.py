import os
import re
import discord
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Regex to detect links
URL_REGEX = r"(https?://[^\s]+)"

# Scrape text from a webpage
def fetch_article_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text.strip()
    except Exception as e:
        print(f"[Error] Failed to fetch article: {e}")
        return None

# Summarize with Groq
def summarize_text_with_groq(article_text):
    prompt = f"Summarize this article in a short, friendly tone:\n\n{article_text[:4000]}"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mixtral-8x7b-32768",  # or llama3-70b-8192
        "messages": [
            {"role": "system", "content": "You are a helpful and witty Discord bot named 'célula cerebral'. You speak English with a Mexican vibe and summarize content casually."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Error] Groq summarization failed: {e}")
        return "Ay caramba... I couldn't summarize that, amigo."

# On bot ready
@client.event
async def on_ready():
    print(f"[INFO] Logged in as {client.user}")

# On message received
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    urls = re.findall(URL_REGEX, message.content)

    if urls:
        await message.channel.typing()
        url = urls[0]
        article_text = fetch_article_text(url)

        if article_text:
            summary = summarize_text_with_groq(article_text)
            await message.reply(f"📚 **Summary of the link:**\n{summary}", mention_author=False)
        else:
            await message.reply("No manches... I couldn’t read that link.", mention_author=False)
    else:
        # Casual fallback response
        await message.reply("Qué onda! Send me a link and I’ll tell you what’s up. 🔍", mention_author=False)

# Run the bot
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
