import os
import re
import json
import discord
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sonnylabs_py import SonnyLabsClient

# --- Configuration & Initialization ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SONNYLABS_API_KEY = os.getenv("SONNYLABS_API_KEY")
SONNYLABS_ANALYSIS_ID = os.getenv("SONNYLABS_ANALYSIS_ID")

if not all([DISCORD_TOKEN, GROQ_API_KEY, SONNYLABS_API_KEY, SONNYLABS_ANALYSIS_ID]):
    print("❌ ERROR: One or more required environment variables are missing.")
    exit()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

sonnylabs_client = SonnyLabsClient(
    api_token=SONNYLABS_API_KEY,
    analysis_id=SONNYLABS_ANALYSIS_ID,
    base_url="https://sonnylabs-service.onrender.com",
)

URL_REGEX = r"(https?://[^\s]+)"

def fetch_article_text(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = (
            soup.find("article") or soup.find("main") or soup.find(id="content")
        )
        paragraphs = main_content.find_all("p") if main_content else soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text.strip() if len(text.split()) > 50 else None
    except Exception as e:
        print(f"[Error] Failed to fetch article: {e}")
        return None

def summarize_text_with_groq(article_text):
    """Summarizes the given text using the Groq API with better error handling."""
    prompt = f"Summarize this article in a short, friendly tone:\n\n{article_text[:4000]}"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        # --- THIS IS THE ONLY LINE THAT HAS BEEN CHANGED ---
        "model": "llama3-8b-8192",  # Switched from the old model to a new, active one.
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful and witty Discord bot named 'célula cerebral'. You speak English with a Mexican vibe and summarize content casually.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 300,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
        )
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        else:
            print(f"[Error] Groq API returned an unexpected response: {result}")
            return "Híjole, the API gave me a weird response. Can't summarize this one."

    except requests.exceptions.HTTPError as http_err:
        print(f"[FATAL] HTTP error occurred with Groq API: {http_err}")
        print(f"[FATAL] Response Body: {response.text}")
        return "Ay caramba... I couldn't summarize that, amigo. (HTTP Error)"
    except Exception as e:
        print(f"[FATAL] An unexpected error occurred with Groq API: {e}")
        return "Ay caramba... I couldn't summarize that, amigo. (General Error)"


@client.event
async def on_ready():
    print(f"[INFO] Logged in as {client.user}")
    print("[INFO] SonnyLabs client initialized. Bot is ready.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    request_tag = None
    try:
        input_analysis = sonnylabs_client.analyze_text(text=message.content, scan_type="input")
        request_tag = input_analysis.get("tag")
    except Exception as e:
        print(f"[Error] SonnyLabs input analysis failed: {e}")

    match = re.search(URL_REGEX, message.content)
    bot_response_text = None
    reply_payload = {}

    if match:
        async with message.channel.typing():
            url = match.group(0)
            article_text = fetch_article_text(url)
            if article_text:
                summary = summarize_text_with_groq(article_text)
                bot_response_text = summary
                embed = discord.Embed(
                    title="🧠 Here's the lowdown, compa:",
                    description=summary,
                    color=discord.Color.from_rgb(0, 170, 255),
                )
                embed.add_field(name="Original Link", value=f"<{url}>", inline=False)
                embed.set_footer(text="Summarized by célula cerebral")
                reply_payload = {"embed": embed}
            else:
                bot_response_text = "No manches... I couldn’t read that link. It might be empty or protected."
                reply_payload = {"content": bot_response_text}

    if bot_response_text and request_tag:
        try:
            sonnylabs_client.analyze_text(text=bot_response_text, scan_type="output", tag=request_tag)
        except Exception as e:
            print(f"[Error] SonnyLabs output analysis failed: {e}")

    if reply_payload:
        await message.reply(**reply_payload, mention_author=False)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)