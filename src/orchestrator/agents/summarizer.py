from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_p0_tasks(task_text: str) -> str:
    prompt = (
        "You are an executive assistant. Summarize the following list of P0 tasks into a short, actionable digest.\n\n"
        f"{task_text}\n\n"
        "Output a concise bullet point summary for reporting to your manager."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()
