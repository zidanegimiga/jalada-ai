import { SoundChoice } from "@/shared/components/SoundChoice";
import { ThemeChoice } from "@/shared/components/ThemeChoice";

/** Settings kept on this device. */
export function Preferences() {
  return (
    <section
      aria-labelledby="preferences-heading"
      className="flex flex-col gap-4 rounded-card border border-border bg-card p-card"
    >
      <h2 id="preferences-heading" className="text-title">
        On this device
      </h2>
      <ThemeChoice />
      <SoundChoice />
    </section>
  );
}
