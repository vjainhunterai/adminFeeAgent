docker exec -it adminfee-agent ssh -i /app/.ssh/id_rsa -o StrictHostKeyChecking=no ubuntu@host.docker.internal echo "SSH works"



Found it. The issue is in `docker-compose.yml` line 50:

```yaml
- ~/.ssh/adminfee_key:/app/.ssh/id_rsa:ro
```

**The problem:** If the file `~/.ssh/adminfee_key` doesn't exist on the host, Docker creates `/app/.ssh/id_rsa` as a **directory** instead of mounting it as a file.

## Fix

Run these commands on your EC2 host:

### 1. Generate the SSH key (if not already done)

```bash
ssh-keygen -t rsa -N "" -f ~/.ssh/adminfee_key
cat ~/.ssh/adminfee_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/adminfee_key
```

### 2. Verify the file exists

```bash
ls -la ~/.ssh/adminfee_key
# Should show a FILE, not a directory
# Example: -rw------- 1 ubuntu ubuntu 2602 ... /home/ubuntu/.ssh/adminfee_key
```

### 3. Restart the containers

```bash
docker-compose down
docker-compose up -d --build
```

### 4. Verify inside the container

```bash
sudo docker exec adminfee-backend ls -la /app/.ssh/id_rsa
# Should show a FILE, not a directory
```

### 5. Re-test SSH

```bash
sudo docker exec adminfee-backend python -c "
import paramiko, os
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(
    hostname=os.getenv('SSH_HOST', 'host.docker.internal'),
    username=os.getenv('SSH_USERNAME', 'ubuntu'),
    key_filename=os.getenv('SSH_KEY_PATH', '/app/.ssh/id_rsa')
)
print('SSH to host: OK')
ssh.close()
"
```

**Root cause summary:** When Docker tries to bind-mount a host file that doesn't exist, it creates a directory at the mount point instead. The fix is simply to create the SSH key file on the host **before** starting the container.

=========================



Here are the **final end-to-end steps** to deploy and run the AdminFee Agent:

---

## Step 1: Prerequisites on your EC2/Ubuntu server

```bash
# Make sure Docker and Docker Compose are installed
docker --version
docker-compose --version

# Make sure these are already running on the host:
# - Ollama LLM (port 11434) with llama3.1:8b loaded
# - Airflow (with the DAG: execute_adminFee_Data_Pipeline_v1)
# - MySQL RDS is accessible
```

---

## Step 2: Clone the repo

```bash
cd /home/ubuntu
git clone <your-repo-url> adminFeeAgent
cd adminFeeAgent
```

---

## Step 3: Setup `.env`

```bash
cp .env.example .env
# Edit .env if needed (DB password, LLM URL, etc.)
nano .env
```

Your `.env` should look like:
```env
# --- MySQL Database ---
DB_USER=kishore
DB_PASSWORD=Gpohealth!#!
DB_HOST=dev-db-test.c969yoyq9cyy.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_NAME=joblog_metadata

# --- Ollama LLM Server ---
LLM_BASE_URL=http://172.31.27.7:11434
LLM_MODEL=llama3.1:8b

# --- S3 Bucket ---
S3_BUCKET=etlhunter
S3_INPUT_KEY=adminfee_input/input_template.xlsx
S3_OUTPUT_PREFIX=adminfee_output

# --- SSH / Airflow (same machine) ---
SSH_HOST=host.docker.internal
SSH_USERNAME=ubuntu
SSH_KEY_PATH=/app/.ssh/id_rsa
AIRFLOW_START_CMD=bash start_airflow.sh
AIRFLOW_TRIGGER_CMD=/home/ubuntu/run_airflow.sh dags trigger execute_adminFee_Data_Pipeline_v1
```

---

## Step 4: Setup SSH key (one-time only)

```bash
# Generate a dedicated key for container → host SSH
ssh-keygen -t rsa -N "" -f ~/.ssh/adminfee_key

# Allow this key to SSH into the same machine
cat ~/.ssh/adminfee_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/adminfee_key

# Verify it works
ssh -i ~/.ssh/adminfee_key ubuntu@localhost "echo OK"
# Should print: OK
```

---

## Step 5: Build and start

```bash
cd /home/ubuntu/adminFeeAgent
docker-compose up -d --build
```

This builds two containers:
| Container | What it does | Port |
|-----------|-------------|------|
| `adminfee-backend` | FastAPI + Uvicorn (API server) | 8000 |
| `adminfee-frontend` | Nginx + React (UI) | 80 |

---

## Step 6: Verify everything is running

```bash
# Check containers are up
docker ps

# Check backend health
curl http://localhost:8000/api/health
# Should return: {"status":"ok","service":"adminFee-agent-api"}

# Check frontend is serving
curl -s http://localhost:80 | head -5
# Should return HTML

# Check backend can SSH to host (Airflow)
docker exec adminfee-backend python -c "
import paramiko, os
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(
    hostname=os.getenv('SSH_HOST', 'host.docker.internal'),
    username=os.getenv('SSH_USERNAME', 'ubuntu'),
    key_filename=os.getenv('SSH_KEY_PATH', '/app/.ssh/id_rsa')
)
print('SSH to host: OK')
ssh.close()
"

# Check backend can reach MySQL
docker exec adminfee-backend python -c "
from config import DB_URI
from sqlalchemy import create_engine, text
engine = create_engine(DB_URI)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('MySQL: OK')
"

# Check backend can reach Ollama LLM
docker exec adminfee-backend python -c "
import os, urllib.request
url = os.getenv('LLM_BASE_URL', 'http://172.31.27.7:11434')
resp = urllib.request.urlopen(url)
print('Ollama: OK')
"
```

---

## Step 7: Open the app

Open browser and go to:

```
http://<your-ec2-public-ip>
```

You'll see the **hunterAI AdminFee** dashboard with 3 workflows:

```
┌─────────────────────────────────────────────────────────────┐
│  hunterAI AdminFee                                          │
│  Dashboard | Process New | Analyze Existing | Status Monitor│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Process NEW  │ │ Analyze      │ │ Status       │        │
│  │ Contracts    │ │ EXISTING     │ │ Monitor      │        │
│  │              │ │ Contracts    │ │              │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 8: Use the app

### Workflow 1 — Process NEW Contracts (click "Process New")

1. Choose **Manual Entry** or **S3 Excel File**
   - Manual: type `PP-OR-123, PP-NS-345`
   - File: upload `input_template.xlsx` to `s3://etlhunter/adminfee_input/`
2. Enter **Delivery Name**: `Delivery_9`
3. Click **Start Processing**
   - Backend inserts contracts into `admin_fee_metadata`
   - SSH's to host → starts Airflow → triggers the DAG
   - Shows pipeline status: `TRIGGERED`
   - Shows output path: `s3://etlhunter/adminfee_output/Delivery_9`
4. Click **Generate Summary Report** after processing completes
   - Compares PO spend vs Report spend per contract
   - LLM generates a reconciliation report

### Workflow 2 — Monitor Status (click "Status Monitor")

1. See real-time **Total / Completed / In Progress** counts
2. Toggle **Auto-refresh (60s)** to keep polling
3. Enter **Delivery Name** and ask questions:
   - "How many contracts are completed?"
   - "Which contracts are still processing?"
   - AI generates SQL, queries DB, explains results

### Workflow 3 — Analyze EXISTING Contracts (click "Analyze Existing")

1. Enter **Delivery Name**: `Delivery 9`
2. Click **Connect** → normalizes to `delivery_9`, fetches contracts
3. Ask questions in the chat:
   - "What is the total spend?"
   - "Which supplier has highest PO spend?"
   - "Compare spend across all contracts"
   - AI generates SQL → runs it → analyzes → formats for business

---

## Troubleshooting

```bash
# View backend logs
docker logs adminfee-backend -f

# View frontend logs
docker logs adminfee-frontend -f

# Restart everything
docker-compose down && docker-compose up -d --build

# SSH test from inside container
docker exec -it adminfee-backend bash
ssh -i /app/.ssh/id_rsa ubuntu@host.docker.internal "echo OK"
```

---

## Summary of what's running

```
Browser → :80 (Nginx/React)
              │
              ├── /          → React SPA (Dashboard, Process, Analyze, Status)
              │
              └── /api/*     → proxy to :8000 (FastAPI)
                                    │
                    ┌───────────────┼───────────────┐──────────────┐
                    │               │               │              │
                    ▼               ▼               ▼              ▼
              MySQL RDS       Ollama LLM        S3 Bucket     Airflow
              (DB queries)    (llama3.1:8b)     (etlhunter)   (same host
              (SQLAlchemy)    (LangChain)       (boto3)        via SSH)
```---------------------------------------------------------------------------------------


All done. Here's the complete step-by-step Docker deployment guide:

Docker Deployment — Step by Step
STEP 1: Install Docker on your EC2
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker ubuntu     # so you don't need sudo
newgrp docker                       # activate group now

What this does: Installs Docker engine + Compose plugin. Adds your user to the docker group so you can run commands without sudo.

STEP 2: Clone the repo
cd /home/ubuntu
git clone https://github.com/vjainhunterai/adminFeeAgent.git
cd adminFeeAgent
git checkout claude/frontend-admin-fee-wrapper-TB4Sc

What this does: Downloads all code to your server and switches to the branch with the frontend wrapper.

STEP 3: Create the .env file
cp .env.example .env
nano .env

Fill in your real values:

DB_USER=kishore
DB_PASSWORD=Gpohealth!#!
DB_HOST=dev-db-test.c969yoyq9cyy.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_NAME=joblog_metadata
LLM_BASE_URL=http://172.31.27.7:11434
LLM_MODEL=llama3.1:8b
AIRFLOW_HOST=ubuntu@172.31.25.132
AIRFLOW_CMD=/home/ubuntu/run_airflow.sh dags trigger execute_adminfee_data_pipeline_v1
EXCEL_INPUT_PATH=/home/ubuntu/adminfee_data_pipeline/Data/agent_input/contracts.xlsx

What this does: Docker Compose reads this file and injects these values as environment variables into the backend container. Your passwords stay outside of code.

STEP 4: Build the Docker images
docker-compose build

What happens internally:

Container	Build steps
backend	Python 3.11-slim → installs pip packages → copies full repo (needs prompts/) → sets up uvicorn
frontend	Stage 1: Node 20 → npm install → npm run build → produces dist/ static files
Stage 2: Nginx 1.25 → copies dist/ files → copies nginx.conf
The frontend build is multi-stage — final image has NO Node.js, only tiny Nginx (~25MB).

STEP 5: Start everything
docker-compose up -d

-d = detached (runs in background).

What happens:

Backend container starts → uvicorn launches with 2 workers on port 8000
Docker waits for backend health check to pass (/api/health returns OK)
Frontend container starts → Nginx serves on port 80
STEP 6: Verify it's running
# Check both containers are "Up" and healthy
docker-compose ps

# Check backend health
curl http://localhost:8000/api/health
# → {"status":"ok","service":"adminFee-agent-api"}

# Check frontend + Nginx proxy
curl http://localhost/api/health
# → {"status":"ok","service":"adminFee-agent-api"}
# (this went: browser → Nginx:80 → proxy → backend:8000)

Open browser: http://<your-ec2-private-ip>

STEP 7: View logs (if something goes wrong)
# All logs together
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend/Nginx only
docker-compose logs -f frontend

Log message	Meaning
Uvicorn running on 0.0.0.0:8000	Backend started OK
Connection refused 172.31.27.7:11434	Ollama LLM server not reachable
Access denied for user 'kishore'	Wrong DB password in .env
502 Bad Gateway	Backend not ready yet, Nginx can't reach it
STEP 8: Stop / Restart / Rebuild
# Stop everything
docker-compose down

# Restart (no rebuild)
docker-compose up -d

# Rebuild after code changes, then restart
docker-compose up -d --build

# Full reset (remove images too)
docker-compose down --rmi all
docker-compose up -d --build

STEP 9: AWS Security Group
Open port 80 in your EC2 security group:

Type	Port	Source
HTTP	80	Your VPC CIDR (e.g. 172.31.0.0/16) or specific IPs
Port 8000 is optional (for direct API testing). Nginx on port 80 already proxies /api to it.

How it all connects
User Browser
     │
     ▼ port 80
┌──────────────────────────────┐
│  frontend container (Nginx)  │
│                              │
│  /             → React app   │  (static HTML/JS/CSS)
│  /api/*        → proxy ──────┼──→ backend:8000
└──────────────────────────────┘
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                     MySQL RDS    Ollama LLM   Airflow
                     (port 3306)  (port 11434)  (SSH)

All 3 external services are on the same 172.31.x.x private VPC, so the Docker container can reach them directly.
