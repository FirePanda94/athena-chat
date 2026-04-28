const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export async function apiClient(url: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    const refreshResponse = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });

    if (!refreshResponse.ok) {
      window.location.href = "/auth/login";
      return response;
    }

    const { access_token } = await refreshResponse.json();
    setAccessToken(access_token);
    const retryHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };
    if (access_token) {
      retryHeaders["Authorization"] = `Bearer ${access_token}`;
    }

    const retryResponse = await fetch(`${BASE_URL}${url}`, {
      ...options,
      headers: retryHeaders,
    });
    return retryResponse;
  }
  return response;
}
