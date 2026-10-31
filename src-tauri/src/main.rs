#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde_json::Value;
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use std::{
    io::{BufRead, BufReader, Write},
    process::{Child, ChildStdin, ChildStdout, Command, Stdio},
    sync::{Arc, Mutex},
};

struct Engine {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
}

impl Engine {
    fn start() -> Result<Self, String> {
        #[cfg(debug_assertions)]
        let mut command = {
            let mut command =
                Command::new(std::env::var("GRAFIPLOT_PYTHON").unwrap_or("python".into()));
            command.args(["-u", "-m", "grafiplot.desktop.service"]);
            command.current_dir(
                std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                    .parent()
                    .unwrap(),
            );
            command
        };
        #[cfg(not(debug_assertions))]
        let mut command = {
            let folder = std::env::current_exe()
                .map_err(|e| e.to_string())?
                .parent()
                .ok_or("No se encuentra la aplicación")?
                .to_path_buf();
            Command::new(folder.join("grafiplot-engine.exe"))
        };
        #[cfg(windows)]
        command.creation_flags(0x08000000);
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("No se pudo iniciar el motor PDF: {e}"))?;
        let input = child.stdin.take().ok_or("No hay canal de entrada")?;
        let output = BufReader::new(child.stdout.take().ok_or("No hay canal de salida")?);
        Ok(Self {
            child,
            input,
            output,
        })
    }

    fn request(&mut self, request: Value) -> Result<Value, String> {
        serde_json::to_writer(&mut self.input, &request).map_err(|e| e.to_string())?;
        self.input
            .write_all(b"\n")
            .and_then(|_| self.input.flush())
            .map_err(|e| e.to_string())?;
        let mut line = String::new();
        if self
            .output
            .read_line(&mut line)
            .map_err(|e| e.to_string())?
            == 0
        {
            return Err("El motor PDF se cerró inesperadamente.".into());
        }
        serde_json::from_str(&line).map_err(|e| format!("Respuesta PDF inválida: {e}"))
    }
}
impl Drop for Engine {
    fn drop(&mut self) {
        // Ask Python to close PDFs and remove its temporary workspace first.
        let _ = self.input.write_all(b"{\"method\":\"shutdown\"}\n");
        let _ = self.input.flush();
        for _ in 0..20 {
            if matches!(self.child.try_wait(), Ok(Some(_))) {
                return;
            }
            std::thread::sleep(std::time::Duration::from_millis(50));
        }
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

type EngineState = Arc<Mutex<Option<Engine>>>;

#[tauri::command]
async fn engine(request: Value, state: tauri::State<'_, EngineState>) -> Result<Value, String> {
    let shared = Arc::clone(&state);
    tauri::async_runtime::spawn_blocking(move || {
        let mut guard = shared.lock().map_err(|e| e.to_string())?;
        if guard.is_none() {
            *guard = Some(Engine::start()?);
        }
        guard.as_mut().unwrap().request(request)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
fn launch_files() -> Vec<String> {
    std::env::args()
        .skip(1)
        .filter(|arg| !arg.starts_with('-'))
        .filter(|arg| std::path::Path::new(arg).is_file())
        .collect()
}

fn main() {
    let state: EngineState = Arc::new(Mutex::new(None));
    let cleanup = Arc::clone(&state);
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(state)
        .invoke_handler(tauri::generate_handler![engine, launch_files])
        .build(tauri::generate_context!())
        .expect("No se pudo iniciar GRAFIPLOT");
    app.run(move |_handle, event| {
        if matches!(event, tauri::RunEvent::Exit) {
            if let Ok(mut engine) = cleanup.lock() {
                *engine = None;
            }
        }
    });
}
