
# EB3 Jobs — Backend MVP (FastAPI + PostgreSQL)

Este projeto é um **passo a passo do zero**, com duas formas de rodar:
1) **Com Docker (recomendado)** — um comando sobe Postgres + API.
2) **Localmente (sem Docker)** — usando Python e um Postgres já instalado.

## 0) Pré-requisitos

### Opção A: Docker
- Docker e Docker Compose instalados.

### Opção B: Local (sem Docker)
- Python 3.10+
- PostgreSQL 14+ (comando `psql` funcionando)
- `pip`

---

## 1) Estrutura do projeto

```
eb3-jobs-mvp/
├─ app.py                # API FastAPI
├─ requirements.txt
├─ Dockerfile            # API container
├─ docker-compose.yml    # Postgres + API
├─ .env.example          # exemplo de variáveis de ambiente
├─ sql/
│   ├─ 01_schema.sql     # cria tabelas
│   └─ 02_seed.sql       # dados de exemplo
└─ ingest_partner.py     # ingestão de feed JSON
```

---

## 2) Rodando com Docker (modo mais simples)

1. **Clonar/baixar** este projeto.
2. Crie um arquivo `.env` baseado em `.env.example` (pode só copiar):
   ```bash
   cp .env.example .env
   ```
3. Suba os serviços:
   ```bash
   docker compose up --build
   ```
   - Isto vai subir **Postgres** e a **API** na porta **8000**.
   - A primeira vez ele cria o banco e aplica os SQLs automaticamente.

4. Verifique a API:
   - Health: http://localhost:8000/health
   - Listar jobs: http://localhost:8000/jobs

5. (Opcional) Abrir o Swagger (docs):  
   http://localhost:8000/docs

6. Derrubar os serviços:
   ```bash
   docker compose down
   ```

> Caso queira resetar o banco, apague o volume `pgdata`:
```bash
docker compose down -v
docker compose up --build
```

---

## 3) Rodando localmente (sem Docker)

> Você precisa ter um **PostgreSQL** instalado e rodando localmente.

1. Crie um virtualenv e instale as dependências:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Crie o banco de dados:
   ```bash
   createdb eb3jobs
   psql eb3jobs -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
   psql eb3jobs -f sql/01_schema.sql
   psql eb3jobs -f sql/02_seed.sql
   ```

3. Configure a variável de ambiente para a API:
   ```bash
   export DATABASE_URL="postgresql+psycopg2://$USER:@localhost:5432/eb3jobs"
   # Windows PowerShell:
   # $env:DATABASE_URL="postgresql+psycopg2://USERNAME:@localhost:5432/eb3jobs"
   ```

4. Rode a API:
   ```bash
   uvicorn app:app --reload --port 8000
   ```

5. Teste:
   - http://127.0.0.1:8000/health
   - http://127.0.0.1:8000/jobs

---

## 4) Ingestão de parceiro (exemplo)

1. Crie um `partner_feed.json` na raiz com este conteúdo:
   ```json
   [
     {
       "employer": "Pioneer Logistics",
       "title": "Warehouse Associate",
       "city": "Houston",
       "state": "tx",
       "wage": 17.25,
       "status": "FILING_NOW",
       "duties": "Loading/unloading, inventory, packing.",
       "apply_url": "https://seuportal.example/apply/warehouse-tx",
       "posted_date": "2025-10-18"
     }
   ]
   ```

2. Execute a ingestão (local):
   ```bash
   export DATABASE_URL="postgresql+psycopg2://$USER:@localhost:5432/eb3jobs"
   python ingest_partner.py
   ```

3. Confira os dados:
   - http://127.0.0.1:8000/jobs?state=TX

---

## 5) Próximos passos

- Adicionar filtros extras (salário mínimo, cidade).
- Endpoint `POST /subscribe` para newsletter/waitlist.
- Painel admin simples (trocar `SOLD_OUT`/`FILING_NOW`).
- Frontend (Next.js) com página `/eb3-jobs` + i18n (PT/EN/ES).

Boa construção! 🚀
