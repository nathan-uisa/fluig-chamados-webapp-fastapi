# Webapp de Abertura de Chamados - Fluig

Webapp para criação de chamados no sistema Fluig, com suporte para geração em lote através de planilhas Excel.

## Requisitos

- Python 3.8+
- Credenciais do Google OAuth configuradas
- Arquivo `.env` com as configurações da API Fluig

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```env
# Credenciais Google OAuth
GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_CLIENT_PROJECT_ID=seu_project_id
GOOGLE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GOOGLE_REDIRECT_URIS=http://127.0.0.1:3000/login/google/callback
GOOGLE_CLIENT_SECRET=seu_client_secret

# API Fluig
API_ENDPOINT_FUNCIONARIO=url_da_api_funcionario
API_ENDPOINT_CHAMADO=url_da_api_chamado
API_KEY=sua_api_key
API_NAME=nome_da_api_key_header
```

3. Certifique-se de que o redirect URI no Google Console está configurado como:
   `http://127.0.0.1:3000/login/google/callback`

## Execução

Execute o servidor:
```bash
python app.py
```

O servidor estará disponível em: `http://127.0.0.1:3000`

## Funcionalidades

### Autenticação
- Login com Google OAuth
- Validação de domínio (apenas emails @uisa.com.br)
- Sessão de usuário persistente
- Logout

### Abertura de Chamados
- Criação de chamados individuais
- Geração em lote através de planilhas Excel (.xlsx)
- Prévia dos chamados antes de criar
- Substituição automática de placeholders pelos valores da planilha

### Funcionalidades de Planilha
- Upload de planilhas Excel
- Processamento automático dos dados
- Suporte a placeholders no formato `<A>`, `<B>`, etc. (referência às colunas)
- Opção para ignorar primeira linha (cabeçalho)
- Controle de quantidade de chamados a criar

### Prévia de Chamados
- Visualização modal dos chamados processados
- Exibição de título e descrição com placeholders substituídos
- Indicadores de sucesso/erro por linha
- Informação sobre total de linhas disponíveis

## Como Usar

### Criar um Chamado Individual

1. Faça login com sua conta Google (@uisa.com.br)
2. Preencha o título e descrição do chamado
3. Clique em "Criar Chamado"

### Criar Múltiplos Chamados via Planilha

1. Prepare uma planilha Excel (.xlsx) com os dados
2. Faça login e acesse a página de chamados
3. Faça upload da planilha
4. Preencha o título e descrição usando placeholders:
   - Use `<A>` para referenciar a coluna A
   - Use `<B>` para referenciar a coluna B
   - E assim por diante
   
   Exemplo:
   - Título: `Chamado <A> - <B>`
   - Descrição: `Arquivo: <A>\nTamanho: <C> GB\nGMUD: <D>`

5. (Opcional) Marque "Ignorar primeira linha" se a primeira linha contém cabeçalhos
6. Defina a quantidade de chamados a criar
7. Clique em "Visualizar Prévia" para ver como os chamados ficarão
8. Clique em "Criar Chamado" para criar os chamados

### Exemplo de Planilha

|  CABEÇALHO A  |  CABEÇALHO B  |  CABEÇALHO C  |  CABEÇALHO D  |
|---------------|---------------|---------------|---------------|
| LINHA 1 COL A | LINHA 1 COL B | LINHA 1 COL C | LINHA 1 COL D |
| LINHA 2 COL A | LINHA 2 COL B | LINHA 2 COL C | LINHA 2 COL D |

Com o título: `Chamado <A>` e descrição: `Arquivo <A> com <C> GB - GMUD: <D>`, serão criados 2 chamados com os valores substituídos.

## Estrutura do Projeto

```
fluig-chamados-webapp-fastapi/
├── app.py                          # Aplicação principal FastAPI
├── requirements.txt                 # Dependências Python
├── .env                            # Variáveis de ambiente (criar)
├── temp.txt                        # Arquivo temporário de processamento
├── src/
│   ├── auth/
│   │   └── auth_api.py            # Autenticação de API
│   ├── classes/
│   │   └── tipos.py               # Modelos Pydantic
│   ├── modulos/
│   │   ├── abrir_chamados.py      # Módulo para abrir chamados em lote
│   │   ├── logger.py              # Configuração de logs
│   │   └── planilha.py            # Processamento de planilhas Excel
│   ├── rotas/
│   │   ├── rt_chamado.py          # Rotas de chamados
│   │   └── rt_login.py            # Rotas de autenticação
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Estilos com tema escuro
│   │   └── js/
│   │       └── chamado.js         # JavaScript para formulário de chamados
│   └── templates/
│       ├── chamado.html           # Template de criação de chamados
│       └── login.html             # Template de login
└── logs/
    └── api_fluig.log              # Arquivo de logs
```

## API Endpoints

### Autenticação
- `GET /login` - Página de login
- `GET /login/google` - Iniciar autenticação Google
- `GET /login/google/callback` - Callback do Google OAuth
- `GET /logout` - Logout do usuário

### Chamados
- `GET /chamado` - Página de criação de chamados
- `POST /chamado` - Criar chamado(s)
- `POST /chamado/preview` - Gerar prévia dos chamados (JSON)

## Tecnologias Utilizadas

- **FastAPI** - Framework web
- **Python 3.8+** - Linguagem de programação
- **Jinja2** - Templates HTML
- **Pydantic** - Validação de dados
- **openpyxl** - Processamento de planilhas Excel
- **configparser** - Processamento de arquivos de configuração
- **Google OAuth 2.0** - Autenticação

## Logs

Os logs são salvos em `logs/api_fluig.log` com rotação automática (máximo 10MB por arquivo, 5 backups).

## Notas

- O arquivo `temp.txt` é gerado automaticamente durante o processamento de planilhas
- A primeira linha da planilha pode ser ignorada se contiver cabeçalhos
- Os placeholders são case-insensitive ( `<A>` = `<a>` )
- A quantidade máxima de chamados por lote é configurável no formulário
