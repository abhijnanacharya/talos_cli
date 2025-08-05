from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_p0_tasks(emails, batch_size=40):
    """
    Accepts list of (subject, body) tuples.
    Returns a combined summary of P0 tasks extracted via GPT in batches.
    """
    if not emails:
        return "No emails to process."

    summaries = []

    for i in range(0, len(emails), batch_size):
        batch = emails[i:i + batch_size]
        print(f"🔄 Processing batch {i // batch_size + 1} ({len(batch)} emails)...")

        prompt = (
            "You are an executive assistant. Your job is to extract only high-priority (P0) tasks from emails. "
            "Format the output clearly using bullet points. Ignore marketing/newsletters.\n\n"
        )

        for idx, (subject, body) in enumerate(batch, 1):
            prompt += f"\n--- EMAIL {idx} ---\n"
            prompt += f"Subject: {subject}\n"
            prompt += f"Body:\n{body[:1000]}\n"  # Reduce token load

        prompt += (
            "\n\nRespond ONLY with P0 tasks in bullet points. If no P0 task, return 'No P0 tasks found.' "
            "Remember: any Job Application related tasks (successful ones or those requiring action) are P0.\n"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            summaries.append(response.choices[0].message.content.strip())
        except Exception as e:
            summaries.append(f"[ERROR PROCESSING BATCH {i // batch_size + 1}]: {e}")
            continue

    return "\n\n".join(summaries)
