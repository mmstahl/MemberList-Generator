"""
SFTP upload helper for Yedidya tools.
Used by both run.py (standalone) and the portal.
"""
import os
import paramiko


def upload_sftp(local_path, sftp_host, sftp_user, sftp_password, remote_path):
    """Upload a local file to a remote server via SFTP."""
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"File not found: {local_path}")

    transport = paramiko.Transport((sftp_host, 22))
    try:
        transport.connect(username=sftp_user, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            sftp.put(local_path, remote_path)
        finally:
            sftp.close()
    finally:
        transport.close()
