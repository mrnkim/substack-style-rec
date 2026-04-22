import type { Metadata } from "next";
import { Noto_Sans, IBM_Plex_Mono } from "next/font/google";
import { UserStateProvider } from "@/lib/user-state";
import { Nav } from "@/components/nav";
import "./globals.css";

const notoSans = Noto_Sans({
  variable: "--font-noto-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "CuratorAI — AI-Powered Video Recommendations",
  description:
    "Netflix-style video discovery powered by TwelveLabs multimodal understanding. Semantic recommendations, cross-creator exploration, and explainable suggestions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${notoSans.variable} ${ibmPlexMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body
        className="noise min-h-full flex flex-col font-[family-name:var(--font-sans)]"
        suppressHydrationWarning
      >
        <UserStateProvider>
          <Nav />
          <main className="flex-1 pt-14">{children}</main>
        </UserStateProvider>
      </body>
    </html>
  );
}
