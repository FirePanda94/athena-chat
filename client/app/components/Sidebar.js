"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/apiClient";

export default function Sidebar({
  activeThreadId,
  onSelectConversation,
  onNewChat,
}) {
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    async function fetchConversations() {
      try {
        const res = await apiClient("/conversations");
        const data = await res.json();
        setConversations(data);
      } catch (err) {
        console.error("Failed to fetch conversations", err);
      }
    }
    fetchConversations();
  }, [activeThreadId]); // refetch when a new conversation is created

  return (
    <aside className="w-64 h-screen bg-[#171717] border-r border-[#2a2a2a] flex flex-col shrink-0">
      <div className="px-4 py-4 border-b border-[#2a2a2a] flex items-center justify-between">
        <span className="text-white font-semibold text-lg">Athena</span>
        <button
          onClick={onNewChat}
          className="text-gray-400 hover:text-white transition-colors text-xl leading-none"
          title="New chat"
        >
          +
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {conversations.length === 0 ? (
          <p className="text-gray-600 text-xs px-4 py-3">
            No conversations yet
          </p>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.thread_id}
              onClick={() => onSelectConversation(conv.thread_id)}
              className={`w-full text-left px-4 py-2.5 hover:bg-[#2a2a2a] transition-colors ${
                activeThreadId === conv.thread_id ? "bg-[#2a2a2a]" : ""
              }`}
            >
              <p
                className={`text-sm truncate ${
                  activeThreadId === conv.thread_id
                    ? "text-white"
                    : "text-gray-400"
                }`}
              >
                {conv.title}
              </p>
              <p className="text-xs text-gray-600 mt-0.5">
                {new Date(conv.created_at).toLocaleDateString()}
              </p>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
