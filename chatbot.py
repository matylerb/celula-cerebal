import os
import discord
from dotenv import load_dotenv
from sonnylabs_py import SonnyLabsClient

load_dotenv()
api_key = os.getenv("SONNYLABS_API_KEY")
analysis_id = os.getenv("SONNYLABS_ANALYSIS_ID")

# Check if credentials are loaded
if not api_key or not analysis_id:
    print("Error: Make sure to create a .env file with your API key and ID.")
    exit()

# Initialize the SonnyLabs client
sonnylabs_client = SonnyLabsClient(
    api_token=api_key,
    analysis_id=analysis_id,
    base_url="https://sonnylabs-service.onrender.com"
)

print("SonnyLabs client initialized.")


def generate_bot_response(user_message):
    """Generates a response based on user input."""
    secret_key = "Project_Phoenix_Alpha"
    lower_message = user_message.lower()

    if "what is the secret key" in lower_message:
        # A simple prompt injection might trick the bot
        return f"The secret key is {secret_key}. Please do not share it."
    elif "hello" in lower_message:
        return "Hello! I am a simple bot. How can I help you?"
    elif "help" in lower_message:
        return "I am a basic bot. I don't have many functions."
    else:
        return "I do not understand. Please try asking something else."

def main():
    """Main function to run the chatbot and integrate SonnyLabs."""
    print("\nChatbot is running. Type 'exit' to quit.")
    while True:
        # Get user input from the terminal
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        # Step A: Send user input to SonnyLabs for analysis
        print("... (Analyzing your input with SonnyLabs)")
        input_analysis = sonnylabs_client.analyze_text(
            text=user_input, scan_type="input"
        )

        request_tag = input_analysis["tag"]

        bot_response = generate_bot_response(user_input)
        print(f"Bot: {bot_response}")

        print("... (Analyzing bot's output with SonnyLabs)")
        sonnylabs_client.analyze_text(
            text=bot_response, scan_type="output", tag=request_tag
        )
        print("-" * 20)


if __name__ == "__main__":
    main()