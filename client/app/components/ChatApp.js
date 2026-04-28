"use client";

import { useState, useRef } from "react";
import Sidebar from "./Sidebar";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { streamChat } from "../utils/chat";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/apiClient";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Morning";
  if (hour < 17) return "Afternoon";
  return "Evening";
}

export default function ChatApp() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("qwen-7b-instruct");
  const contentRef = useRef("");
  const modelRef = useRef("qwen-7b-instruct");
  const stepsRef = useRef([]);
  const { user } = useAuth();

  function handleModelChange(model) {
    setSelectedModel(model);
    modelRef.current = model;
  }

  function handleNewChat() {
    setMessages([]);
    setInput("");
    setThreadId(null);
    contentRef.current = "";
    stepsRef.current = [];
  }

  async function handleSelectConversation(selectedThreadId) {
    handleNewChat();
    setThreadId(selectedThreadId);
    try {
      const res = await apiClient(
        `/conversations/${selectedThreadId}/messages`,
      );
      const history = await res.json();
      setMessages(history);
    } catch (e) {
      console.error("Failed to load conversation history", e);
    }
  }

  async function handleSend() {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    contentRef.current = "";
    stepsRef.current = [];
    try {
      await streamChat(
        input,
        threadId,
        modelRef.current,
        (chunk) => {
          contentRef.current += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "ai") {
              updated[updated.length - 1] = {
                ...last,
                content: contentRef.current,
              };
            } else {
              updated.push({ role: "ai", content: contentRef.current });
            }
            return updated;
          });
        },
        (newThreadId) => {
          setThreadId(newThreadId);
        },
        (step) => {
          stepsRef.current = [...stepsRef.current, step];
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "steps") {
              updated[updated.length - 1] = {
                ...last,
                steps: stepsRef.current,
              };
            } else {
              updated.push({ role: "steps", steps: stepsRef.current });
            }
            return updated;
          });
        },
      );
    } catch (e) {
      if (e.status === 429) {
        setMessages((prev) => [
          ...prev,
          {
            role: "ai",
            content: "You're sending messages too fast. Please wait a moment.",
          },
        ]);
      }
    }

    setIsLoading(false);
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-screen bg-[#1e1e1e] text-white">
      <Sidebar
        activeThreadId={threadId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
      />

      <div className="flex flex-col flex-1 min-w-0">
        {!hasMessages ? (
          <main className="flex flex-col items-center justify-center flex-1 gap-8">
            <h1
              className="text-4xl font-semibold"
              style={{ fontFamily: "var(--font-source-serif-4)" }}
            >
              {getGreeting()}, {user?.email?.split("@")[0]}
            </h1>
            <MessageInput
              input={input}
              setInput={setInput}
              onSend={handleSend}
              isLoading={isLoading}
              selectedModel={selectedModel}
              setSelectedModel={handleModelChange}
            />
          </main>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-2xl mx-auto w-full">
                <MessageList messages={messages} />
              </div>
            </div>
            <div className="p-4">
              <MessageInput
                input={input}
                setInput={setInput}
                onSend={handleSend}
                isLoading={isLoading}
                selectedModel={selectedModel}
                setSelectedModel={handleModelChange}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
