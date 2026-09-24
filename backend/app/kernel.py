"""One persistent Python kernel per notebook (variables survive between runs, like Colab)."""
import base64
import mimetypes
import os
import time
from pathlib import Path

from jupyter_client import KernelManager

from . import store

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
OUTPUTS = WORKSPACE / "outputs"


class Kernel:
    def __init__(self):
        self.km = KernelManager(kernel_name="python3")
        env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK="1", MPLBACKEND="module://matplotlib_inline.backend_inline")
        self.km.start_kernel(cwd=str(WORKSPACE), env=env)
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready(timeout=120)

    def interrupt(self):
        self.km.interrupt_kernel()

    def shutdown(self):
        try:
            self.kc.stop_channels()
            self.km.shutdown_kernel(now=True)
        except Exception:  # noqa: BLE001
            pass


def _snapshot():
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    return {str(p): p.stat().st_mtime for p in OUTPUTS.rglob("*") if p.is_file()}


def execute(kernel: Kernel, run_id: int, code: str, on_update):
    """Run code; call on_update(outputs) as output arrives; return (status, outputs, files)."""
    outputs, files, status = [], [], "ok"
    before = _snapshot()
    msg_id = kernel.kc.execute(code)
    last_push = 0.0
    img_n = 0
    while True:
        try:
            msg = kernel.kc.get_iopub_msg(timeout=1)
        except Exception:  # noqa: BLE001  (timeout: keep waiting)
            continue
        if msg["parent_header"].get("msg_id") != msg_id:
            continue
        t, c = msg["msg_type"], msg["content"]
        if t == "stream":
            if outputs and outputs[-1]["type"] == "stream" and outputs[-1]["name"] == c["name"]:
                outputs[-1]["text"] += c["text"]
            else:
                outputs.append({"type": "stream", "name": c["name"], "text": c["text"]})
        elif t in ("display_data", "execute_result"):
            data = c["data"]
            if "image/png" in data:
                img_n += 1
                key = f"runs/{run_id}/image_{img_n}.png"
                store.put_bytes(key, base64.b64decode(data["image/png"]), "image/png")
                outputs.append({"type": "image", "key": key})
            elif "text/plain" in data:
                outputs.append({"type": "result", "text": data["text/plain"]})
        elif t == "error":
            status = "error"
            outputs.append({"type": "error", "text": "\n".join(c["traceback"]), "ename": c["ename"]})
        elif t == "status" and c["execution_state"] == "idle":
            break
        if time.time() - last_push > 1:
            on_update(outputs)
            last_push = time.time()

    for p, m in _snapshot().items():
        if before.get(p) != m:
            rel = os.path.relpath(p, OUTPUTS)
            key = f"runs/{run_id}/files/{rel}"
            store.put_file(key, p)
            files.append({"key": key, "name": rel, "type": mimetypes.guess_type(p)[0] or "application/octet-stream"})
    return status, outputs, files
