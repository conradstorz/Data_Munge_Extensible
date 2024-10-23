import openai
from dotenv import dotenv_values

SECRETS = dotenv_values('ChatGPT.env')  # load secrets from '.env' file
openai.api_key = SECRETS["openai.api_key"]


def test_openai_api():
    try:
        # Example API call: Chat completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a short story about a robot learning to dance."}
            ],
            max_tokens=50
        )
        print("API Response:")
        print(response['choices'][0]['message']['content'].strip())
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_openai_api()

