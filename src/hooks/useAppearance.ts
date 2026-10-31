import { useEffect, useState } from "react";
import {
  applyTheme,
  initialTheme,
  THEME_KEY,
  type Theme,
} from "../lib/appearance";

export function useAppearance() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  useEffect(() => {
    applyTheme(theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* Session preference still works. */
    }
  }, [theme]);
  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key === THEME_KEY) setTheme(initialTheme());
    };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  return { theme, setTheme };
}
