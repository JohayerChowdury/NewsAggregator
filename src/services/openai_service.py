import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

categories = [
    "Government Policy & Regulatory Updates",
    "Financial Incentives & Housing Programs",
    "Industry Innovations & Construction Resources",
    "Community Initiatives & Local Developments",
    "Housing Market Trends & Demographic Insights",
]


class OpenAIService:
    def __init__(self, organization=None, project=None):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.config = {
            "api_key": self.openai_api_key or "doesntmatter",
            "base_url": os.getenv("LLM_ENDPOINT") or "https://api.openai.com/v1",
            "organization": organization or os.getenv("OPENAI_ORGANIZATION"),
            "project": project or os.getenv("OPENAI_PROJECT"),
        }
        self.classification_model = (
            "mistral-nemo:latest" if not self.openai_api_key else "gpt-4o"
        )  # TODO: Confirm if gpt-4o is what is wanted

        self.summarization_model = (
            "mistral-nemo" if not self.openai_api_key else "gpt-4o"
        )
        self.async_openai_client = AsyncOpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"],
            organization=self.config["organization"],
            project=self.config["project"],
        )

    def get_client(self):
        return self.async_openai_client

    async def assign_category(self, text):
        system_prompt = (
            f"You are a strict categorization assistant. You will be given text delimited by triple quotes."
            f"Using the given text, your task is to either return ONLY ONE category from the following list: {' '.join(categories)} or respond with I don't know."
            f"Do not explain your choice. Do not include any other text or punctuation."
        )
        user_prompt = f"Text: '''{text}'''"
        try:
            response = await self.async_openai_client.chat.completions.create(
                stream=False,
                model=self.classification_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=8,
            )
            category = response.choices[0].message.content.strip()
            if not category:
                return None
            return category
        except Exception as e:
            print(f"Error assigning category with OpenAI: {e}")
            return None

    async def generate_summary(self, text, max_tokens=100):
        system_prompt = (
            "You are a strict summarization assistant. You will be given text delimited by triple quotes."
            "Your task is to summarize the text in a concise manner."
        )
        user_prompt = f"Text: '''{text}''' "
        try:
            response = await self.async_openai_client.chat.completions.create(
                stream=False,
                model=self.summarization_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content.strip()
            if not content:
                return None
            return content
        except Exception as e:
            print(f"Error summarizing with OpenAI: {e}")
            return None
