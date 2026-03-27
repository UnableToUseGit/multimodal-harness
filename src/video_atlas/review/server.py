from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

from .workspace_loader import ReviewWorkspace, load_review_workspace


STATIC_DIR = Path(__file__).resolve().parent / "static"


@dataclass
class ReviewAppServer:
    server: ThreadingHTTPServer
    host: str
    port: int
    workspaces: list[ReviewWorkspace]

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def serve_forever(self) -> None:
        self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()


def _workspace_payload(workspaces: list[ReviewWorkspace]) -> dict[str, object]:
    payload = []
    for workspace in workspaces:
        data = workspace.to_dict()
        data["source_video_url"] = (
            f"/media/{workspace.workspace_id}/{workspace.source_video_relative_path}"
            if workspace.source_video_relative_path
            else None
        )
        data["normalized_audio_url"] = (
            f"/media/{workspace.workspace_id}/{workspace.normalized_audio_relative_path}"
            if workspace.normalized_audio_relative_path
            else None
        )
        for segment in data["segments"]:
            clip_relative_path = segment.get("clip_relative_path")
            subtitles_relative_path = segment.get("subtitles_relative_path")
            readme_relative_path = segment.get("readme_relative_path")
            segment["clip_url"] = f"/media/{workspace.workspace_id}/{clip_relative_path}" if clip_relative_path else None
            segment["subtitles_url"] = f"/media/{workspace.workspace_id}/{subtitles_relative_path}" if subtitles_relative_path else None
            segment["readme_url"] = f"/media/{workspace.workspace_id}/{readme_relative_path}" if readme_relative_path else None
        payload.append(data)
    return {"workspaces": payload}


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def _static_bytes(name: str) -> bytes:
    return (STATIC_DIR / name).read_bytes()


def _guess_content_type(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(str(path))
    return content_type or "application/octet-stream"


def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int] | None:
    if not range_header.startswith("bytes="):
        return None

    byte_range = range_header[len("bytes="):].strip()
    if "," in byte_range or "-" not in byte_range:
        return None

    start_text, end_text = byte_range.split("-", 1)
    if not start_text and not end_text:
        return None

    try:
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else file_size - 1
        else:
            suffix_length = int(end_text)
            if suffix_length <= 0:
                return None
            start = max(file_size - suffix_length, 0)
            end = file_size - 1
    except ValueError:
        return None

    if start < 0 or end < start or start >= file_size:
        return None

    end = min(end, file_size - 1)
    return start, end


def _build_handler(workspaces: dict[str, ReviewWorkspace]):
    payload_bytes = _json_bytes(_workspace_payload(list(workspaces.values())))

    class ReviewRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/":
                self._write_bytes(_static_bytes("index.html"), "text/html; charset=utf-8")
                return
            if path == "/app.js":
                self._write_bytes(_static_bytes("app.js"), "application/javascript; charset=utf-8")
                return
            if path == "/styles.css":
                self._write_bytes(_static_bytes("styles.css"), "text/css; charset=utf-8")
                return
            if path == "/api/index":
                self._write_bytes(payload_bytes, "application/json; charset=utf-8")
                return
            if path.startswith("/media/"):
                self._serve_media(path)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _serve_media(self, request_path: str) -> None:
            parts = request_path.split("/", 3)
            if len(parts) != 4:
                self.send_error(HTTPStatus.NOT_FOUND, "Invalid media path")
                return

            _, _, workspace_id, relative_path = parts
            workspace = workspaces.get(workspace_id)
            if workspace is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown workspace")
                return

            target = (workspace.root_path / relative_path).resolve()
            if workspace.root_path not in target.parents and target != workspace.root_path:
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden path")
                return
            if not target.exists() or not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Missing file")
                return

            self._serve_file(target)

        def _write_bytes(self, body: bytes, content_type: str) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _serve_file(self, path: Path) -> None:
            file_size = path.stat().st_size
            content_type = _guess_content_type(path)
            range_header = self.headers.get("Range")
            byte_range = _parse_range_header(range_header, file_size) if range_header else None

            if byte_range is None:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                with path.open("rb") as handle:
                    self.wfile.write(handle.read())
                return

            start, end = byte_range
            content_length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(content_length))
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with path.open("rb") as handle:
                handle.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk = handle.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

    return ReviewRequestHandler


def run_review_app(
    canonical_atlas_dir: str | Path | None = None,
    derived_atlas_dir: str | Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ReviewAppServer:
    loaded_workspaces: list[ReviewWorkspace] = []
    if canonical_atlas_dir is not None:
        loaded_workspaces.append(
            load_review_workspace(canonical_atlas_dir, workspace_id="canonical", label="Canonical Atlas")
        )
    if derived_atlas_dir is not None:
        loaded_workspaces.append(
            load_review_workspace(derived_atlas_dir, workspace_id="derived", label="Derived Atlas")
        )
    if not loaded_workspaces:
        raise ValueError("At least one atlas directory path must be provided.")

    handler = _build_handler({workspace.workspace_id: workspace for workspace in loaded_workspaces})
    server = ThreadingHTTPServer((host, port), handler)
    return ReviewAppServer(server=server, host=host, port=port, workspaces=loaded_workspaces)
