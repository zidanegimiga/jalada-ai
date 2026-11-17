import type { Metadata, Viewport } from "next";
import { Onest } from "next/font/google";

import { Splash, SplashScript } from "@/components/splash/splash";

import "./globals.css";

const onest = Onest({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? "http://localhost:3000"),
  title: "Jalada AI",
  description: "Money records for people without an accountant.",
};

// Colours the phone's browser bar to match the page in both themes.
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fefff6" },
    { media: "(prefers-color-scheme: dark)", color: "#0c0c0a" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${onest.variable} h-full antialiased`}>
      <head>
        <SplashScript />
      </head>
      <body className="min-h-full flex flex-col">
        <Splash />
        {children}
      </body>
    </html>
  );
}
