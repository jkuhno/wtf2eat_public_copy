from langchain_openai import ChatOpenAI # type: ignore
import os

def get_chat_model(model_name, temperature):
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ.get("GROQ_API_KEY")
    )
    return llm