import pickle
import socket
import threading
import curses
import time
from datetime import datetime


class ClientServ:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
        self.hostname = None
        self.os = None
        self.last_seen = datetime.now()

    def send_command(self, command):
        try:
            # Serializar el comando
            data = pickle.dumps(command)
            # Enviar primero la longitud
            self.socket.sendall(len(data).to_bytes(4, 'big'))
            # Enviar los datos
            self.socket.sendall(data)

            # Recibir la longitud de la respuesta
            response_length = int.from_bytes(self.socket.recv(4), 'big')
            # Recibir la respuesta completa
            response_data = b''
            while len(response_data) < response_length:
                chunk = self.socket.recv(min(4096, response_length - len(response_data)))
                if not chunk:
                    break
                response_data += chunk

            return pickle.loads(response_data)
        except Exception as e:
            return f"Error al enviar comando: {str(e)}"


class Server:
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = None
        self.host = host
        self.port = port
        self.connected_clients = []
        self.running = False

    def start(self):
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

                    # Recibir longitud de los datos
                    length_data = client_socket.recv(4)
                    if length_data:
                        length = int.from_bytes(length_data, 'big')
                        # Recibir datos del cliente
                        client_data = b''
                        while len(client_data) < length:
                            chunk = client_socket.recv(min(4096, length - len(client_data)))
                            if not chunk:
                                break
                            client_data += chunk

                        if client_data:
                            client_info = pickle.loads(client_data)
                            print(f"[+] Datos del cliente recibidos: {client_info}")

                            # Crear y almacenar la nueva conexión
                            new_client = ClientServ(client_socket, client_address)
                            self.connected_clients.append(new_client)

                except Exception as e:
                    print(f"[!] Error al aceptar conexión: {e}")
                    continue

        except Exception as e:
            print(f"[!] Error al iniciar el servidor: {e}")
            self.stop()

    def stop(self):
        self.running = False
        self.connected_clients = []
        if self.server:
            try:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
            except Exception as e:
                print(f"Error al detener el servidor: {e}")
                pass
            print("[-] Servidor detenido.")

    def get_client_info(self):
        return [f"{client.address[0]}:{client.address[1]}" for client in self.connected_clients]




if __name__ == "__main__":
    server = Server()

    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.start)
    server_thread.start()

