import type { Metadata } from "next";

import { Colours, Components, Shapes, Type } from "./sections";

export const metadata: Metadata = {
  title: "Design · Jalada AI",
  robots: { index: false },
};

/** Every design token and the shared components, in both themes, for anyone building a
 * screen. The values live in globals.css. */
export default function DesignPage() {
  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col gap-section px-gutter pt-8 pb-12">
      <header className="flex flex-col gap-1">
        <h1 className="text-display">Design</h1>
        <p className="text-lead text-muted-foreground">
          The tokens and components every screen is built from.
        </p>
      </header>
      <Colours />
      <Type />
      <Shapes />
      <Components />
    </main>
  );
}
