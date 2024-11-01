import socket
import threading
import curses
import json
from datetime import datetime
import sys

class Client:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
        self.hostname = None
        self.os = None
        self.last_seen = datetime.now()
        
    def send_command(self, command):
        try:
            self.socket.send(command.encode())
            response = self.socket.recv(4096).decode()
            return response
        except:
            return "Error al enviar comando"

class ServerUI:
    def __init__(self):
        self.clients = {}
        self.selected_client = None
        self.command_history = []
        self.current_command = ""
        self.messages = []
        
    def setup_curses(self):
        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)
        
    def cleanup_curses(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()
        
    def draw_screen(self):
        self.screen.clear()
        height, width = self.screen.getmaxyx()
        
        # Título
        title = "Control Remoto - Servidor"
        self.screen.addstr(0, (width - len(title)) // 2, title, curses.color_pair(1))
        
        # Lista de clientes
        self.screen.addstr(2, 2, "Clientes Conectados:", curses.color_pair(2))
        client_y = 3
        for i, (addr, client) in enumerate(self.clients.items()):
            prefix = "-> " if addr == self.selected_client else "   "
            client_str = f"{prefix}{client.address[0]}:{client.address[1]}"
            self.screen.addstr(client_y + i, 2, client_str)
            
        # Área de mensajes
        self.screen.addstr(2, width // 3 + 2, "Mensajes:", curses.color_pair(2))
        for i, msg in enumerate(self.messages[-10:]):
            self.screen.addstr(3 + i, width // 3 + 2, msg[:width - (width // 3 + 4)])
            
        # Línea de comando
        self.screen.addstr(height - 2, 2, "Comando: " + self.current_command)
        
        # Ayuda
        help_text = "↑/↓: Seleccionar cliente | Enter: Enviar comando | Q: Salir"
        self.screen.addstr(height - 1, 2, help_text, curses.color_pair(2))
        
        self.screen.refresh()
        
    def handle_input(self):
        while True:
            try:
                key = self.screen.getch()
                if key == ord('q'):
                    break
                    
                elif key == curses.KEY_UP:
                    # Seleccionar cliente anterior
                    clients = list(self.clients.keys())
                    if clients:
                        current_idx = clients.index(self.selected_client) if self.selected_client else 0
                        self.selected_client = clients[(current_idx - 1) % len(clients)]
                        
                elif key == curses.KEY_DOWN:
                    # Seleccionar siguiente cliente
                    clients = list(self.clients.keys())
                    if clients:
                        current_idx = clients.index(self.selected_client) if self.selected_client else 0
                        self.selected_client = clients[(current_idx + 1) % len(clients)]
                        
                elif key == ord('\n'):
                    # Enviar comando
                    if self.selected_client and self.current_command:
                        client = self.clients[self.selected_client]
                        response = client.send_command(self.current_command)
                        self.messages.append(f"[{client.address[0]}] $ {self.current_command}")
                        self.messages.append(f"Respuesta: {response}")
                        self.current_command = ""
                        
                elif key == curses.KEY_BACKSPACE or key == 127:
                    # Borrar último carácter
                    self.current_command = self.current_command[:-1]
                    
                elif 32 <= key <= 126:  # Caracteres imprimibles
                    self.current_command += chr(key)
                    
                self.draw_screen()
                
            except Exception as e:
                self.cleanup_curses()
                print(f"Error en la interfaz: {e}")
                break
                
    def accept_clients(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 9999))
        server.listen(5)
        
        while True:
            try:
                client_socket, address = server.accept()
                client = Client(client_socket, address)
                self.clients[address] = client
                if not self.selected_client:
                    self.selected_client = address
                self.messages.append(f"Nuevo cliente conectado: {address[0]}:{address[1]}")
                self.draw_screen()
            except:
                break
                
    def run(self):
        try:
            self.setup_curses()
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            self.handle_input()
            
        finally:
            self.cleanup_curses()

if __name__ == "__main__":
    server = ServerUI()
    server.run()
