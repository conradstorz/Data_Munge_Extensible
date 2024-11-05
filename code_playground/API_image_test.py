from openai import OpenAI
from dotenv import dotenv_values

SECRETS = dotenv_values('ChatGPT_and_Twilio.env')  # load secrets from '.env' file
openai_api_key = SECRETS["openai.api_key"]

OpenAI_client = OpenAI(
    # This is the default and can be omitted
    api_key=openai_api_key,
)
 
import base64

def jpeg_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# setup logging
import load_loguru_logging_defaults  # file will process automatically on import
from loguru import logger
logger.info(f'Program start...')


from pathlib import Path

base_path = Path.cwd()
logger.debug(f'Current working directory {base_path}')


# Gather all .jpg files
jpg_files = list(base_path.rglob("*.jpg"))
logger.info(f'{len(jpg_files)} photo files found.')

for jpg_file in jpg_files:
    logger.info(f"Processing: {jpg_file}")

    file_size = jpg_file.stat().st_size / 1024 / 1024

    # Usage
    logger.info(f'Size of original image file is {file_size:.2f}M bytes')
    base64_string = jpeg_to_base64(jpg_file)
    logger.info(f'Encoded image length is {len(base64_string) / 1024 / 1024:.2f}M characters.')


    prompt = 'focus only on the vehicle centermost in the photo and answer these questions; Is there a vehicle in the photo? what color? what make? what model? is there a registration plate visible? what are the registration details?'

    response = OpenAI_client.chat.completions.create(
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

    # now extract the analysis from the response
    answer = response.choices[0].message.content
    logger.info(answer)



"""
Here's an example of async useage
import os
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


async def main() -> None:
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-3.5-turbo",
    )


asyncio.run(main())

could this be used to submit all photos at once and get results as they become available?
"""