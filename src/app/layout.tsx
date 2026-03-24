import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Instrument_Serif } from "next/font/google";
import { UserStateProvider } from "@/lib/user-state";
import { Nav } from "@/components/nav";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-display",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Substack TV — AI-Powered Recommendations",
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
      className={`${geistSans.variable} ${geistMono.variable} ${instrumentSerif.variable} h-full antialiased`}
    >
      <body className="noise min-h-full flex flex-col font-[family-name:var(--font-geist-sans)]">
        <UserStateProvider>
          <Nav />
          <main className="flex-1 pt-14">{children}</main>
        </UserStateProvider>
      </body>
    </html>
  );
}
