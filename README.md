# CasaPy

Servidor caseiro leve em Python para rodar no Termux (por exemplo, em um Redmi10C).

## Recursos

- ✅ Autenticação com login/senha (SQLite)
- ✅ Armazenamento remoto isolado por usuário
- ✅ Interface responsiva para desktop e mobile
- ✅ Suporte a IPv4 e IPv6
- ✅ Informações do sistema em tempo real
- ✅ Gerenciador de arquivos web
- 🔄 Gerenciamento de serviços (em desenvolvimento)

## Como instalar

No Termux:

```bash
pkg update && pkg upgrade
pkg install python
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Como rodar

```bash
python -m app.main
```

Abra no navegador ou acesse de outra máquina na mesma rede:

- IPv4: `http://<IPv4-do-aparelho>:8080`
- IPv6: `http://[<IPv6-do-aparelho>]:8080`

O servidor usa host `::` para suportar conexões IPv6 e IPv4 quando o sistema permite o mapeamento de endereços.

## Primeiros passos

1. Acesse `http://localhost:8080/register` para criar uma conta
2. Faça login com suas credenciais
3. Use o home para navegar para informações ou armazenamento

## Estrutura do projeto

```
app/
├── main.py                # Ponto de entrada
├── server.py              # Criação do FastAPI
├── config.py              # Configurações
├── auth.py                # Utilitários de autenticação
├── db.py                  # SQLite database
├── routes/
│   ├── auth/              # Login/register/logout
│   ├── home.py            # Home page
│   ├── info.py            # Informações do sistema
│   ├── storage.py         # Gerenciador de arquivos
│   └── api/               # API endpoints
├── services/
│   ├── system.py          # Info do sistema
│   ├── device.py          # Controle do aparelho
│   └── storage.py         # Gerenciamento de armazenamento
├── models/
│   ├── user.py            # Modelos e autenticação
│   └── device.py          # Modelos de dispositivo
├── templates/             # HTML/Jinja2
└── static/
    ├── css/               # Estilos responsivos
    └── js/                # JavaScript
data/
└── users.db               # Banco de dados SQLite
```

## Testando

```bash
python -m pytest
```

## Notas de desenvolvimento

- Senhas são hash com SHA256
- Cookies HTTP-only para segurança
- Cada usuário tem sua pasta de armazenamento isolada
- CSS responsivo com breakpoints em 768px e 480px
