import type { MetadataRoute } from "next";

import { THEME_COLOURS } from "@/shared/theme/theme";

type Icon = NonNullable<MetadataRoute.Manifest["icons"]>[number];

const ICONS: Icon[] = [192, 512].flatMap((size) => [
  {
    src: `/icons/icon-${size}.png`,
    sizes: `${size}x${size}`,
    type: "image/png",
    purpose: "any",
  },
  {
    src: `/icons/maskable-${size}.png`,
    sizes: `${size}x${size}`,
    type: "image/png",
    purpose: "maskable",
  },
]);

/** What a phone or computer needs to install Jalada AI as an app (decision 0028). */
export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Jalada AI",
    short_name: "Jalada",
    description: "Money records for people without an accountant.",
    lang: "en-KE",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: THEME_COLOURS.light,
    theme_color: THEME_COLOURS.light,
    categories: ["finance", "productivity"],
    icons: ICONS,
    shortcuts: [
      { name: "To check", url: "/review", icons: [ICONS[0]] },
      { name: "Ledger", url: "/ledger", icons: [ICONS[0]] },
    ],
  };
}
