"use client";

import { useUserState } from "@/lib/user-state";

interface SubscribeButtonProps {
  creatorId: string;
  size?: "sm" | "md";
}

export function SubscribeButton({ creatorId, size = "md" }: SubscribeButtonProps) {
  const { isSubscribed, toggleSubscription } = useUserState();
  const subscribed = isSubscribed(creatorId);

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleSubscription(creatorId);
      }}
      className={`btn-subscribe ${subscribed ? "subscribed" : ""} ${
        size === "sm" ? "text-xs px-3 py-1" : "text-sm"
      }`}
    >
      {subscribed ? "Subscribed" : "Subscribe"}
    </button>
  );
}
