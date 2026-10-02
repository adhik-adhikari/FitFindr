"use client";

import { useEffect, useState } from "react";

type HealthState = "checking" | "connected" | "unavailable" | "unconfigured";

export default function Home() {
  const [health, setHealth] = useState<HealthState>(
    process.env.NEXT_PUBLIC_API_URL ? "checking" : "unconfigured",
  );

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) return;

    const controller = new AbortController();
    const checkHealth = async () => {
      try {
        const response = await fetch(`${apiUrl.replace(/\/$/, "")}/health`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Health request failed");
        const result: unknown = await response.json();
        if (
          typeof result !== "object" ||
          result === null ||
          !("status" in result) ||
          result.status !== "ok"
        ) {
          throw new Error("Unexpected health response");
        }
        setHealth("connected");
      } catch {
        if (!controller.signal.aborted) setHealth("unavailable");
      }
    };

    void checkHealth();
    return () => controller.abort();
  }, []);

  const message = {
    checking: "Checking backend connection…",
    connected: "Backend connected",
    unavailable: "Backend unavailable. Check that it is running and CORS is configured.",
    unconfigured: "Set NEXT_PUBLIC_API_URL to connect to the backend.",
  }[health];

  return (
    <main>
      <h1>FitFindr</h1>
      <p>Project walking skeleton</p>
      <p role="status" aria-live="polite">{message}</p>
    </main>
  );
}
