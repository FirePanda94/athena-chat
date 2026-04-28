**Athena**

An AI assistant built with a multi-agent architecture. Athena routes user queries to specialized agents for research, math, code, and planning — and streams the entire thought process back to the user in real time.

**Live:** athena-chat-five.vercel.app

**What it does**

Answers research questions using live web search via Tavily
Solves math problems with a dedicated math agent
Writes and explains Python code
Breaks down complex tasks using a planner agent that decomposes them into ordered subtasks
Streams the supervisor's reasoning, agent delegation, observations, and final response to the frontend in real time
Persists conversation history per user with a sidebar for past chats
Protects all routes with JWT auth (access token in memory, refresh token in httpOnly cookie)
Guards inputs and outputs with LLM-based classifiers to block harmful content and sanitize responses
Rate limits chat requests per user
