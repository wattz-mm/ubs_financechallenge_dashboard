import type { DashboardPayload } from "./types";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export async function fetchDashboard(): Promise<DashboardPayload> {
  const response = await fetch(`${BASE}/api/dashboard`);
  if (!response.ok) {
    throw new Error(`Dashboard request failed: ${response.status}`);
  }
  return response.json();
}

export async function refreshIngestion(): Promise<void> {
  const response = await fetch(`${BASE}/api/ingest/run`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Refresh failed: ${response.status}`);
  }
}

export async function fetchPptReady(): Promise<unknown> {
  const response = await fetch(`${BASE}/api/export/ppt-ready`);
  if (!response.ok) {
    throw new Error(`Export failed: ${response.status}`);
  }
  return response.json();
}

