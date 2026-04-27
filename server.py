#!/usr/bin/env python3
import http.server, json, os, base64, subprocess, urllib.parse
from datetime import datetime

BLOG_DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self.path = '/post.html'
        path = os.path.join(BLOG_DIR, self.path.lstrip('/'))
        if os.path.exists(path):
            self.send_response(200)
            if path.endswith('.html'):
                self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != '/publish':
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(length))

        try:
            # 記事ファイルを作成
            slug = data['slug']
            content = data['content']
            post_path = os.path.join(BLOG_DIR, 'content', 'posts', f'{slug}.md')
            with open(post_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 写真を保存
            if data.get('photoData') and data.get('photo'):
                img_data = data['photoData'].split(',')[1]
                img_path = os.path.join(BLOG_DIR, 'static', data['photo'])
                with open(img_path, 'wb') as f:
                    f.write(base64.b64decode(img_data))

            # GitHubにプッシュ
            subprocess.run(['git', 'add', '.'], cwd=BLOG_DIR, check=True)
            subprocess.run(['git', 'commit', '-m', f'記事追加: {slug}'], cwd=BLOG_DIR, check=True)
            subprocess.run(['git', 'push'], cwd=BLOG_DIR, check=True)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': str(e)}).encode())

    def log_message(self, format, *args):
        pass

print('サーバー起動中... http://localhost:3456 を開いてください')
http.server.HTTPServer(('localhost', 3456), Handler).serve_forever()
