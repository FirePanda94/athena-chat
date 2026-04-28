import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_URL;

export async function POST(request: NextRequest) {
  console.log("API_BASE_URL:", API_BASE_URL);

  const { email, password } = await request.json();
  const backendResponse = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  console.log("Backend status:", backendResponse.status);
  const data = await backendResponse.json();
  console.log("Backend response:", data);

  if (!backendResponse.ok) {
    return NextResponse.json(data, { status: backendResponse.status });
  }

  return NextResponse.json(data, { status: 201 });
}
