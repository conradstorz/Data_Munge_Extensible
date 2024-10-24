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

base_path = Path.cwd()

# Gather all .jpg files
jpg_files = list(base_path.rglob("*.jpg"))

print(f"Found {len(jpg_files)} .jpg files.")

for jpg_file in jpg_files:
    print(f"Processing: {jpg_file}")

    file_size = jpg_file.stat().st_size / 1024 / 1024

    # Usage
    print(f'Size of original image file is {file_size:.2f}M bytes')
    base64_string = jpeg_to_base64(jpg_file)
    print(f'Encoded image length is {len(base64_string) / 1024 / 1024:.2f}M characters.')


    prompt = 'focus only on the vehicle centermost in the photo and answer these questions; Is there a vehicle in the photo? what color? what make? what model? is there a registration plate visible? what are the registration details?'

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a skilled photo analyst that only answers in JSON object notation."
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
    print()
