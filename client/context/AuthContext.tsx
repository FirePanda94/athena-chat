"use client";
import React, { useState, useContext, useEffect, useCallback } from "react";
import { setAccessToken as setClientToken, apiClient } from "@/lib/apiClient";

interface AuthContextType {
  accessToken: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  user: { email: string } | null;
}

const AuthContext = React.createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<{ email: string } | null>(null);

  async function login(email: string, password: string) {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Login failed");
    }

    setAccessToken(data.access_token);
    setClientToken(data.access_token);

    const meResponse = await apiClient("/me");
    const userData = await meResponse.json();
    setUser(userData);
  }

  async function logout() {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
      });
      setAccessToken(null);
      setClientToken(null);
      setUser(null);
      window.location.href = "/auth/login";
    } catch {}
  }

  const refreshToken = useCallback(async () => {
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) {
      setAccessToken(null);
      setClientToken(null);
      return;
    }
    const { access_token } = await response.json();
    setAccessToken(access_token);
    setClientToken(access_token);

    const meResponse = await apiClient("/me");
    const userData = await meResponse.json();
    setUser(userData);
  }, []);

  useEffect(() => {
    refreshToken().finally(() => setIsLoading(false));
  }, [refreshToken]);

  useEffect(() => {
    setClientToken(accessToken);
  }, [accessToken]);

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        isLoading,
        login,
        logout,
        refreshToken,
        user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

export default AuthContext;
