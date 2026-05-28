from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

# Configuração do Banco de Dados
DB_PATH = "meu_site.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS ferramentas (id INTEGER PRIMARY KEY, nome TEXT, url TEXT)")

@app.route('/')
def home():
    return render_template('home.html', title="Home")

@app.route('/arquivos')
def arquivos():
    return render_template('arquivos.html', title="Arquivos")

@app.route('/terminal')
def terminal():
    return render_template('terminal.html', title="Terminal")

if __name__ == '__main__':
    init_db()
    # host='::' habilita o acesso via IPv6
    app.run(host='::', port=8080, debug=True)