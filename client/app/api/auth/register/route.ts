import { NextRequest, NextResponse } from "next/server";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export async function POST(request: NextRequest) {
  const { email, password } = await request.json();

  const backendResponse = await fetch(`${API_BASE_URL}/auth/register`, {
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

  const data = await backendResponse.json();
  return NextResponse.json(data, { status: 201 });
}
