from pydantic import BaseModel, Field
from typing import Optional, Literal, Annotated, TypedDict
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END, add_messages
from src.utils.llm import get_llm
from src.prompts.supervisor import supervisor_prompt
from src.agents.research_agent import run_research_agent
from src.agents.math_agent import run_math_agent
from src.agents.code_agent import run_code_agent
from src.agents.planner_agent import run_planner_agent


# --- Structured Output Schema ---

class SupervisorOutput(BaseModel):
    thought: str = Field(description="Analysis of the user request and plan")
    action_agent: Optional[Literal["research_agent", "math_agent", "code_agent", "planner_agent"]] = Field(
        default=None,
        description="Agent to call. Null if ready to give final response."
    )
    action_input: Optional[str] = Field(
        default=None,
        description="Exact high-context query to send to the agent."
    )
    final_response: Optional[str] = Field(
        default=None,
        description="Final answer to the user. Only fill this when done."
    )


# --- State ---

class TraceStep(TypedDict):
    thought: str
    action: Optional[str]
    action_input: Optional[str]
    observation: Optional[str]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    model: str
    trace: list
    next_agent: Optional[str]
    pending_input: Optional[str]
    iteration_count: int       # hard cap enforcement
    has_planned: bool          # ensures planner is called at most once
    plan_data: Optional[dict]  # serialized plan for frontend rendering


# --- Supervisor Node ---

async def supervisor_node(state: State, config: RunnableConfig) -> dict:
    model_name = config.get("configurable", {}).get("model", "qwen-7b-instruct")
    llm = get_llm(model_name)
    structured_llm = supervisor_prompt | llm.with_structured_output(SupervisorOutput)

    iteration_count = state.get("iteration_count", 0)
    has_planned = state.get("has_planned", False)
    trace = state.get("trace", [])

    # Dynamic cap: 3 if a plan exists (planner takes one slot), 2 otherwise
    max_iterations = 10 if has_planned else 5

    # Hard stop — force final response when cap is reached
    if iteration_count >= max_iterations:
        forced_messages = list(state["messages"]) + [
            HumanMessage(content="You have reached the maximum number of agent calls. Synthesize the best possible answer from the information you have gathered so far and provide a final_response immediately.")
        ]
        result: SupervisorOutput = await structured_llm.ainvoke({"messages": forced_messages})
        result.action_agent = None
        result.action_input = None
    else:
        result: SupervisorOutput = await structured_llm.ainvoke({"messages": state["messages"]})

    # Guard: supervisor tried to call planner again — block it
    if result.action_agent == "planner_agent" and has_planned:
        result.action_agent = None
        result.action_input = None
        result.final_response = result.thought
        result.thought = "Planner already called. Synthesizing from available data."

    if result.final_response:
        trace_step: TraceStep = {
            "thought": result.thought,
            "action": None,
            "action_input": None,
            "observation": None,
        }
        return {
            "messages": [AIMessage(content=result.final_response)],
            "trace": trace + [trace_step],
            "next_agent": None,
            "pending_input": None,
            "iteration_count": iteration_count,
            "has_planned": has_planned,
        }

    trace_step: TraceStep = {
        "thought": result.thought,
        "action": result.action_agent,
        "action_input": result.action_input,
        "observation": None,
    }
    return {
        "trace": trace + [trace_step],
        "next_agent": result.action_agent,
        "pending_input": result.action_input,
        "iteration_count": iteration_count + 1,
        "has_planned": has_planned,
    }


# --- Routing ---

def route_supervisor(state: State) -> str:
    return state.get("next_agent") or END


# --- Helpers ---

def _update_trace_with_observation(trace: list, observation: str) -> list:
    if not trace:
        return trace
    last = dict(trace[-1])
    last["observation"] = observation
    return trace[:-1] + [last]


def _observation_message(agent_name: str, result: str) -> str:
    """
    Wraps the agent result in a directive so weak models know to stop calling
    agents and emit a final_response on the next supervisor turn.
    """
    return (
        f"Observation from {agent_name}: {result}\n\n"
        "You now have the information needed to answer the user. "
        "Set final_response with a complete answer and leave action_agent empty."
    )


# --- Agent Nodes ---

async def research_node(state: State, config: RunnableConfig) -> dict:
    model_name = config.get("configurable", {}).get("model", "qwen-7b-instruct")
    result = await run_research_agent(state.get("pending_input", ""), model_name)
    return {
        "messages": [HumanMessage(content=_observation_message("research_agent", result))],
        "trace": _update_trace_with_observation(state.get("trace", []), result),
        "next_agent": None,
        "pending_input": None,
    }


async def math_node(state: State, config: RunnableConfig) -> dict:
    model_name = config.get("configurable", {}).get("model", "qwen-7b-instruct")
    result = await run_math_agent(state.get("pending_input", ""), model_name)
    return {
        "messages": [HumanMessage(content=_observation_message("math_agent", result))],
        "trace": _update_trace_with_observation(state.get("trace", []), result),
        "next_agent": None,
        "pending_input": None,
    }


async def code_node(state: State, config: RunnableConfig) -> dict:
    model_name = config.get("configurable", {}).get("model", "qwen-7b-instruct")
    result = await run_code_agent(state.get("pending_input", ""), model_name)
    return {
        "messages": [HumanMessage(content=_observation_message("code_agent", result))],
        "trace": _update_trace_with_observation(state.get("trace", []), result),
        "next_agent": None,
        "pending_input": None,
    }


async def planner_node(state: State, config: RunnableConfig) -> dict:
    model_name = config.get("configurable", {}).get("model", "qwen-7b-instruct")
    plan = await run_planner_agent(state.get("pending_input", ""), model_name)

    # Serialize plan for frontend rendering
    plan_data = {
        "reasoning": plan.reasoning,
        "subtasks": [
            {
                "order": st.order,
                "description": st.description,
                "suggested_agent": st.suggested_agent,
            }
            for st in plan.subtasks
        ],
    }

    # Plain text observation for the supervisor's message history
    plan_lines = [f"Plan reasoning: {plan.reasoning}", "Subtasks:"]
    for st in plan.subtasks:
        agent_hint = f" → suggested: {st.suggested_agent}" if st.suggested_agent else ""
        plan_lines.append(f"  {st.order}. {st.description}{agent_hint}")
    plan_text = "\n".join(plan_lines)

    return {
        "messages": [HumanMessage(
            content=(
                f"Observation from planner_agent:\n{plan_text}\n\n"
                "Now execute the subtasks in order using the suggested agents."
            )
        )],
        "trace": _update_trace_with_observation(state.get("trace", []), plan_text),
        "next_agent": None,
        "pending_input": None,
        "has_planned": True,
        "plan_data": plan_data,
    }


# --- Graph ---

def build_supervisor(checkpointer):
    graph = StateGraph(State)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research_agent", research_node)
    graph.add_node("math_agent", math_node)
    graph.add_node("code_agent", code_node)
    graph.add_node("planner_agent", planner_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", route_supervisor, {
        "research_agent": "research_agent",
        "math_agent":     "math_agent",
        "code_agent":     "code_agent",
        "planner_agent":  "planner_agent",
        END:              END,
    })
    graph.add_edge("research_agent", "supervisor")
    graph.add_edge("math_agent",     "supervisor")
    graph.add_edge("code_agent",     "supervisor")
    graph.add_edge("planner_agent",  "supervisor")

    return graph.compile(checkpointer=checkpointer)