from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def ask_ai(user_message):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
                You are a salon receptionist.

                Extract:
                service
                date
                time

                Return JSON only.
                """
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    return response.choices[0].message.content
