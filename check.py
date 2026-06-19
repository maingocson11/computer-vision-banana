from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

resp = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"user","content":"1+1="}]
)

print(resp.choices[0].message.content)
