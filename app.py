from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, jsonify
import sqlite3
import os, shutil, subprocess

# Informamos ao Flask para buscar os templates na pasta raiz do projeto.
# O padrão recomendado seria criar uma pasta 'templates/' e mover os .html para lá.
app = Flask(__name__, template_folder='.')
app.secret_key = 'chave_secreta_para_flash_messages'

# Configuração do Banco de Dados
DB_PATH = "meu_site.db"
DRIVE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drive')
if not os.path.exists(DRIVE_ROOT):
    os.makedirs(DRIVE_ROOT)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS ferramentas (id INTEGER PRIMARY KEY, nome TEXT, url TEXT)")

@app.route('/')
def home():
    return render_template('home.html', title="Home")

@app.route('/arquivos/')
@app.route('/arquivos/<path:subpath>')
def arquivos(subpath=""):
    abs_path = os.path.join(DRIVE_ROOT, subpath)
    
    # Segurança: Impede acesso fora da pasta drive
    if not os.path.abspath(abs_path).startswith(os.path.abspath(DRIVE_ROOT)):
        return "Acesso negado", 403

    if not os.path.exists(abs_path):
        return "Caminho não encontrado", 404

    # Se for um arquivo, faz o download
    if os.path.isfile(abs_path):
        return send_from_directory(os.path.dirname(abs_path), os.path.basename(abs_path))

    # Listagem de diretório
    items = []
    for item in os.listdir(abs_path):
        item_path = os.path.join(abs_path, item)
        is_dir = os.path.isdir(item_path)
        items.append({
            'name': item,
            'is_dir': is_dir,
            'rel_path': os.path.join(subpath, item).replace("\\", "/")
        })
    
    # Ordenar: Pastas primeiro, depois arquivos
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    
    parent_path = os.path.dirname(subpath).replace("\\", "/") if subpath else None
    return render_template('arquivos.html', title="Arquivos", items=items, current_path=subpath, parent_path=parent_path)

@app.route('/arquivos/upload', methods=['POST'])
def upload_file():
    subpath = request.form.get('path', '')
    file = request.files.get('file')
    if file:
        target_path = os.path.join(DRIVE_ROOT, subpath, file.filename)
        file.save(target_path)
    return redirect(url_for('arquivos', subpath=subpath))

@app.route('/arquivos/mkdir', methods=['POST'])
def make_dir():
    subpath = request.form.get('path', '')
    dirname = request.form.get('dirname', '')
    if dirname:
        target_path = os.path.join(DRIVE_ROOT, subpath, dirname)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
    return redirect(url_for('arquivos', subpath=subpath))

@app.route('/arquivos/delete/<path:filepath>')
def delete_item(filepath):
    abs_path = os.path.join(DRIVE_ROOT, filepath)
    if not os.path.abspath(abs_path).startswith(os.path.abspath(DRIVE_ROOT)):
        return "Operação não permitida", 403
    
    if os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
    
    return redirect(url_for('arquivos', subpath=os.path.dirname(filepath)))

@app.route('/arquivos/action', methods=['POST'])
def file_action():
    # Placeholder para funcionalidades de mover e copiar
    action = request.form.get('action')
    src = request.form.get('src')
    dest = request.form.get('dest')
    # Lógica de mover/copiar virá na próxima iteração conforme necessidade
    return redirect(url_for('arquivos', subpath=os.path.dirname(src)))

@app.route('/terminal')
def terminal():
    # Enviamos o diretório atual para iniciar o prompt
    return render_template('terminal.html', title="Terminal", cwd=os.getcwd())

@app.route('/terminal/executar', methods=['POST'])
def executar_comando():
    dados = request.get_json()
    comando = dados.get('comando', '')
    diretorio_atual = dados.get('diretorio', os.getcwd())

    try:
        # Trata o comando de mudança de diretório separadamente
        if comando.startswith('cd '):
            novo_path = comando[3:].strip()
            # Resolve o caminho (absoluto ou relativo)
            target_dir = os.path.abspath(os.path.join(diretorio_atual, novo_path))
            if os.path.isdir(target_dir):
                return jsonify({'output': '', 'cwd': target_dir})
            else:
                return jsonify({'output': f'cd: {novo_path}: No such file or directory\n', 'cwd': diretorio_atual})

        # Executa o comando no shell do sistema
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            cwd=diretorio_atual,
            timeout=15
        )
        
        output = resultado.stdout + resultado.stderr
        return jsonify({'output': output, 'cwd': diretorio_atual})
    except Exception as e:
        return jsonify({'output': f'Erro: {str(e)}\n', 'cwd': diretorio_atual})

if __name__ == '__main__':
    init_db()
    # No Termux, o host '::' permite que o servidor aceite conexões IPv4 e IPv6 ao mesmo tempo.
    app.run(host='::', port=8080, debug=True)