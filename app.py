from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, jsonify, send_file
import sqlite3, os, shutil, subprocess, zipfile, io, json
from datetime import datetime, timedelta

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
        conn.execute("""CREATE TABLE IF NOT EXISTS lembretes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tarefa TEXT, 
            descricao TEXT,
            data_hora TEXT, 
            repeticao TEXT DEFAULT 'Nenhuma',
            feito INTEGER DEFAULT 0
        )""")
        conn.execute("CREATE TABLE IF NOT EXISTS notas (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, conteudo TEXT, data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, chave TEXT UNIQUE, valor TEXT)")
        conn.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('usuario_nome', 'Usuário')")
        conn.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('ssh_cmd', 'ssh u0_a288@[::1] -p 8022')")
        conn.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('ssh_password', '')")

def get_sys_stats():
    stats = {'cpu': 0, 'ram': 0, 'bateria': 0}
    try:
        # Bateria
        try:
            bat_out = subprocess.check_output(['termux-battery-status'], timeout=2).decode('utf-8')
            stats['bateria'] = json.loads(bat_out).get('percentage', 0)
        except:
            if os.path.exists("/sys/class/power_supply/battery/capacity"):
                with open("/sys/class/power_supply/battery/capacity", "r") as f:
                    stats['bateria'] = int(f.read().strip())

        # RAM
        try:
            ram_out = subprocess.check_output(['free'], timeout=2).decode('utf-8')
            for line in ram_out.splitlines():
                if line.startswith("Mem:"):
                    parts = line.split()
                    total, available = int(parts[1]), int(parts[6])
                    stats['ram'] = round(((total - available) / total) * 100, 1)
        except: pass

        # CPU
        with open('/proc/loadavg', 'r') as f:
            load = float(f.read().split()[0])
            stats['cpu'] = min(round((load / 8) * 100, 1), 100)
    except Exception as e:
        print(f"Erro ao obter stats: {e}")
    return stats

@app.route('/')
def home():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        lembretes = conn.execute("SELECT * FROM lembretes WHERE feito = 0 AND data_hora >= datetime('now', 'localtime') ORDER BY data_hora ASC LIMIT 3").fetchall()
        nome = conn.execute("SELECT valor FROM config WHERE chave = 'usuario_nome'").fetchone()['valor']
    return render_template('home.html', title="Home", lembretes=lembretes, nome=nome, stats=get_sys_stats())

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
    files = request.files.getlist('file')
    for file in files:
        if file.filename:
            target_path = os.path.join(DRIVE_ROOT, subpath, file.filename)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            file.save(target_path)
    return redirect(url_for('arquivos', subpath=subpath))

@app.route('/arquivos/download_zip')
def download_zip():
    subpath = request.args.get('path', '')
    abs_path = os.path.join(DRIVE_ROOT, subpath)
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(abs_path):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path, os.path.relpath(file_path, abs_path))
    memory_file.seek(0)
    return send_file(memory_file, download_name=f'{os.path.basename(abs_path) or "drive"}.zip', as_attachment=True)

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
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        configs = conn.execute("SELECT chave, valor FROM config WHERE chave IN ('ssh_cmd', 'ssh_password')").fetchall()
        cfg_dict = {row['chave']: row['valor'] for row in configs}
    return render_template('terminal.html', title="Terminal", cwd=os.getcwd(), ssh_cmd=cfg_dict.get('ssh_cmd', ''))

@app.route('/terminal/executar', methods=['POST'])
def executar_comando():
    dados = request.get_json()
    comando = dados.get('comando', '')
    diretorio_atual = dados.get('diretorio', os.getcwd())

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        configs = conn.execute("SELECT chave, valor FROM config WHERE chave IN ('ssh_cmd', 'ssh_password')").fetchall()
        cfg = {row['chave']: row['valor'] for row in configs}

    try:
        if cfg.get('ssh_cmd'):
            # Uso de sshpass para injetar senha no SSH
            ssh_prefix = f"sshpass -p '{cfg['ssh_password']}' {cfg['ssh_cmd']}"
            if comando.startswith('cd '):
                remote_cmd = f"cd '{comando[3:].strip()}' && pwd"
                final_cmd = f"{ssh_prefix} \"{remote_cmd}\""
            else:
                final_cmd = f"{ssh_prefix} \"cd '{diretorio_atual}' && {comando}\""
            
            result = subprocess.run(final_cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            new_cwd = output.strip() if comando.startswith('cd ') else diretorio_atual
            return jsonify({'output': output if not comando.startswith('cd ') else '', 'cwd': new_cwd})
        else:
            # Execução local se SSH não configurado
            if comando.startswith('cd '):
                target_dir = os.path.abspath(os.path.join(diretorio_atual, comando[3:].strip()))
                if os.path.isdir(target_dir):
                    return jsonify({'output': '', 'cwd': target_dir})
                return jsonify({'output': 'Diretório não encontrado\n', 'cwd': diretorio_atual})
            
            result = subprocess.run(comando, shell=True, capture_output=True, text=True, cwd=diretorio_atual, timeout=15)
            return jsonify({'output': result.stdout + result.stderr, 'cwd': diretorio_atual})
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
    desc = request.form.get('descricao')
    data_hora = request.form.get('data_hora')
    rep = request.form.get('repeticao')
    if tarefa and data_hora:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO lembretes (tarefa, descricao, data_hora, repeticao) VALUES (?, ?, ?, ?)", 
                        (tarefa, desc, data_hora.replace('T', ' '), rep))
    return redirect(url_for('agenda'))

@app.route('/agenda/edit/<int:id>', methods=['POST'])
def edit_agenda(id):
    tarefa = request.form.get('tarefa')
    desc = request.form.get('descricao')
    data_hora = request.form.get('data_hora')
    rep = request.form.get('repeticao')
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE lembretes SET tarefa=?, descricao=?, data_hora=?, repeticao=? WHERE id=?", 
                    (tarefa, desc, data_hora.replace('T', ' '), rep, id))
    return redirect(url_for('agenda'))

@app.route('/agenda/toggle/<int:id>')
def toggle_agenda(id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        item = conn.execute("SELECT * FROM lembretes WHERE id = ?", (id,)).fetchone()
        novo_status = 1 if item['feito'] == 0 else 0
        
        # Lógica de repetição: se marcar como feito e tiver repetição, cria o próximo
        if novo_status == 1 and item['repeticao'] != 'Nenhuma':
            data_atual = datetime.strptime(item['data_hora'], '%Y-%m-%d %H:%M')
            if item['repeticao'] == 'Diário': nova_data = data_atual + timedelta(days=1)
            elif item['repeticao'] == 'Semanal': nova_data = data_atual + timedelta(weeks=1)
            elif item['repeticao'] == 'Mensal': nova_data = data_atual + timedelta(days=30)
            conn.execute("INSERT INTO lembretes (tarefa, descricao, data_hora, repeticao) VALUES (?, ?, ?, ?)",
                        (item['tarefa'], item['descricao'], nova_data.strftime('%Y-%m-%d %H:%M'), item['repeticao']))
        
        conn.execute("UPDATE lembretes SET feito = ? WHERE id = ?", (novo_status, id))
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
    ssh_cmd = request.form.get('ssh_cmd')
    ssh_pass = request.form.get('ssh_password')
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE config SET valor = ? WHERE chave = 'usuario_nome'", (nome,))
        conn.execute("UPDATE config SET valor = ? WHERE chave = 'ssh_cmd'", (ssh_cmd,))
        conn.execute("UPDATE config SET valor = ? WHERE chave = 'ssh_password'", (ssh_pass,))
    return redirect(url_for('configuracoes'))

if __name__ == '__main__':
    init_db()
    # No Termux, o host '::' permite que o servidor aceite conexões IPv4 e IPv6 ao mesmo tempo.
    app.run(host='::', port=8080, debug=True)