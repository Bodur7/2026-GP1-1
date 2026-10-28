"""Loopback-only upload app. Launch with Test Full Pipeline.command."""
from __future__ import annotations

import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import sys
import threading
from urllib.parse import parse_qs, urlsplit
from urllib.request import urlopen
from urllib.error import URLError
import uuid
import webbrowser

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from dish_identifier.pipeline import Pipeline, runtime_signature, validate_image
from dish_identifier.claude_client import StageError
from dish_identifier.recipe_fusion import NAME_NORMALIZATION_METHOD

UI = Path(__file__).with_name("pipeline_ui")


def save_json(path, value):
    temp = path.with_suffix('.tmp')
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')
    temp.replace(path)


class App:
    def __init__(self, pipeline, output=None):
        self.pipeline = pipeline
        self.token = secrets.token_urlsafe(32)
        self.jobs = {}
        self.upload_ids = {}
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.output = output or PROJECT / 'manual_testing/pipeline_results' / (datetime.now().strftime('%Y%m%d_%H%M%S_') + secrets.token_hex(3))
        self.output.mkdir(mode=0o700, parents=True, exist_ok=False)

    def add(self, data, name, upload_id):
        with self.lock:
            if upload_id in self.upload_ids:
                return self.jobs[self.upload_ids[upload_id]]
            if len(self.jobs) >= 100:
                raise StageError('session_limit', 'This session has reached 100 photos. Restart the tester for a new session.')
            if sum(job['status'] != 'done' for job in self.jobs.values()) >= 8:
                raise StageError('queue_full', 'Eight photos are already being processed. Wait for a photo to finish before uploading more.')
            job_id = uuid.uuid4().hex
            directory = self.output / job_id
            directory.mkdir(mode=0o700)
            path = directory / 'original.image'
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(data)
            job = {'id': job_id, 'filename': name, 'status': 'queued', 'result': None,
                   'created_at': datetime.now(timezone.utc).isoformat()}
            self.jobs[job_id] = job
            self.upload_ids[upload_id] = job_id
            save_json(directory / 'result.json', job)
            self.executor.submit(self.process, job_id, path)
            return json.loads(json.dumps(job))

    def process(self, job_id, path):
        with self.lock:
            self.jobs[job_id]['status'] = 'running'
            filename = self.jobs[job_id]['filename']
        def update(result):
            with self.lock:
                self.jobs[job_id]['result'] = json.loads(json.dumps(result, allow_nan=False))
                save_json(path.parent / 'result.json', self.jobs[job_id])
        try:
            result = self.pipeline.run(path, filename=filename, progress=update)
        except Exception as error:
            result = {'decision': 'error', 'message': 'The local analysis could not be completed. Please restart the tester and try again.',
                      'error_type': type(error).__name__, 'stages': [], 'filename': filename}
        with self.lock:
            self.jobs[job_id].update(status='done', result=result)
            save_json(path.parent / 'result.json', self.jobs[job_id])

    def get(self, job_id):
        with self.lock:
            return json.loads(json.dumps(self.jobs[job_id])) if job_id in self.jobs else None


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, app):
        self.app = app
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = 'MisbarLocal/1.0'

    def log_message(self, *args):
        pass

    def host_ok(self):
        return self.headers.get('Host') == '127.0.0.1:' + str(self.server.server_port)

    def send(self, status, body, mime='application/json', filename=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if filename:
            self.send_header('Content-Disposition', 'attachment; filename="' + filename + '"')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if not self.host_ok():
            return self.send(403, {'message': 'This tester accepts local requests only.'})
        path = urlsplit(self.path).path
        if path == '/':
            page = (UI / 'index.html').read_text().replace('@@TOKEN@@', self.server.app.token)
            return self.send(200, page.encode(), 'text/html; charset=utf-8')
        if path in ('/app.js', '/style.css'):
            return self.send(200, (UI / path[1:]).read_bytes(), 'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
        if path == '/api/health':
            return self.send(200, {'app': 'misbar-full-pipeline-v1', 'ready': not self.server.app.pipeline.setup_errors,
                'setup_errors': self.server.app.pipeline.setup_errors,
                'ingredient_data': self.server.app.pipeline.ingredient_data,
                'ingredient_name_normalization': NAME_NORMALIZATION_METHOD,
                'runtime_signature': self.server.app.pipeline.runtime_signature,
                'semantic_normalization_enabled': self.server.app.pipeline.config['normalization_enabled'],
                'classification_output': 'top1', 'stage_count': len(self.server.app.pipeline.stage_definitions),
                'stop_after': ('Semantic ingredient normalization, before user-allergy matching'
                    if self.server.app.pipeline.config['normalization_enabled'] else 'Ingredient merging, before semantic normalization'),
                'model': self.server.app.pipeline.config['claude_model']})
        if path == '/api/jobs':
            with self.server.app.lock:
                jobs = [{'id': j['id'], 'filename': j['filename'], 'status': j['status']} for j in self.server.app.jobs.values()]
            return self.send(200, {'jobs': jobs})
        match = re.fullmatch(r'/api/jobs/([a-f0-9]{32})(/(image|download))?', path)
        if match:
            job = self.server.app.get(match[1])
            if job is None:
                return self.send(404, {'message': 'This photo was not found in the current session.'})
            if match[3] == 'image':
                data = (self.server.app.output / match[1] / 'original.image').read_bytes()
                try:
                    _, mime, _ = validate_image(data, self.server.app.pipeline.config)
                except StageError:
                    return self.send(415, {'message': 'A preview is not available for this file.'})
                return self.send(200, data, mime)
            return self.send(200, job, filename='misbar_' + match[1][:8] + '.json' if match[3] == 'download' else None)
        return self.send(404, {'message': 'Page not found.'})

    def do_POST(self):
        expected_origin = 'http://127.0.0.1:' + str(self.server.server_port)
        if not self.host_ok() or self.headers.get('Origin', expected_origin) != expected_origin or not hmac.compare_digest(self.headers.get('X-Misbar-Token', ''), self.server.app.token):
            return self.send(403, {'message': 'This upload was not authorized by the local tester.'})
        route = urlsplit(self.path)
        if route.path != '/api/jobs':
            return self.send(404, {'message': 'Page not found.'})
        try:
            if self.headers.get('Transfer-Encoding') or not self.headers.get('Content-Length'):
                return self.send(411, {'message': 'The image upload requires a known file size.'})
            length = int(self.headers['Content-Length'])
            if not 0 < length <= self.server.app.pipeline.config['max_upload_bytes']:
                return self.send(413, {'message': 'Choose a non-empty image up to 4 MB.'})
            upload_id = self.headers.get('X-Upload-Id', '')
            if not re.fullmatch(r'[a-f0-9-]{16,64}', upload_id):
                return self.send(400, {'message': 'The upload identity is invalid. Refresh the tester and try again.'})
            name = parse_qs(route.query).get('name', ['photo'])[0].replace('\\', '/').split('/')[-1][:180]
            self.connection.settimeout(20)
            data = self.rfile.read(length)
            if len(data) != length:
                return self.send(400, {'message': 'The image upload was interrupted. Please upload the photo again.'})
            job = self.server.app.add(data, name, upload_id)
            return self.send(202, {'id': job['id'], 'filename': job['filename'], 'status': job['status']})
        except StageError as error:
            return self.send(429, {'message': error.message, 'code': error.code})
        except (ValueError, TimeoutError, OSError):
            return self.send(400, {'message': 'The photo could not be uploaded. Please choose it again.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    if args.port:
        url = 'http://127.0.0.1:' + str(args.port)
        try:
            with urlopen(url + '/api/health', timeout=2) as response:
                existing = json.load(response)
            if existing.get('app') == 'misbar-full-pipeline-v1':
                config = json.loads((PROJECT / 'configs/pipeline.json').read_text())
                data_file = config['ingredient_data_file']
                source_path = (PROJECT / data_file).resolve()
                expected_data = hashlib.sha256(source_path.read_bytes()).hexdigest()
                running_data = existing.get('ingredient_data') or {}
                if running_data.get('sha256') != expected_data or running_data.get('path') != str(source_path):
                    print('An older data version is running. Close its launcher window, then start this tester again.', flush=True)
                    sys.exit(1)
                if existing.get('ingredient_name_normalization') != NAME_NORMALIZATION_METHOD:
                    print('An older merging version is running. Close its launcher window, then start this tester again.', flush=True)
                    sys.exit(1)
                if existing.get('runtime_signature') != runtime_signature(PROJECT):
                    print('An older pipeline version is running. Close its launcher window, then start this tester again.', flush=True)
                    sys.exit(1)
                print('Misbar is already running: ' + url, flush=True)
                if not args.no_open:
                    webbrowser.open(url)
                return
        except (URLError, OSError, ValueError):
            pass
    pipeline = Pipeline()
    print('Loading the existing frozen dish model…', flush=True)
    pipeline.runtime.load()
    app = App(pipeline)
    server = Server(('127.0.0.1', args.port), app)
    url = 'http://127.0.0.1:' + str(server.server_port)
    print('Misbar is ready: ' + url, flush=True)
    print('Upload photos in the browser. Keep this window open. Press Control+C to stop.', flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.executor.shutdown(wait=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('The tester could not start (' + type(error).__name__ + '). Check the local model and configuration.', file=sys.stderr)
        sys.exit(1)
