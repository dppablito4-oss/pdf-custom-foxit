import { Moon, Sun } from "lucide-react";
import { useAppearance } from "../hooks/useAppearance";

export function AppearanceControl() {
  const { theme, setTheme } = useAppearance();
  return (
    <div className="appearance-control">
      <span className="appearance-label">APARIENCIA</span>
      <div
        className="theme-switch"
        role="group"
        aria-label="Tema de la aplicación"
      >
        <button
          aria-label="Modo claro"
          aria-pressed={theme === "light"}
          onClick={() => setTheme("light")}
        >
          <Sun size={16} />
          Claro
        </button>
        <button
          aria-label="Modo oscuro"
          aria-pressed={theme === "dark"}
          onClick={() => setTheme("dark")}
        >
          <Moon size={16} />
          Oscuro
        </button>
      </div>
    </div>
  );
}
