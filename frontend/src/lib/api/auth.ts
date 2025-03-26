const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function login({ username, password }: { username: string; password: string }) {
  const res = await fetch(`${url}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const data = await res.json();
    throw new Error(data?.detail || "Login failed");
  }

  return true;
}

export async function logout() {
  const res = await fetch(`${url}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error("Logout failed");
  }

  return true;
}
