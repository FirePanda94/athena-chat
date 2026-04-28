from langchain_core.messages import HumanMessage
from src.prompts.planner import planner_prompt
from dotenv import load_dotenv
from src.utils.llm import get_llm
from pydantic import BaseModel, Field
from typing import Literal
import warnings
warnings.filterwarnings("ignore")
load_dotenv()


# ── Pydantic output schema ─────────────────────────────────────────────────────

class SubTask(BaseModel):
    order: int = Field(description="Execution order, starting from 1")
    description: str = Field(description="Clear, self-contained instruction for the agent")
    suggested_agent: Literal["research_agent", "math_agent", "code_agent"] | None = Field(
        default=None,
        description="Best agent for this subtask, or null if the supervisor should decide"
    )

class Plan(BaseModel):
    reasoning: str = Field(description="Why you broke the task down this way")
    subtasks: list[SubTask] = Field(description="Ordered list of subtasks")


# ── Planner agent ──────────────────────────────────────────────────────────────

async def run_planner_agent(task: str, model_name: str = "qwen-7b-instruct") -> Plan:
    llm = get_llm(model_name)
    llm_with_structure = llm.with_structured_output(Plan)
    chain = planner_prompt | llm_with_structure

    messages = [HumanMessage(content=task)]
    plan: Plan = await chain.ainvoke({"messages": messages})

    return plan