export type Theme = "light" | "dark";
export const THEME_KEY = "grafiplot.studio.theme";

export function readTheme(
  storage: Pick<Storage, "getItem"> | undefined,
): Theme {
  try {
    return storage?.getItem(THEME_KEY) === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", theme === "dark" ? "#111318" : "#f1f3f6");
}

export function initialTheme(): Theme {
  try {
    return readTheme(window.localStorage);
  } catch {
    return "dark";
  }
}
