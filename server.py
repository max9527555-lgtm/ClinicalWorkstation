from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os,webbrowser
root=Path(__file__).resolve().parent/'dist'
os.chdir(str(root))
class Handler(SimpleHTTPRequestHandler):
    extensions_map=dict(SimpleHTTPRequestHandler.extensions_map,**{'.js':'text/javascript','.webmanifest':'application/manifest+json','.json':'application/json','.svg':'image/svg+xml'})
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
if __name__=='__main__':
    print('请在浏览器打开 http://localhost:4173 ，保持此窗口运行；按 Ctrl+C 停止。')
    ThreadingHTTPServer(('127.0.0.1',4173),Handler).serve_forever()
