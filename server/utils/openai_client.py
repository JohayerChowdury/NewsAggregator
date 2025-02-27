import os
import openai

open_ai_api_key = os.environ.get("OPENAI_API_KEY")
llm_endpoint = os.environ.get("LLM_ENDPOINT")
open_ai_organization = os.environ.get("OPENAI_ORGANIZATION_ID")
open_ai_project = os.environ.get("OPENAI_PROJECT_ID")

# comment out the print statement
print(open_ai_api_key, llm_endpoint, open_ai_organization, open_ai_project)

openai_client = openai.OpenAI(
    api_key=open_ai_api_key,
    base_url=llm_endpoint,
    organization=open_ai_organization,
    project=open_ai_project,
)
