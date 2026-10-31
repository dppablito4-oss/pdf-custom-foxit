import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createInterface } from "node:readline";

// Development only: the production desktop uses Rust/stdin, without an HTTP server.
export default defineConfig({
  plugins: [
    react(),
    {
      name: "grafiplot-local-engine",
      configureServer(server) {
        let child: ChildProcessWithoutNullStreams | undefined;
        const pending: {
          resolve: (value: string) => void;
          reject: (error: Error) => void;
        }[] = [];
        function start() {
          if (child) return;
          child = spawn(
            process.env.GRAFIPLOT_PYTHON || "python",
            ["-u", "-m", "grafiplot.desktop.service"],
            { cwd: process.cwd(), windowsHide: true },
          );
          child.stderr.on("data", (data) => process.stderr.write(data));
          createInterface({ input: child.stdout }).on("line", (line) =>
            pending.shift()?.resolve(line),
          );
          child.on("error", (error) => {
            pending.splice(0).forEach((item) => item.reject(error));
            child = undefined;
          });
          child.on("exit", () => {
            pending
              .splice(0)
              .forEach((item) =>
                item.reject(new Error("El motor PDF se cerró.")),
              );
            child = undefined;
          });
        }
        server.httpServer?.once("close", () => child?.kill());
        server.middlewares.use("/api/engine", async (req, res) => {
          if (
            req.method !== "POST" ||
            !["127.0.0.1", "localhost"].includes(
              (req.headers.host || "").split(":")[0],
            )
          ) {
            res.writeHead(403).end();
            return;
          }
          const origin = req.headers.origin;
          if (origin && origin !== `http://${req.headers.host}`) {
            res.writeHead(403).end();
            return;
          }
          try {
            let body = "";
            for await (const chunk of req) {
              body += chunk;
              if (body.length > 140_000_000)
                throw new Error(
                  "Archivo demasiado grande para el modo de desarrollo.",
                );
            }
            const request = JSON.parse(body);
            start();
            const result = await new Promise<string>((resolve, reject) => {
              pending.push({ resolve, reject });
              child!.stdin.write(JSON.stringify(request) + "\n");
            });
            res.setHeader("Content-Type", "application/json");
            res.end(result);
          } catch (error) {
            res
              .writeHead(500, { "Content-Type": "application/json" })
              .end(JSON.stringify({ error: String(error) }));
          }
        });
      },
    },
  ],
  server: {
    port: 1420,
    strictPort: true,
    host: "127.0.0.1",
    watch: {
      ignored: [
        "**/.build/**",
        "**/.build-tools/**",
        "**/artifacts/**",
        "**/src-tauri/target/**",
      ],
    },
  },
  clearScreen: false,
});
