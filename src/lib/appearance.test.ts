import { describe, expect, it } from "vitest";
import { readTheme, THEME_KEY } from "./appearance";

describe("preferencia de apariencia", () => {
  it("usa oscuro en la primera apertura", () => {
    expect(readTheme(undefined)).toBe("dark");
    expect(readTheme({ getItem: () => null })).toBe("dark");
  });
  it("recupera la elección del usuario", () => {
    expect(
      readTheme({ getItem: (key) => (key === THEME_KEY ? "light" : null) }),
    ).toBe("light");
    expect(readTheme({ getItem: () => "dark" })).toBe("dark");
  });
  it("tolera preferencias dañadas o almacenamiento bloqueado", () => {
    expect(readTheme({ getItem: () => "invalid" })).toBe("dark");
    expect(
      readTheme({
        getItem: () => {
          throw new Error("Storage blocked");
        },
      }),
    ).toBe("dark");
  });
});
