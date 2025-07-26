import os
import re
import json
import discord
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# URL detection regex
URL_REGEX = r"(https?://[^\s]+)"

# Function to extract article text from a link
def fetch_article_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text.strip()
    except Exception as e:
        print(f"[Error fetching article]: {e}")
        return None

# Function to summarize text using Groq's API
def summarize_text_with_groq(article_text):
    prompt = f"Summarize this article in a short, casual, Mexican-English tone:\n\n{article_text[:4000]}"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mixtral-8x7b-32768",  # You can also try llama3-70b-8192
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are 'célula cerebral', a witty and friendly Discord bot. "
                    "You speak English but with a chill Mexican vibe. You help users by summarizing links "
                    "in a way that's casual and helpful. Keep it short and easy to read. Use some playful tone if it fits."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
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
        print(f"[Error with Groq API]: {e}")
        return "Oops, I couldn’t summarize that right now, carnalito."

# Event: Bot is ready
@client.event
async def on_ready():
    print(f"✅ Bot is online as {client.user}")

# Event: Message received
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
            await message.reply(f"📌 **Summary of the link:**\n{summary}", mention_author=False)
        else:
            await message.reply("Ay caray... I couldn't read that link, try another one?", mention_author=False)
    else:
        await message.reply("¿Qué onda? Drop me a link and I’ll break it down for you, compa. 🧠", mention_author=False)

# Start the bot
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
