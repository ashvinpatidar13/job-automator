import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

msg = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    messages=[{"role": "user", "content": 'Return ONLY this JSON, no markdown: {"fit_score": 80}'}]
)

print(repr(msg.content[0].text))