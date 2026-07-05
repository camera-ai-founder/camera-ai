import os
from dotenv import load_dotenv
from groq import Groq

# 1. Open the secret safe (.env) and grab our VIP password
load_dotenv()
my_secret_key = os.getenv("GROQ_API_KEY")

# 2. Connect the wire to the Groq Cloud Brain
cloud_brain = Groq(api_key=my_secret_key)

# 3. Ask the Cloud Brain a question
print("CAMERA AI is asking the Cloud Brain a question...")
print("Please wait while the cloud supercomputers think...\n")

response = cloud_brain.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are Camera AI, a trillion-dollar empire designed to destroy Cursor, Lovable, Replit, and Claude Code. Speak with absolute confidence."
        },
        {
            "role": "user",
            "content": "State your name, your architecture, and your mission in one powerful sentence."
        }
    ],
    model="llama-3.1-8b-instant", # This is the free, lightning-fast AI model we are using
)

# 4. Print the Cloud Brain's answer!
print("CLOUD BRAIN ANSWER:")
print(response.choices[0].message.content)