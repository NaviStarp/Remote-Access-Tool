import socket
import subprocess
from . import functions as f
import curses

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.commands = {
            "hostname": f.get_hostname,
            "ip": f.get_ip,
            "os": f.get_os,
            "users": f.get_users,
            "processes": f.get_processes,
            "drives": f.get_drives,
            "files": f.get_files,
            "network": f.get_network,
            "services": f.get_services
        }
        self.client_socket = None

    def connect(self,ip,port):
        """Conecta al servidor."""
        try:
            self.client_socket = socket.create_connection((ip, port))
            print("[+] Conectado al servidor.")
            return True
        except Exception as e:
            print(f"[!] Error al conectar al servidor: {e}")
            return False

    def display_commands(self, stdscr):
        """Muestra la lista de comandos en la interfaz curses y permite la selección."""
        current_row = 0
        command_list = list(self.commands.keys())

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            stdscr.addstr(0, width // 2 - len("Seleccione un comando") // 2, "Seleccione un comando", curses.A_BOLD)

            for idx, command in enumerate(command_list):
                if idx == current_row:
                    stdscr.attron(curses.A_REVERSE)  # Resaltar
                    stdscr.addstr(idx + 2, 1, command)
                    stdscr.attroff(curses.A_REVERSE)  # Apagar el resaltado
                else:
                    stdscr.addstr(idx + 2, 1, command)

            stdscr.addstr(height - 1, 0, "Use Up/Down to navigate, Enter to execute, 'q' to quit.")
            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(command_list) - 1:
                current_row += 1
            elif key in (curses.KEY_ENTER, 10, 13):
                selected_command = command_list[current_row]
                output = self.execute_command(selected_command)
                self.show_output(stdscr, output)  # Mostrar el resultado
            elif key == ord('q'):
                break

    def execute_command(self, command):
        """Ejecuta un comando en el sistema y devuelve la salida."""
        try:
            result = self.commands[command]()  # Llama a la función correspondiente
            return result
        except Exception as e:
            return f"Error ejecutando el comando: {e}"

    def show_output(self, stdscr, output):
        """Muestra la salida del comando en la interfaz curses."""
        stdscr.clear()
        stdscr.addstr(0, 0, "Resultado del comando:", curses.A_BOLD)
        stdscr.addstr(1, 0, output)  # Muestra la salida
        stdscr.addstr(len(output.splitlines()) + 2, 0, "Presione cualquier tecla para continuar.")
        stdscr.refresh()
        stdscr.getch()  # Espera a que el usuario presione una tecla

    def close(self):
        """Cierra la conexión del cliente."""
        if self.client_socket:
            self.client_socket.close()
            print("[-] Conexión cerrada.")
