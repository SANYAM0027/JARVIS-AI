from openai import OpenAI
from config.api_keys import OPENROUTER_API_KEY, JARVIS_MODEL  # Centralized config import
from ai.memory import jarvis_memory

# OpenRouter Client initialized using centralized configuration
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

SYSTEM_PROMPT = """
You are JARVIS, an advanced AI operating system acting as the elite growth strategist for Sanyam Chanana's digital media platform: TechFinTrail.com.

When handling analytics inquiries:
1. Treat website metrics with rigorous professional depth.
2. Focus on maximizing Lead Generation (newsletter signups, affiliate link clicks, financial product applications).
3. Outline clear actionable directives to enhance performance metrics via Search Engine Optimization (SEO), high-intent keyword targeting, and strategic newsletter funneling.
4. Address the user as Sir. Be precise, articulate, and structured.
"""


def process_command(command):

    command_lower = command.lower()

    try:

        # --------------------
        # MEMORY COMMANDS
        # --------------------

        if command_lower.startswith("remember"):

            content = command.replace(
                "remember",
                "",
                1
            ).strip()

            memory_id = f"memory_{len(jarvis_memory.memory)+1}"

            jarvis_memory.remember(
                memory_id,
                content
            )

            return "I will remember that, Sir."

        if "show memory" in command_lower:

            memory = jarvis_memory.show_memory()

            if not memory:
                return "Memory is currently empty, Sir."

            return str(memory)

        # --------------------
        # AI RESPONSE
        # --------------------

        # Utilizing the centralized model variable exported from config/api_keys.py
        response = client.chat.completions.create(
            model=JARVIS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": command
                }
            ],
            temperature=0.7
        )

        answer = response.choices[0].message.content

        return answer

    except Exception as e:

        return f"Error: {str(e)}"


# Test Mode

if __name__ == "__main__":

    print("JARVIS AI ONLINE")

    while True:

        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            break

        reply = process_command(user_input)

        print(f"\nJarvis: {reply}")