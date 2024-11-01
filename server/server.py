import pickle
import socket
import threading
import curses
import time


class ClientServ:
    """Clase para manejar la conexión con un cliente."""

    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address

    def execute_command(self, command: str):
        import subprocess
        try:
            # Run the command using subprocess
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return result.decode().strip()  # Return the output as a string
        except subprocess.CalledProcessError as e:
            print(f"[!] Error al ejecutar el comando: {e}")
            return None

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
        self.connected_clients = []  # List of connected clients
        self.running = False  # Control variable for the loop

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

                        # Create and store the new client connection
                        new_client = ClientServ(client_socket, client_address)
                        self.connected_clients.append(new_client)

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
            client.close()
        self.connected_clients = []

        if self.server:
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            print("[-] Servidor detenido.")

    def get_client_info(self):
        """Obtiene la información de los clientes conectados."""
        return [f"{client.client_address[0]}:{client.client_address[1]}" for client in self.connected_clients]


def curses_ui(server):
    """Crea una interfaz de usuario utilizando curses para mostrar los clientes conectados."""
    stdscr = curses.initscr()
    curses.curs_set(0)  # Ocultar el cursor
    stdscr.nodelay(1)  # No bloquear en espera de entrada
    stdscr.clear()

    while server.running:
        stdscr.clear()
        stdscr.addstr(0, 0, "[*] Clientes conectados:", curses.A_BOLD)
        clients_info = server.get_client_info()

        if clients_info:
            for idx, client_info in enumerate(clients_info):
                stdscr.addstr(idx + 1, 0, client_info)
        else:
            stdscr.addstr(1, 0, "No hay clientes conectados.")

        stdscr.addstr(len(clients_info) + 2, 0, "Presione 'q' para salir.")
        stdscr.refresh()

        # Check for quit key
        key = stdscr.getch()
        if key == ord('q'):
            break
        time.sleep(1)  # Sleep for a short period to reduce CPU usage

    curses.endwin()


if __name__ == "__main__":
    server = Server()

    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.start)
    server_thread.start()

    try:
        curses_ui(server)  # Start the curses UI
    except KeyboardInterrupt:
        print("\n[!] Deteniendo servidor manualmente.")
    finally:
        server.stop()
        server_thread.join()  # Wait for the server thread to finish
