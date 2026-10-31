import { Component, type ErrorInfo, type ReactNode } from "react";
import { RefreshCw } from "lucide-react";

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("GRAFIPLOT UI", error, info.componentStack);
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="empty-state" style={{ height: "100vh" }}>
        <span className="eyebrow">GRAFIPLOT STUDIO</span>
        <h2>Necesitamos reiniciar la vista.</h2>
        <p>
          Ocurrió un error en la interfaz. Tus archivos originales permanecen
          intactos.
        </p>
        <button
          className="button primary"
          onClick={() => window.location.reload()}
        >
          <RefreshCw size={17} />
          Recargar interfaz
        </button>
      </div>
    );
  }
}
