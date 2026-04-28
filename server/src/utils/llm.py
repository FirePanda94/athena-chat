from langchain_openai import ChatOpenAI
def get_llm(model_name: str):
    if model_name == "gpt-4o-mini":
        return ChatOpenAI(model="gpt-4.1-2025-04-14", temperature=0)
    else:
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)