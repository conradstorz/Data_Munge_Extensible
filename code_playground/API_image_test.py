from openai import OpenAI
from dotenv import dotenv_values

SECRETS = dotenv_values('ChatGPT_and_Twilio.env')  # load secrets from '.env' file
openai_api_key = SECRETS["openai.api_key"]

client = OpenAI(
    # This is the default and can be omitted
    api_key=openai_api_key,
)

import base64

def jpeg_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

from pathlib import Path

file_path = Path('car.jpg')
file_size = file_path.stat().st_size / 1024 / 1024

# Usage
print(f'Size of original image file is {file_size:.2f}M bytes')
base64_string = jpeg_to_base64("car.jpg")
print(f'Encoded image length is {len(base64_string) / 1024 / 1024:.2f}M characters.')

prompt = 'what is this'

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a skilled photo analyst that only answers in iambic pentameter."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"},
                },
            ],
        }
    ],
)

# now extract the Haiku from the response
answer = response.choices[0].message.content
print(answer)
