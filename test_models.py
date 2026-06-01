import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

client = genai.Client()
print("Methods in client.models:")
print(dir(client.models))

try:
    models = client.models.list()
    print("\nSupported Models:")
    for m in models:
        if "gemini" in m.name.lower():
            print(m.name)
except Exception as e:
    print(f"Error calling list(): {e}")
