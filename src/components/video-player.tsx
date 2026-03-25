"use client";

import { useRef, useEffect, useState } from "react";
import Hls from "hls.js";
import { formatDuration } from "@/lib/utils";

interface VideoPlayerProps {
  hlsUrl?: string;
  thumbnailUrl: string;
  title: string;
  duration: number;
}

export function VideoPlayer({ hlsUrl, thumbnailUrl, title, duration }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !hlsUrl || !playing) return;

    let hls: Hls | null = null;

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // Safari — native HLS support
      video.src = hlsUrl;
      video.play();
    } else if (Hls.isSupported()) {
      hls = new Hls();
      hls.loadSource(hlsUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal) setError(true);
      });
    } else {
      setError(true);
    }

    return () => {
      hls?.destroy();
    };
  }, [hlsUrl, playing]);

  const handlePlay = () => {
    if (!hlsUrl) {
      setError(true);
      return;
    }
    setPlaying(true);
  };

  return (
    <div className="aspect-video rounded-xl overflow-hidden relative bg-black">
      {playing ? (
        <>
          <video
            ref={videoRef}
            className="w-full h-full"
            controls
            poster={thumbnailUrl}
          />
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80">
              <p className="text-sm text-[var(--text-secondary)]">Unable to play video</p>
            </div>
          )}
        </>
      ) : (
        <>
          <img
            src={thumbnailUrl}
            alt={title}
            className="absolute inset-0 w-full h-full object-cover"
          />
          {/* Play button */}
          <button
            onClick={handlePlay}
            className="absolute inset-0 flex items-center justify-center cursor-pointer group"
          >
            <div className="w-16 h-16 rounded-full bg-[var(--accent)] flex items-center justify-center shadow-2xl transition-transform group-hover:scale-110">
              <svg width="24" height="24" viewBox="0 0 16 16" fill="none">
                <path d="M4 2L14 8L4 14V2Z" fill="#1D1C1B" />
              </svg>
            </div>
          </button>
          {/* Duration */}
          <span className="absolute bottom-3 right-3 px-2 py-1 text-xs font-mono bg-black/70 text-[var(--text-primary)] rounded">
            {formatDuration(duration)}
          </span>
        </>
      )}
    </div>
  );
}
