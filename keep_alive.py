"""
Keep-alive сервер для предотвращения засыпания бота на Replit
Используйте этот файл только для Replit!
"""
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Discord Status Bot is alive and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Запускает Flask сервер в отдельном потоке"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
