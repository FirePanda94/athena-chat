from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.tools.search import search_tool
from src.prompts.research_agent import research_prompt
from src.utils.llm import get_llm

async def run_research_agent(task: str, model_name: str = "qwen-7b-instruct") -> str:
    llm = get_llm(model_name)
    llm_with_tools = llm.bind_tools(tools=[search_tool])
    chain = research_prompt | llm_with_tools

    messages = [HumanMessage(content=task)]
    max_iterations = 2
    iteration = 0

    while iteration < max_iterations:
        response = await chain.ainvoke({"messages": messages})
        messages.append(response)
        iteration += 1

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            result = await search_tool.ainvoke(tool_call["args"])
            raw = str(result)[:3000]
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": raw
            })

    summary_llm = get_llm(model_name)
    summary = await summary_llm.ainvoke([
        SystemMessage(content="You are a summarizer. Summarize the following research findings in 3-5 concise sentences. Only include the key facts."),
        HumanMessage(content=response.content)
    ])

    return summary.content