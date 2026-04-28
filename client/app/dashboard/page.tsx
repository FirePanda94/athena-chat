"use client";

import { useRequireAuth } from "@/hooks/useRequireAuth";
import ChatApp from "@/app/components/ChatApp";

export default function Dashboard() {
  useRequireAuth();
  return <ChatApp />;
}
