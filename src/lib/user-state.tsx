"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import type { UserState } from "./types";

interface UserStateContextValue extends UserState {
  toggleSubscription: (creatorId: string) => void;
  isSubscribed: (creatorId: string) => boolean;
  markWatched: (videoId: string) => void;
  hasWatched: (videoId: string) => boolean;
  reset: () => void;
}

const STORAGE_KEY = "substack-rec-user-state";

const defaultState: UserState = {
  subscriptions: ["lex", "colin-samir", "vox-earworm"],
  watchHistory: [],
};

const UserStateContext = createContext<UserStateContextValue | null>(null);

export function UserStateProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<UserState>(defaultState);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setState(JSON.parse(stored));
    } catch {}
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }
  }, [state, hydrated]);

  const toggleSubscription = useCallback((creatorId: string) => {
    setState((prev) => ({
      ...prev,
      subscriptions: prev.subscriptions.includes(creatorId)
        ? prev.subscriptions.filter((id) => id !== creatorId)
        : [...prev.subscriptions, creatorId],
    }));
  }, []);

  const isSubscribed = useCallback(
    (creatorId: string) => state.subscriptions.includes(creatorId),
    [state.subscriptions],
  );

  const markWatched = useCallback((videoId: string) => {
    setState((prev) => ({
      ...prev,
      watchHistory: prev.watchHistory.includes(videoId)
        ? prev.watchHistory
        : [...prev.watchHistory, videoId],
    }));
  }, []);

  const hasWatched = useCallback(
    (videoId: string) => state.watchHistory.includes(videoId),
    [state.watchHistory],
  );

  const reset = useCallback(() => {
    setState(defaultState);
  }, []);

  if (!hydrated) {
    return <div className="min-h-screen bg-[var(--bg-primary)]" />;
  }

  return (
    <UserStateContext.Provider
      value={{ ...state, toggleSubscription, isSubscribed, markWatched, hasWatched, reset }}
    >
      {children}
    </UserStateContext.Provider>
  );
}

export function useUserState(): UserStateContextValue {
  const ctx = useContext(UserStateContext);
  if (!ctx) throw new Error("useUserState must be used within UserStateProvider");
  return ctx;
}
