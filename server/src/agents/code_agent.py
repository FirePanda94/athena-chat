from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage
from src.utils.llm import get_llm
from src.prompts.code_agent import code_prompt
from fastmcp import Client

MCP_SERVER = {
    "python-sandbox": {
        "transport": "stdio",
        "command": "python",
        "args": ["src/mcp_servers/python_sandbox.py"],
    }
}

MAX_RETRIES = 3

class CodeOutput(BaseModel):
    explanation: str = Field(description="Brief explanation of the code and approach")
    code: Optional[str] = Field(default=None, description="Python code to execute. Null if no code is needed.")
    packages: list[str] = Field(default=[], description="List of pip packages required to run the code e.g. ['yfinance', 'pandas']")

async def run_code_agent(task: str, model_name: str = "qwen-7b-instruct") -> str:
    print(f"[code_agent] Task received: {task}")

    llm = get_llm(model_name)
    structured_llm = llm.with_structured_output(CodeOutput)
    chain = code_prompt | structured_llm

    # Initial generation
    result: CodeOutput = await chain.ainvoke({"messages": [HumanMessage(content=task)]})
    print(f"[code_agent] Code block present: {bool(result.code)}")

    if not result.code:
        print("[code_agent] No code block, returning explanation only")
        return result.explanation

    messages = [HumanMessage(content=task)]

    for attempt in range(MAX_RETRIES):
        print(f"[code_agent] Attempt {attempt + 1} — executing code...")
        print(f"[code_agent] Packages: {result.packages}")
        print(f"[code_agent] Code:\n{result.code}")

        try:
            async with Client(MCP_SERVER) as client:
                output = await client.call_tool("run_python_code", {
                    "code": result.code,
                    "packages": result.packages
                })
                execution_result = output.content[0].text if output.content else "No output"
                print(f"[code_agent] Execution result: {execution_result}")

            # Check if execution itself returned an error
            if execution_result.lower().startswith("error"):
                raise RuntimeError(execution_result)

            # Success
            return (
                f"{result.explanation}\n\n"
                f"```python\n{result.code}\n```\n\n"
                f"**Execution Output:**\n```\n{execution_result}\n```"
            )

        except Exception as e:
            error_msg = str(e)
            print(f"[code_agent] Error on attempt {attempt + 1}: {error_msg}")

            if attempt + 1 == MAX_RETRIES:
                return (
                    f"{result.explanation}\n\n"
                    f"```python\n{result.code}\n```\n\n"
                    f"**Execution failed after {MAX_RETRIES} attempts:**\n```\n{error_msg}\n```"
                )

            # Feed error back to LLM to fix
            print(f"[code_agent] Asking LLM to fix the error...")
            messages = messages + [
                AIMessage(content=f"```python\n{result.code}\n```"),
                HumanMessage(content=(
                    f"That code failed with this error:\n\n{error_msg}\n\n"
                    f"Fix the code and try a different approach."
                ))
            ]
            result = await chain.ainvoke({"messages": messages})