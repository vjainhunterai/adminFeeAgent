import os
import time

import paramiko

def trigger_airflow_dag():
    # ---------------------------------------------------------------------------
    # Read SSH config from environment variables (set by docker-compose .env)
    # This replaces the hardcoded Windows paths that don't work in Docker.
    #
    # Inside Docker, the .pem file is mounted at /app/secrets/airflow.pem
    # via a docker-compose volume (see docker-compose.yml)
    # ---------------------------------------------------------------------------
    hostname = os.getenv("SSH_HOST", "172.31.25.132")
    username = os.getenv("SSH_USERNAME", "ubuntu")
    pem_file = os.getenv("SSH_KEY_PATH", "/app/secrets/airflow.pem")

    start_airflow_cmd = os.getenv("AIRFLOW_START_CMD", "bash start_airflow.sh")
    command = os.getenv("AIRFLOW_TRIGGER_CMD",
                        "/home/ubuntu/run_airflow.sh dags trigger execute_adminFee_Data_Pipeline_v1")

    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to Airflow server
        ssh.connect(
            hostname=hostname,
            username=username,
            key_filename=pem_file
        )

        print(f"Connected to {hostname} as {username}")

        # Start Airflow services
        print("Starting Airflow services...")
        stdin, stdout, stderr = ssh.exec_command(start_airflow_cmd)

        start_out = stdout.read().decode()
        start_error = stderr.read().decode()

        if start_out:
            print(start_out)
        if start_error:
            print("Error while starting airflow:", start_error)

        print("Waiting for Airflow services to initialize...")
        time.sleep(15)

        # Trigger the DAG
        stdin, stdout, stderr = ssh.exec_command(command)

        dags = stdout.read().decode()

        if dags:
            print("Airflow output:", dags)

        ssh.close()

    except Exception as e:
        raise RuntimeError(f"SSH connection to {hostname} failed: {str(e)}")
