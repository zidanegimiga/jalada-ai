import type { Metadata, Viewport } from "next";
import { Martian_Mono, Onest } from "next/font/google";

import { ClickSounds } from "@/app/_components/ClickSounds";
import { Splash, SplashScript } from "@/app/_components/Splash";
import { ThemeScript } from "@/app/_components/ThemeScript";
import { THEME_COLOURS } from "@/shared/theme/theme";

import "./globals.css";

const onest = Onest({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

// Labels, step numbers and tags: a wide mono with some character, one variable file.
const martian = Martian_Mono({
  variable: "--font-label",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? "http://localhost:3000"),
  title: "Jalada AI",
  description: "Money records for people without an accountant.",
};

// Colours the phone's browser bar to match the page in both themes.
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: THEME_COLOURS.light },
    { media: "(prefers-color-scheme: dark)", color: THEME_COLOURS.dark },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // The scripts in <head> set data-theme and data-splash before React loads.
    <html
      lang="en"
      className={`${onest.variable} ${martian.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <ThemeScript />
        <SplashScript />
      </head>
      <body className="min-h-full flex flex-col">
        <Splash />
        <ClickSounds />
        {children}
      </body>
    </html>
  );
}
