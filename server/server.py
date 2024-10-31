import pickle
import socket
from client.client import Client

class ClientServ:
    """Clase para manejar la conexión con un cliente."""
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address

    def close(self):
        """Cierra la conexión del cliente."""
        self.client_socket.close()
        print(f"[-] Conexión cerrada para {self.client_address}")


class Server:
    """Clase para un servidor de escucha de conexiones."""
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = None
        self.host = host
        self.port = port
        self.connected_clients = []
        self.running = False  # Variable de control para el bucle

    def start(self):
        """Inicia el servidor."""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen()
            self.running = True
            print(f"[*] Servidor escuchando en {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, client_address = self.server.accept()
                    print(f"[+] Nueva conexión desde {client_address}")

                    client_data = client_socket.recv(4096)
                    if client_data:
                        # Deserializar los datos como un diccionario
                        client_info = pickle.loads(client_data)
                        print(f"[+] Datos del cliente recibidos: {client_info}")
                        # Aquí puedes enviar un mensaje de respuesta al cliente, si es necesario
                        response = {"message": "Conexión exitosa"}
                        client_socket.sendall(pickle.dumps(response))

                        New_client = Client( client_socket=client_socket)
                        print(f"[+] Cliente creado: {New_client.client_socket.getsockname()}")
                        self.connected_clients.append(New_client)

                except Exception as e:
                    print(f"[!] Error al aceptar conexión: {e}")
                    break

        except Exception as e:
            print(f"[!] Error al iniciar el servidor: {e}")
            self.stop()  # Detiene y limpia en caso de error

    def stop(self):
        """Detiene el servidor y cierra todas las conexiones."""
        self.running = False
        for client in self.connected_clients:
            if client.client_socket:
                client.close()
        self.connected_clients = []

        if self.server:
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            print("[-] Servidor detenido.")


if __name__ == "__main__":
    server = Server()
    try:
        server.start()  # Inicia el servidor y espera una conexión
    except KeyboardInterrupt:
        print("\n[!] Deteniendo servidor manualmente.")
        server.stop()