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
        conn.execute("CREATE TABLE IF NOT EXISTS lembretes (id INTEGER PRIMARY KEY AUTOINCREMENT, tarefa TEXT, data_hora TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS notas (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, conteudo TEXT, data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, chave TEXT UNIQUE, valor TEXT)")
        # Valor padrão para o nome do usuário
        conn.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('usuario_nome', 'Usuário')")

@app.route('/')
def home():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        lembretes = conn.execute("SELECT * FROM lembretes WHERE data_hora >= datetime('now', 'localtime') ORDER BY data_hora ASC LIMIT 3").fetchall()
        nome = conn.execute("SELECT valor FROM config WHERE chave = 'usuario_nome'").fetchone()['valor']
    return render_template('home.html', title="Home", lembretes=lembretes, nome=nome)

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

# --- AGENDA ---
@app.route('/agenda')
def agenda():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        itens = conn.execute("SELECT * FROM lembretes ORDER BY data_hora ASC").fetchall()
    return render_template('agenda.html', title="Agenda", itens=itens)

@app.route('/agenda/add', methods=['POST'])
def add_agenda():
    tarefa = request.form.get('tarefa')
    data_hora = request.form.get('data_hora')
    if tarefa and data_hora:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO lembretes (tarefa, data_hora) VALUES (?, ?)", (tarefa, data_hora.replace('T', ' ')))
    return redirect(url_for('agenda'))

@app.route('/agenda/delete/<int:id>')
def delete_agenda(id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM lembretes WHERE id = ?", (id,))
    return redirect(url_for('agenda'))

# --- NOTAS ---
@app.route('/notas')
def notas():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        notas_list = conn.execute("SELECT * FROM notas ORDER BY data_criacao DESC").fetchall()
    return render_template('notas.html', title="Notas", notas=notas_list)

@app.route('/notas/add', methods=['POST'])
def add_nota():
    titulo = request.form.get('titulo')
    conteudo = request.form.get('conteudo')
    if titulo:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO notas (titulo, conteudo) VALUES (?, ?)", (titulo, conteudo))
    return redirect(url_for('notas'))

@app.route('/notas/edit/<int:id>', methods=['POST'])
def edit_nota(id):
    titulo = request.form.get('titulo')
    conteudo = request.form.get('conteudo')
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE notas SET titulo = ?, conteudo = ? WHERE id = ?", (titulo, conteudo, id))
    return redirect(url_for('notas'))

@app.route('/notas/delete/<int:id>')
def delete_nota(id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM notas WHERE id = ?", (id,))
    return redirect(url_for('notas'))

# --- CONFIGURAÇÕES ---
@app.route('/configuracoes')
def configuracoes():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        configs = conn.execute("SELECT * FROM config").fetchall()
        # Transformar em dicionário para facilitar no template
        cfg_dict = {row['chave']: row['valor'] for row in configs}
        
        # Estatísticas simples
        stats = {
            'arquivos': sum([len(files) for r, d, files in os.walk(DRIVE_ROOT)]),
            'notas': conn.execute("SELECT COUNT(*) FROM notas").fetchone()[0],
            'lembretes': conn.execute("SELECT COUNT(*) FROM lembretes").fetchone()[0]
        }
    return render_template('configuracoes.html', title="Configurações", configs=cfg_dict, stats=stats)

@app.route('/configuracoes/update', methods=['POST'])
def update_config():
    nome = request.form.get('usuario_nome')
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE config SET valor = ? WHERE chave = 'usuario_nome'", (nome,))
    return redirect(url_for('configuracoes'))

if __name__ == '__main__':
    init_db()
    # No Termux, o host '::' permite que o servidor aceite conexões IPv4 e IPv6 ao mesmo tempo.
    app.run(host='::', port=8080, debug=True)