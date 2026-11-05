export type User = {
  id: string;
  email: string;
  display_name: string;
};

export class AuthError extends Error {}

type ErrorBody = { error?: { message?: string } };

async function post(path: string, body?: unknown): Promise<Response> {
  const response = await fetch(path, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = (await response.json().catch(() => ({}))) as ErrorBody;
    throw new AuthError(data.error?.message ?? "Something went wrong. Try again.");
  }
  return response;
}

export async function signUp(email: string, password: string, displayName: string): Promise<User> {
  const response = await post("/v1/auth/signup", { email, password, display_name: displayName });
  return (await response.json()) as User;
}

export async function signIn(email: string, password: string): Promise<User> {
  const response = await post("/v1/auth/login", { email, password });
  return (await response.json()) as User;
}

export async function signOut(): Promise<void> {
  await post("/v1/auth/logout");
}
