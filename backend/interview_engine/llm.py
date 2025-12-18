import os
from langchain.chat_models import init_chat_model


API_KEY = os.environ.get("OPENAI_API_KEY")

LLM = init_chat_model(
    "gpt-5-nano",          # or "gpt-5-nano" 등
    api_key=API_KEY,        # 명시적으로 박아두면 더 깔끔
)

