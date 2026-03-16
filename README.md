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
