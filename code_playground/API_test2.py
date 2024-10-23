from openai import OpenAI
from dotenv import dotenv_values

SECRETS = dotenv_values('ChatGPT_and_Twilio.env')  # load secrets from '.env' file
openai_api_key = SECRETS["openai.api_key"]

client = OpenAI(
    # This is the default and can be omitted
    api_key=openai_api_key,
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "write a haiku",
        }
    ],
    model="gpt-3.5-turbo",
)

print(chat_completion)