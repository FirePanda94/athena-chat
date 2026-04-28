from langchain_core.messages import HumanMessage
from src.tools.calculator import calculator
from src.prompts.math_agent import math_prompt
from dotenv import load_dotenv
from src.utils.llm import get_llm
import warnings
warnings.filterwarnings("ignore")
load_dotenv()



async def run_math_agent(task: str, model_name: str = "qwen-7b-instruct") -> str:
    llm = get_llm(model_name)
    llm_with_tools = llm.bind_tools(tools=[calculator])
    chain = math_prompt | llm_with_tools

    messages = [HumanMessage(content=task)]

    while True:
        response = await chain.ainvoke({"messages": messages})
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            result = await calculator.ainvoke(tool_call["args"])
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": str(result)
            })

    return response.content