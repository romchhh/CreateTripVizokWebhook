#!/usr/bin/env python3
"""
Простий HTTP сервер для обслуговування веб-додатка
"""

import http.server
import socketserver
import os
import sys

# Порт для веб-сервера
PORT = 8003

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler з підтримкою CORS"""
    
    def end_headers(self):
        # Додаємо CORS заголовки
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Обробляємо preflight запити
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Логування запитів
        print(f"🌐 {format % args}")

def start_server():
    """Запускає HTTP сервер"""
    
    # Переходимо в папку docs
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    if os.path.exists(docs_dir):
        os.chdir(docs_dir)
        print(f"📂 Serving from: {docs_dir}")
    else:
        print(f"❌ Папка docs не знайдена: {docs_dir}")
        sys.exit(1)
    
    # Створюємо сервер
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"🚀 HTTP Server started!")
        print(f"📱 WebApp URL: http://localhost:{PORT}")
        print(f"📱 Direct link: http://localhost:{PORT}/index.html")
        print(f"🔧 Webhook endpoint: http://localhost:8001/webhook")
        print(f"")
        print(f"▶️  Відкрийте http://localhost:{PORT} у браузері")
        print(f"🛑 Натисніть Ctrl+C для зупинки")
        print("-" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Сервер зупинено")

if __name__ == "__main__":
    start_server() 