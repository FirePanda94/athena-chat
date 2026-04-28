import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_URL;

export async function POST(request: NextRequest) {
  const { email, password } = await request.json();

  const backendResponse = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!backendResponse.ok) {
    const errorData = await backendResponse.json();
    return NextResponse.json(errorData, { status: backendResponse.status });
  }

  const { access_token, refresh_token } = await backendResponse.json();

  const response = NextResponse.json({ access_token });

  response.cookies.set({
    name: "refresh_token",
    value: refresh_token,
    httpOnly: true,
    secure: true,
    sameSite: "strict",
    path: "/",
  });

  return response;
}
