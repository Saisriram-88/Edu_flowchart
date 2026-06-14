from google import genai

client = genai.Client(api_key="Keep You API Key here")

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="What is 2 + 2?"
)

print(response.text)