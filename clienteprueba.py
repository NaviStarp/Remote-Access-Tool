import socket
import sys

class Client:
    def __init__(self, host, port):
        self.server_address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect(self):
        try:
            self.socket.connect(self.server_address)
            print("Conectado al servidor")
            self.listen_for_commands()
        except Exception as e:
            print(f"Error al conectar con el servidor: {e}")
            sys.exit(1)
            
    def listen_for_commands(self):
        try:
            while True:
                command = self.socket.recv(4096).decode()
                if command:
                    print(f"Comando recibido: {command}")
                    response = self.execute_command(command)
                    self.socket.send(response.encode())
                else:
                    break
        except Exception as e:
            print(f"Error al recibir comando: {e}")
        finally:
            self.socket.close()
    
    def execute_command(self, command):
        # Aquí puedes procesar los comandos recibidos.
        # Por ejemplo, podrías usar 'os' para ejecutar comandos en el sistema.
        try:
            if command == "fecha":
                from datetime import datetime
                return f"Fecha actual: {datetime.now()}"
            else:
                return f"Comando no reconocido: {command}"
        except Exception as e:
            return f"Error al ejecutar comando: {e}"

if __name__ == "__main__":
    host = "127.0.0.1"  # Cambia a la dirección IP del servidor si es necesario
    port = 9999  # Debe coincidir con el puerto del servidor
    client = Client(host, port)
    client.connect()

