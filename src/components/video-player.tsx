"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import Hls from "hls.js";
import { formatDuration } from "@/lib/utils";

interface VideoPlayerProps {
  hlsUrl?: string;
  thumbnailUrl: string;
  title: string;
  duration: number;
  startTime?: number;
}

export interface VideoPlayerHandle {
  /**
   * Jump the player to `time` (seconds). Starts playback if currently paused
   * on the poster. If HLS hasn't been mounted yet (cold first click), the
   * pending start position is captured for the upcoming `loadSource` call.
   */
  seekTo: (time: number) => void;
}

export const VideoPlayer = forwardRef<VideoPlayerHandle, VideoPlayerProps>(
  function VideoPlayer(
    { hlsUrl, thumbnailUrl, title, duration, startTime = 0 },
    ref,
  ) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [playing, setPlaying] = useState(startTime > 0);
    const [error, setError] = useState(false);
    // Captures the position that the next HLS init should start from.
    // Seeded with the URL ?t= param; chapter clicks while still on the poster
    // overwrite it before flipping `playing` to true.
    const initialSeekRef = useRef<number>(startTime);

    useEffect(() => {
      const video = videoRef.current;
      if (!video || !hlsUrl || !playing) return;

      const startPos = initialSeekRef.current;
      let hls: Hls | null = null;

      if (video.canPlayType("application/vnd.apple.mpegurl")) {
        // Safari — native HLS support
        video.src = hlsUrl;
        if (startPos > 0) video.currentTime = startPos;
        video.play();
      } else if (Hls.isSupported()) {
        hls = new Hls({ startPosition: startPos > 0 ? startPos : -1 });
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

    useImperativeHandle(
      ref,
      () => ({
        seekTo(time: number) {
          if (!hlsUrl) return;
          const video = videoRef.current;
          if (playing && video) {
            video.currentTime = time;
            void video.play().catch(() => {});
          } else {
            initialSeekRef.current = time;
            setPlaying(true);
          }
        },
      }),
      [hlsUrl, playing],
    );

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
  },
);
