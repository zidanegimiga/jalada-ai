import { THEME_COLOURS, THEME_STORAGE_KEY } from "@/shared/theme/theme";

/**
 * Runs before the first paint, so a picked theme never flashes the other one first. It sets
 * data-theme on <html> and colours the browser bar to match.
 */
const SCRIPT = `try{var t=localStorage.getItem(${JSON.stringify(THEME_STORAGE_KEY)});if(t==="light"||t==="dark"){document.documentElement.dataset.theme=t;var c=${JSON.stringify(THEME_COLOURS)}[t];document.querySelectorAll('meta[name="theme-color"]').forEach(function(m){m.setAttribute("content",c)})}}catch(e){}`;

export function ThemeScript() {
  return <script dangerouslySetInnerHTML={{ __html: SCRIPT }} />;
}
