import { NextRequest, NextResponse } from "next/server";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (refreshToken) {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  const response = NextResponse.json(
    { message: "logged out" },
    { status: 200 },
  );

  response.cookies.set({
    name: "refresh_token",
    value: "",
    maxAge: 0,
    path: "/",
  });

  return response;
}
