import os
import time

import paramiko


def trigger_airflow_dag():
    """
    Trigger Airflow DAG via SSH to the host machine.

    Since Airflow runs on the SAME machine as Docker, the container
    SSH's to host.docker.internal using a mounted SSH key from the
    host's ~/.ssh/adminfee_key (no separate secrets/ folder needed).
    """
    hostname = os.getenv("SSH_HOST", "host.docker.internal")
    username = os.getenv("SSH_USERNAME", "ubuntu")
    key_path = os.getenv("SSH_KEY_PATH", "/app/.ssh/id_rsa")

    start_airflow_cmd = os.getenv("AIRFLOW_START_CMD", "bash start_airflow.sh")
    command = os.getenv("AIRFLOW_TRIGGER_CMD",
                        "/home/ubuntu/run_airflow.sh dags trigger execute_adminFee_Data_Pipeline_v1")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=hostname,
            username=username,
            key_filename=key_path
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
