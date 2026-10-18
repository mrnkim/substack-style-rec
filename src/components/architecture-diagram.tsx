"use client";

import { ReactNode } from "react";

// ─── Tooltip copy ─────────────────────────────────────────────────────────────

const TIPS: Record<string, string> = {
  "Next.js":
    "React framework powering the video discovery user interface (UI), with server-side rendering and API routes.",
  "client library":
    "Fetch helpers that call the FastAPI backend for videos, recommendations, and search.",
  FastAPI:
    "Python web server exposing representational state transfer (REST) endpoints over HTTP (Hypertext Transfer Protocol). Route handlers call Pixeltable directly to store, transform, and query multimodal data.",
  pixeltable:
    "Multimodal backend. Stores the videos next to their embeddings and tags, calls TwelveLabs on insert, and runs similarity search.",
  store:
    "Insert videos and creators as rows. Native video columns associate source media with its structured metadata.",
  transform:
    "Computed columns run scene detection and call TwelveLabs on insert. Pixeltable computes new rows and maintains their scene index incrementally.",
  query:
    "Similarity search via .similarity() and filtering. Uses pgvector under the hood.",
  TwelveLabs:
    "Queries use Pixeltable's built-in Marengo embed. Analyze and scene video embeds are custom user-defined functions (UDFs) in functions.py. Analyze results are a computed column, and the scene embedding is the embedding index's embedding function.",
  embed:
    "Embed API v2 with Marengo 3.0. Stores one 512-dimension vector for each scene clip.",
  analyze:
    "Analyze API extracting structured attributes: topic, style, and tone from video content.",
};

// ─── Inline SVG icons ─────────────────────────────────────────────────────────

type IconProps = { className?: string };

export function MonitorIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <rect width="20" height="14" x="2" y="3" rx="2" />
      <line x1="8" x2="16" y1="21" y2="21" />
      <line x1="12" x2="12" y1="17" y2="21" />
    </svg>
  );
}

export function ServerIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <rect width="20" height="8" x="2" y="2" rx="2" />
      <rect width="20" height="8" x="2" y="14" rx="2" />
      <line x1="6" x2="6.01" y1="6" y2="6" />
      <line x1="6" x2="6.01" y1="18" y2="18" />
    </svg>
  );
}

function DatabaseIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5V19A9 3 0 0 0 21 19V5" />
      <path d="M3 12A9 3 0 0 0 21 12" />
    </svg>
  );
}

function CpuIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <rect width="16" height="16" x="4" y="4" rx="2" />
      <rect width="6" height="6" x="9" y="9" rx="1" />
      <path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2" />
    </svg>
  );
}

function SearchIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

export function GithubIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

// Bars traced from the TwelveLabs app icon, as [x, y, width] in a 180px grid.
const TWELVELABS_BARS: [number, number, number][] = [
  [105, 32, 8],
  [96, 42, 14], [142, 42, 6],
  [87, 52, 23], [115, 52, 6], [134, 52, 24],
  [53, 62, 23], [112, 62, 27], [143, 62, 21],
  [9, 72, 28], [44, 72, 50], [108, 72, 31], [158, 72, 13],
  [33, 82, 65], [108, 82, 25],
  [44, 92, 82],
  [31, 101, 31], [92, 101, 25],
  [41, 111, 10], [59, 111, 10], [95, 111, 10], [113, 111, 9],
  [51, 121, 7], [68, 121, 12], [90, 121, 8], [102, 121, 22],
  [84, 131, 7],
  [77, 141, 7],
];

export function TwelveLabsLogo({ className }: IconProps) {
  return (
    <svg viewBox="5 5 170 170" fill="currentColor" className={className} aria-hidden>
      {TWELVELABS_BARS.map(([x, y, w]) => (
        <rect key={`${x}-${y}`} x={x} y={y} width={w} height={6} />
      ))}
    </svg>
  );
}

// Cells of the "P" in the Pixeltable mark's 7x7 grid, as [row, column].
const PIXELTABLE_DOTS = new Set([
  "0-1", "0-2", "0-3", "0-4",
  "1-1", "1-5",
  "2-1", "2-5",
  "3-1", "3-2", "3-3", "3-4",
  "4-1", "5-1", "6-1",
]);

export function PixeltableLogo({ className }: IconProps) {
  const cells = [];
  for (let row = 0; row < 7; row++) {
    for (let col = 0; col < 7; col++) {
      const cx = 70 + col * 51;
      const cy = 83 + row * 51;
      cells.push(
        PIXELTABLE_DOTS.has(`${row}-${col}`) ? (
          <circle key={`${row}-${col}`} cx={cx} cy={cy} r={19} />
        ) : (
          <rect key={`${row}-${col}`} x={cx - 19} y={cy - 19} width={38} height={38} opacity={0.3} />
        ),
      );
    }
  }
  return (
    <svg viewBox="0 0 446 477" fill="currentColor" className={className} aria-hidden>
      <rect x="7.5" y="7.5" width="431" height="462" rx="40" fill="none" stroke="currentColor" strokeWidth="15" />
      {cells}
    </svg>
  );
}

// ─── Hover popover (CSS-only) ─────────────────────────────────────────────────

function Hover({
  tip,
  children,
}: {
  tip?: string;
  children: ReactNode;
}) {
  if (!tip) return <>{children}</>;
  return (
    <div className="group/tip relative">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-[calc(100%+8px)] z-50 w-[240px] -translate-x-1/2 rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-elevated)] px-3 py-2 text-[11px] font-normal leading-snug text-[var(--text-secondary)] opacity-0 shadow-[var(--shadow-elevated)] transition-opacity duration-150 group-hover/tip:opacity-100 group-focus-within/tip:opacity-100"
      >
        {tip}
      </span>
    </div>
  );
}

// ─── Diagram primitives ───────────────────────────────────────────────────────

function DiagNode({
  label,
  sub,
  icon: Icon,
  tip,
  children,
}: {
  label: string;
  sub?: string;
  icon?: (props: IconProps) => ReactNode;
  tip?: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)] p-3 text-center shadow-[var(--shadow-card)] transition-colors hover:border-[var(--border-accent)]">
      <Hover tip={tip}>
        <div className="mb-0.5 flex items-center justify-center gap-1.5">
          {Icon && <Icon className="w-3.5 h-3.5 text-[var(--text-secondary)]" />}
          <span className="text-xs font-semibold text-[var(--text-primary)]">
            {label}
          </span>
        </div>
        {sub && (
          <span className="block max-w-[200px] text-[11px] leading-snug text-[var(--text-tertiary)]">
            {sub}
          </span>
        )}
      </Hover>
      {children && <div className="mt-2 w-full">{children}</div>}
    </div>
  );
}

function Pill({ label }: { label: string }) {
  const tip = TIPS[label];
  const pill = (
    <span className="inline-block rounded-md border border-[var(--border-default)] bg-[var(--bg-elevated)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-primary)] shadow-[var(--shadow-card)]">
      {label}
    </span>
  );
  return <Hover tip={tip}>{pill}</Hover>;
}

function Zone({
  title,
  className,
  children,
}: {
  title: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`flex flex-col gap-3 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-surface)]/40 p-4 ${className ?? ""}`}
    >
      <div className="text-center text-[9px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
        {title}
      </div>
      {children}
    </div>
  );
}

function IntegrationBadge({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center">
      <span className="inline-flex items-center gap-1 rounded-full border border-[var(--border-accent)] bg-[var(--accent-muted)] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-[var(--accent)]">
        <PixeltableLogo className="w-2.5 h-2.5" />
        {text}
      </span>
    </div>
  );
}

function PixeltableBox({ children }: { children: ReactNode }) {
  return (
    <div
      className="w-full rounded-[var(--radius-lg)] border border-[var(--border-accent)] p-4 shadow-[var(--shadow-card)]"
      style={{
        background:
          "linear-gradient(to bottom, var(--accent-muted), transparent)",
      }}
    >
      {children}
    </div>
  );
}

function FlowArrow({ label }: { label: string }) {
  return (
    <div className="flex shrink-0 items-center justify-center gap-2 py-1 md:flex-col md:gap-1 md:px-2 md:py-0">
      <svg
        width="48"
        height="20"
        viewBox="0 0 48 20"
        fill="none"
        className="rotate-90 text-[var(--text-tertiary)] md:rotate-0"
        aria-hidden
      >
        <path d="M4 10H40" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M36 5L42 10L36 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="whitespace-nowrap text-[9px] font-medium text-[var(--text-tertiary)]">
        {label}
      </span>
    </div>
  );
}

function BiFlowArrow() {
  return (
    <div className="flex shrink-0 flex-col items-center justify-center gap-1 px-2 py-1 md:gap-0.5 md:py-0">
      <span className="whitespace-nowrap text-[9px] font-medium text-[var(--text-tertiary)]">
        videos
      </span>
      <svg
        width="48"
        height="14"
        viewBox="0 0 48 14"
        fill="none"
        className="rotate-90 text-[var(--accent)] md:rotate-0"
        aria-hidden
      >
        <path d="M4 7H40" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="4 3" />
        <path d="M36 3L42 7L36 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <svg
        width="48"
        height="14"
        viewBox="0 0 48 14"
        fill="none"
        className="rotate-90 text-[var(--accent)] md:rotate-0"
        aria-hidden
      >
        <path d="M8 7H44" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="4 3" />
        <path d="M12 3L6 7L12 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="whitespace-nowrap text-[9px] font-medium text-[var(--text-tertiary)]">
        vectors
      </span>
    </div>
  );
}

// ─── Main diagram ─────────────────────────────────────────────────────────────

export default function ArchitectureDiagram() {
  return (
    <div className="w-full">
      <div className="p-2">
        <div className="flex flex-col items-stretch gap-2 md:flex-row md:gap-0">
          {/* LEFT: the app */}
          <Zone title="the app" className="flex-1">
            <DiagNode
              label="Next.js"
              sub="frontend"
              icon={MonitorIcon}
              tip={TIPS["Next.js"]}
            >
              <div className="mt-1 flex items-center justify-center gap-1.5">
                <Pill label="client library" />
              </div>
            </DiagNode>
          </Zone>

          <FlowArrow label="HTTP" />

          {/* CENTER: server-side */}
          <Zone title="server-side" className="flex-[1.8]">
            <DiagNode
              label="FastAPI"
              sub="web server"
              icon={ServerIcon}
              tip={TIPS["FastAPI"]}
            />

            <IntegrationBadge text="pixeltable integration" />

            <PixeltableBox>
              <Hover tip={TIPS.pixeltable}>
                <div className="mb-3 flex items-center justify-center gap-1.5">
                  <PixeltableLogo className="w-3.5 h-3.5 text-[var(--accent)]" />
                  <span className="text-xs font-semibold text-[var(--text-primary)]">
                    pixeltable
                  </span>
                  <span className="ml-1 text-[10px] text-[var(--text-tertiary)]">
                    multimodal backend
                  </span>
                </div>
              </Hover>

              <div className="grid grid-cols-3 gap-2">
                <Hover tip={TIPS.store}>
                  <div className="flex flex-col items-center justify-center rounded-md border border-[var(--border-default)] bg-[var(--bg-card)] p-2.5 text-center">
                    <DatabaseIcon className="mb-1 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                    <span className="text-[11px] font-semibold text-[var(--text-primary)]">
                      database
                    </span>
                    <span className="mt-0.5 text-[10px] leading-snug text-[var(--text-tertiary)]">
                      tables &amp; views
                    </span>
                  </div>
                </Hover>
                <Hover tip={TIPS.transform}>
                  <div className="flex flex-col items-center justify-center rounded-md border border-[var(--border-default)] bg-[var(--bg-card)] p-2.5 text-center">
                    <CpuIcon className="mb-1 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                    <span className="text-[11px] font-semibold text-[var(--text-primary)]">
                      AI steps
                    </span>
                    <span className="mt-0.5 text-[10px] leading-snug text-[var(--text-tertiary)]">
                      computed columns
                    </span>
                  </div>
                </Hover>
                <Hover tip={TIPS.query}>
                  <div className="flex flex-col items-center justify-center rounded-md border border-[var(--border-default)] bg-[var(--bg-card)] p-2.5 text-center">
                    <SearchIcon className="mb-1 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                    <span className="text-[11px] font-semibold text-[var(--text-primary)]">
                      query
                    </span>
                    <span className="mt-0.5 text-[10px] leading-snug text-[var(--text-tertiary)]">
                      embedding indexes · .similarity()
                    </span>
                  </div>
                </Hover>
              </div>
            </PixeltableBox>
          </Zone>

          <BiFlowArrow />

          {/* RIGHT: external */}
          <Zone title="external" className="flex-1">
            <DiagNode
              label="TwelveLabs"
              sub="video embeddings"
              icon={TwelveLabsLogo}
              tip={TIPS.TwelveLabs}
            >
              <div className="mt-1 flex items-center justify-center gap-1.5">
                <Pill label="embed" />
                <Pill label="analyze" />
              </div>
            </DiagNode>

            <IntegrationBadge text="pixeltable integration" />

            <div className="text-center text-[10px] leading-snug text-[var(--text-tertiary)]">
              Queries use the built-in Marengo embed. Analyze and scene video
              embeds are custom user-defined functions (UDFs). Analyze results are a
              computed column, and scene embeds run inside the embedding index.
            </div>
          </Zone>
        </div>
      </div>
    </div>
  );
}
