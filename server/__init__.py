# server/server.py
import socket
from client.client import Client  
class Server:
    """Clase para un servidor de escucha de conexiones."""
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = None
        self.host = host
        self.port = port
        self.connected_clients = []

    def start(self):
        """Inicia el servidor."""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            print(f"[*] Servidor escuchando en {self.host}:{self.port}")

            while True:
                client_socket, client_address = self.server.accept()
                client = Client(client_socket, client_address)  # Crear objeto Client
                self.connected_clients.append(client)


        except Exception as e:
            print(f"[!] Error al iniciar el servidor: {e}")

    def stop(self):
        """Detiene el servidor y cierra todas las conexiones."""
        for client in self.connected_clients:
            client.close()
        self.connected_clients = []
        print("[-] Servidor detenido.")



if __name__ == "__main__":
    server = Server()

    server.start()  # Inicia el servidor y espera una conexión

