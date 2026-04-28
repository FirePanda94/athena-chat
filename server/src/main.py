from fastapi import FastAPI, Query, Depends, Request
from src.services.db import connect_db, disconnect_db
import src.services.db as db
from contextlib import asynccontextmanager
from src.auth.router import router as auth_router
from src.conversations.router import router as conversations_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from src.agents.supervisor import build_supervisor
from src.auth.dependancies import get_current_user
from src.config.index import appConfig
from typing import Optional
from uuid import uuid4
import json
from src.utils.rate_limiter import check_rate_limit
from src.guardrails.input_guard import check_input
from src.guardrails.output_guard import check_output

@asynccontextmanager
async def lifespan(app):
    await connect_db()

    async with AsyncConnectionPool(
        conninfo=appConfig['database_url'],
        max_size=10,
        kwargs={"autocommit": True}
    ) as pool_pg:
        checkpointer = AsyncPostgresSaver(pool_pg)
        await checkpointer.setup()
        app.state.graph = build_supervisor(checkpointer)
        yield

    await disconnect_db()

AGENT_LABELS = {
    "research_agent": "Research agent",
    "math_agent":     "Math agent",
    "code_agent":     "Code agent",
    "planner_agent":  "Planner agent",
}

async def generate_chat_responses(
    request: Request,
    message: str,
    user_id: str,
    thread_id: Optional[str] = None,
    model: str = "qwen-7b-instruct"
):
    guard = await check_input(message)
    if not guard.safe:
        yield f"data: {json.dumps({'type': 'blocked', 'reason': guard.reason})}\n\n"
        yield f"data: {json.dumps({'type': 'end'})}\n\n"
        return
    graph = request.app.state.graph
    is_new = thread_id is None
    config = {
        "configurable": {
            "thread_id": str(uuid4()) if is_new else thread_id,
            "model": model
        }
    }

    if is_new:
        new_thread_id = config["configurable"]["thread_id"]
        title = message[:60] + ("..." if len(message) > 60 else "")
        await db.pool.execute(
            """
            INSERT INTO conversations (thread_id, user_id, title)
            VALUES ($1, $2, $3)
            """,
            new_thread_id, user_id, title
        )
        yield f"data: {json.dumps({'type': 'thread_id', 'thread_id': new_thread_id})}\n\n"

    events = graph.astream_events(
        {"messages": [HumanMessage(content=message)]},
        version="v2",
        config=config
    )

    seen_supervisor_run_ids = set()

    async for event in events:
        event_type = event["event"]
        metadata = event.get("metadata", {})
        node = metadata.get("langgraph_node", "")
        data = event.get("data", {})
        run_id = event.get("run_id", "")
        event_name = event.get("name", "")

        if event_type == "on_chain_start" and node == "supervisor" and event_name == "supervisor":
            if run_id not in seen_supervisor_run_ids:
                seen_supervisor_run_ids.add(run_id)
                yield f"data: {json.dumps({'type': 'thinking'})}\n\n"

        elif event_type == "on_chain_end" and node == "supervisor" and event_name == "supervisor":
            output = data.get("output", {})
            if not isinstance(output, dict):
                continue

            trace = output.get("trace", [])
            if not trace:
                continue

            last_step = trace[-1]

            yield f"data: {json.dumps({'type': 'thought', 'content': last_step['thought']})}\n\n"

            if last_step.get("action"):
                label = AGENT_LABELS.get(last_step["action"], last_step["action"])
                yield f"data: {json.dumps({'type': 'action', 'content': f'Calling {label}', 'task': last_step.get('action_input', '')})}\n\n"
                yield f"data: {json.dumps({'type': 'delegation', 'content': f'Delegating to {label}', 'task': last_step.get('action_input', '')})}\n\n"

            messages = output.get("messages", [])
            if messages:
                final_content = messages[-1].content
                if final_content:
                    yield f"data: {json.dumps({'type': 'writing'})}\n\n"
                    guard = await check_output(final_content)
                    if not guard.safe and guard.sanitized:
                        final_content = guard.sanitized
                    yield f"data: {json.dumps({'type': 'content', 'content': final_content})}\n\n"

        elif event_type == "on_chain_end" and node in AGENT_LABELS and event_name == node:
            output = data.get("output", {})
            if not isinstance(output, dict):
                continue

            label = AGENT_LABELS[node]

            if node == "planner_agent":
                plan_data = output.get("plan_data")
                if plan_data:
                    yield f"data: {json.dumps({'type': 'plan', 'reasoning': plan_data['reasoning'], 'subtasks': plan_data['subtasks']})}\n\n"
                yield f"data: {json.dumps({'type': 'agent_done', 'content': f'{label} done'})}\n\n"

            else:
                trace = output.get("trace", [])
                observation = trace[-1].get("observation", "") if trace else ""
                yield f"data: {json.dumps({'type': 'agent_done', 'content': f'{label} done'})}\n\n"
                if observation:
                    yield f"data: {json.dumps({'type': 'observation', 'content': observation})}\n\n"

        elif event_type == "on_tool_start":
            tool_name = event.get("name", "")
            tool_input = data.get("input", {})

            if tool_name == "tavily_search_results_json":
                query = tool_input.get("query", "")
                yield f"data: {json.dumps({'type': 'tool_call', 'content': f'Searching: {query}'})}\n\n"

            elif tool_name == "calculator":
                expression = tool_input.get("expression", "")
                yield f"data: {json.dumps({'type': 'tool_call', 'content': f'Calculating: {expression}'})}\n\n"

        elif event_type == "on_tool_end":
            tool_name = event.get("name", "")
            output = data.get("output", "")

            if tool_name == "tavily_search_results_json":
                if isinstance(output, list):
                    urls = [item["url"] for item in output if "url" in item][:4]
                    if urls:
                        yield f"data: {json.dumps({'type': 'reading', 'urls': urls})}\n\n"

    yield f"data: {json.dumps({'type': 'end'})}\n\n"


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://athena-chat-five.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)

@app.get("/conversations/{thread_id}/messages")
async def get_conversation_messages(
    thread_id: str,
    request: Request,
    current_user=Depends(get_current_user)
):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)

    messages = []
    for msg in state.values.get("messages", []):
        if msg.type == "human":
            # Skip internal observation messages injected by agents
            if "Observation from" in msg.content:
                continue
            messages.append({"role": "user", "content": msg.content})
        elif msg.type == "ai" and msg.content:
            messages.append({"role": "ai", "content": msg.content})

    return messages

@app.get("/chat_stream/{message}")
async def chat_stream(
    message: str,
    request: Request,
    thread_id: Optional[str] = Query(None),
    model: Optional[str] = Query("qwen-7b-instruct"),
    current_user = Depends(get_current_user)
    
):
    check_rate_limit(str(current_user["id"]))
    return StreamingResponse(
        generate_chat_responses(request, message, current_user["id"], thread_id, model),
        media_type="text/event-stream"
    )

app.include_router(auth_router, prefix="/auth")
app.include_router(conversations_router)