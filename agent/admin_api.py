"""
Admin API — Manage client configs, test DB connections, view schema.
Runs alongside the agent on port 8096.
"""
import json
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

from client_config import (
    list_configs, load_config, save_config,
    get_active_config_name, set_active_config, create_default_config,
)

logger = logging.getLogger("mrna.admin")

# Reference to running attacher for live schema info
_attacher = None


def set_attacher(attacher):
    global _attacher
    _attacher = attacher


class AdminHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def do_OPTIONS(self):
        self._json(204, "")

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            schema_info = None
            if _attacher and _attacher.tables:
                schema_info = {
                    "tables": len(_attacher.tables),
                    "total_columns": sum(len(t["columns"]) for t in _attacher.tables.values()),
                    "total_rows": sum(t["row_count"] for t in _attacher.tables.values()),
                }
            self._json(200, {
                "status": "ok",
                "active_config": get_active_config_name(),
                "database_connected": _attacher is not None and _attacher.pool is not None,
                "schema": schema_info,
            })

        elif path == "/configs":
            configs = list_configs()
            active = get_active_config_name()
            self._json(200, {
                "configs": configs,
                "active": active,
            })

        elif path.startswith("/configs/"):
            name = path.split("/configs/")[1]
            try:
                config = load_config(name)
                # Mask database URL password
                if "database_url" in config:
                    url = config["database_url"]
                    if "@" in url:
                        parts = url.split("@")
                        config["database_url_masked"] = "***@" + parts[-1]
                self._json(200, config)
            except FileNotFoundError:
                self._json(404, {"error": f"Config '{name}' not found"})

        elif path == "/schema":
            if not _attacher or not _attacher.tables:
                self._json(400, {"error": "No database attached"})
                return
            self._json(200, {
                "tables": _attacher.tables,
                "context": _attacher.schema_context,
                "few_shot_count": _attacher.few_shot.count("Q:"),
            })

        elif path == "/sessions":
            self._json(200, {"sessions": []})

        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path == "/configs":
            # Create new config
            try:
                data = json.loads(body)
                name = data.pop("config_name", None)
                if not name:
                    self._json(400, {"error": "config_name required"})
                    return
                save_config(name, data)
                self._json(200, {"success": True, "name": name})
            except Exception as e:
                self._json(400, {"error": str(e)})

        elif path == "/configs/activate":
            try:
                data = json.loads(body)
                name = data.get("name")
                if not name:
                    self._json(400, {"error": "name required"})
                    return
                set_active_config(name)
                self._json(200, {"success": True, "active": name,
                    "message": "Restart agent to apply new config"})
            except Exception as e:
                self._json(400, {"error": str(e)})

        elif path == "/test-connection":
            # Test a database connection
            try:
                data = json.loads(body)
                url = data.get("database_url")
                schema = data.get("schema", "public")
                if not url:
                    self._json(400, {"error": "database_url required"})
                    return

                # Run async test in a new loop
                result = _test_connection_sync(url, schema)
                self._json(200, result)
            except Exception as e:
                self._json(500, {"error": str(e)})

        elif path == "/query":
            # Test a natural language query
            if not _attacher:
                self._json(400, {"error": "No database attached"})
                return
            try:
                data = json.loads(body)
                question = data.get("question")
                if not question:
                    self._json(400, {"error": "question required"})
                    return
                result = asyncio.run(_attacher.ask(question))
                self._json(200, result)
            except Exception as e:
                self._json(500, {"error": str(e)})

        else:
            self._json(404, {"error": "Not found"})

    def do_PUT(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path.startswith("/configs/"):
            name = path.split("/configs/")[1]
            try:
                data = json.loads(body)
                save_config(name, data)
                self._json(200, {"success": True})
            except Exception as e:
                self._json(400, {"error": str(e)})
        else:
            self._json(404, {"error": "Not found"})

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode() if length else ""


def _test_connection_sync(url, schema):
    """Test DB connection in a sync context."""
    import asyncpg

    async def _test():
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(url), timeout=10
            )
            # Get table count
            rows = await conn.fetch(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 AND table_type = 'BASE TABLE'",
                schema,
            )
            tables = [r["table_name"] for r in rows]

            # Get total row count estimate
            total_rows = 0
            for t in tables[:10]:
                try:
                    cnt = await conn.fetchval(f'SELECT COUNT(*) FROM "{schema}"."{t}"')
                    total_rows += cnt
                except Exception:
                    pass

            await conn.close()
            return {
                "success": True,
                "tables": len(tables),
                "table_names": tables,
                "total_rows_sample": total_rows,
                "schema": schema,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    return asyncio.run(_test())


def start_admin_server(port=8096):
    """Start admin API in a background thread."""
    create_default_config()

    def _run():
        server = HTTPServer(("0.0.0.0", port), AdminHandler)
        logger.info(f"Admin API on http://localhost:{port}")
        server.serve_forever()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
