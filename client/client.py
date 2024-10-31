import socket
import subprocess
from . import functions as f
import curses
import time
from math import ceil


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # Definimos qué comandos necesitan argumentos y cuáles son
        self.command_args = {
            "kill": ["pid", "Ingrese el PID del proceso a terminar: "],
            "files": ["path", "Ingrese la ruta a listar (Enter para actual): "],
            "shell": ["command", "Ingrese el comando a ejecutar: "]
        }
        self.commands = {
            "hostname": f.get_hostname,
            "ip": f.get_ip,
            "os": f.get_os,
            "users": f.get_users,
            "processes": f.get_processes,
            "drives": f.get_drives,
            "files": f.get_files,
            "network": f.get_network,
            "services": f.get_services,
            "kill": f.kill_process,
            "shell": f.execute_shell,
            "system_info": f.get_system_info,
            "environment": f.get_environment,
            "installed_software": f.get_installed_software,
            "network_connections": f.get_network_connections,
            "Close connection": self.close
        }

        self.client_socket = None
        self.status_message = ""
        self.colors = {}

    def get_command_args(self, stdscr, command):
        """Solicita los argumentos necesarios para un comando."""
        if command not in self.command_args:
            return []

        height, width = stdscr.getmaxyx()
        args = []

        # Guardar el estado actual de la pantalla
        stdscr.clear()
        self.draw_box(stdscr, 0, 0, height - 1, width - 1)

        # Título
        title = f"Ingrese argumentos para {command}"
        title_pos = max(1, (width - len(title)) // 2)
        stdscr.attron(curses.color_pair(self.colors['header']) | curses.A_BOLD)
        stdscr.addstr(1, title_pos, title)
        stdscr.attroff(curses.color_pair(self.colors['header']) | curses.A_BOLD)

        # Solicitar cada argumento
        curses.echo()  # Activar eco para ver lo que se escribe
        curses.curs_set(1)  # Mostrar el cursor

        prompt = self.command_args[command][1]
        stdscr.addstr(3, 2, prompt)
        stdscr.refresh()

        # Crear una ventana para la entrada
        input_win = curses.newwin(1, width - len(prompt) - 4, 3, len(prompt) + 2)
        input_win.refresh()

        # Obtener entrada
        arg = input_win.getstr().decode('utf-8')
        args.append(arg)

        curses.noecho()  # Desactivar eco
        curses.curs_set(0)  # Ocultar el cursor
        return args

    def execute_command(self, stdscr,command):
        """Ejecuta un comando en el sistema y devuelve la salida."""
        try:
            if command in self.command_args:
                args = self.get_command_args(stdscr, command)
                result = self.commands[command](*args)
            else:
                result = self.commands[command]()

            self.status_message = f"[+] Comando '{command}' ejecutado exitosamente"
            return result
        except Exception as e:
            self.status_message = f"[!] Error ejecutando el comando: {e}"
            return f"Error: {e}"

    def init_colors(self):
        """Inicializa los pares de colores para la interfaz."""
        curses.start_color()
        curses.use_default_colors()
        self.colors['header'] = 1
        self.colors['selected'] = 2
        self.colors['status_ok'] = 3
        self.colors['status_error'] = 4
        self.colors['help'] = 5

        curses.init_pair(1, curses.COLOR_BLUE, -1)  # Título
        curses.init_pair(2, curses.COLOR_BLUE, -1)  # Selección
        curses.init_pair(3, curses.COLOR_GREEN, -1)  # Bordes (estado activo)
        curses.init_pair(4, curses.COLOR_RED, -1)  # Estado inactivo
        curses.init_pair(5, curses.COLOR_YELLOW, -1)  # Estado de ayuda o aviso

    def connect(self, ip, port):
        """Conecta al servidor."""
        try:
            self.client_socket = socket.create_connection((ip, port))
            self.status_message = "[+] Conectado al servidor."
            return True
        except Exception as e:
            self.status_message = f"[!] Error al conectar al servidor: {e}"
            return False

    def draw_box(self, win, y, x, height, width):
        """Dibuja un marco alrededor de una región, evitando la última posición."""
        max_y, max_x = win.getmaxyx()

        # Ajustar dimensiones para evitar escribir en los bordes
        if y + height >= max_y:
            height = max_y - y - 1
        if x + width >= max_x:
            width = max_x - x - 1

        # Dibujar las esquinas
        win.addch(y, x, curses.ACS_ULCORNER)
        win.addch(y, x + width - 1, curses.ACS_URCORNER)
        win.addch(y + height - 1, x, curses.ACS_LLCORNER)

        # Dibujar las líneas horizontales
        win.hline(y, x + 1, curses.ACS_HLINE, width - 2)
        win.hline(y + height - 1, x + 1, curses.ACS_HLINE, width - 2)

        # Dibujar las líneas verticales
        win.vline(y + 1, x, curses.ACS_VLINE, height - 2)
        win.vline(y + 1, x + width - 1, curses.ACS_VLINE, height - 2)

        # Dibujar la esquina inferior derecha solo si no está en el límite
        if y + height < max_y and x + width < max_x:
            win.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)

    def display_commands(self, stdscr):
        """Muestra la lista de comandos en la interfaz curses y permite la selección."""
        self.init_colors()
        curses.curs_set(0)  # Oculta el cursor
        current_row = 0
        command_list = list(self.commands.keys())

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # Ajustar dimensiones para dejar espacio para los bordes
            safe_height = height - 1
            safe_width = width - 1

            # Dibuja el marco principal
            self.draw_box(stdscr, 0, 0, safe_height, safe_width)

            # Título
            title = "Panel de Control - Seleccione un comando"
            title_pos = max(1, (safe_width - len(title)) // 2)
            stdscr.attron(curses.color_pair(self.colors['header']) | curses.A_BOLD)
            stdscr.addstr(1, title_pos, title[:safe_width - 2])
            stdscr.attroff(curses.color_pair(self.colors['header']) | curses.A_BOLD)

            # Marco para la lista de comandos
            commands_height = min(len(command_list) + 4, safe_height - 6)
            commands_width = min(30, safe_width - 4)
            commands_y = 3
            commands_x = max(1, (safe_width - commands_width) // 2)
            self.draw_box(stdscr, commands_y, commands_x, commands_height, commands_width)

            # Lista de comandos
            visible_commands = len(command_list)
            if commands_height - 4 < visible_commands:
                visible_commands = commands_height - 4

            for idx in range(visible_commands):
                y = commands_y + idx + 2
                x = commands_x + 2
                if y < safe_height - 1:
                    command = command_list[idx]
                    if idx == current_row:
                        stdscr.attron(curses.color_pair(self.colors['selected']))
                        stdscr.addstr(y, x, f" {command} ".ljust(commands_width - 4)[:commands_width - 4])
                        stdscr.attroff(curses.color_pair(self.colors['selected']))
                    else:
                        stdscr.addstr(y, x, command[:commands_width - 4])

            # Barra de estado
            if self.status_message and safe_height > 4:
                status_y = safe_height - 2
                color = self.colors['status_ok'] if "[+]" in self.status_message else self.colors['status_error']
                stdscr.attron(curses.color_pair(color))
                stdscr.addstr(status_y, 2, self.status_message[:safe_width - 4])
                stdscr.attroff(curses.color_pair(color))

            # Ayuda
            if safe_height > 5:
                help_text = "↑/↓: Navegar | Enter: Ejecutar | Q: Salir"
                help_pos = max(1, (safe_width - len(help_text)) // 2)
                stdscr.attron(curses.color_pair(self.colors['help']))
                stdscr.addstr(safe_height - 3, help_pos, help_text[:safe_width - 2])
                stdscr.attroff(curses.color_pair(self.colors['help']))

            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(command_list) - 1:
                current_row += 1
            elif key in (curses.KEY_ENTER, 10, 13):
                selected_command = command_list[current_row]
                output = self.execute_command(stdscr, selected_command)
                self.show_output(stdscr, output)
            elif key == ord('q'):
                break

    def show_output(self, stdscr, output):
        """Muestra la salida del comando en la interfaz curses con paginación."""
        height, width = stdscr.getmaxyx()
        safe_height = height - 1
        safe_width = width - 1
        lines = output.splitlines()
        pages = ceil(len(lines) / (safe_height - 7))
        current_page = 0

        while True:
            stdscr.clear()
            self.draw_box(stdscr, 0, 0, safe_height, safe_width)

            # Título
            title = "Resultado del Comando"
            title_pos = max(1, (safe_width - len(title)) // 2)
            stdscr.attron(curses.color_pair(self.colors['header']) | curses.A_BOLD)
            stdscr.addstr(1, title_pos, title[:safe_width - 2])
            stdscr.attroff(curses.color_pair(self.colors['header']) | curses.A_BOLD)

            # Contenido
            max_lines = safe_height - 7
            start_line = current_page * max_lines
            end_line = min(start_line + max_lines, len(lines))

            for i, line in enumerate(lines[start_line:end_line]):
                if i + 3 < safe_height - 1:
                    stdscr.addstr(i + 3, 2, line[:safe_width - 4])

            # Información de página
            if pages > 1 and safe_height > 4:
                page_info = f"Página {current_page + 1}/{pages}"
                page_pos = max(1, (safe_width - len(page_info)) // 2)
                stdscr.attron(curses.color_pair(self.colors['help']))
                stdscr.addstr(safe_height - 3, page_pos, page_info[:safe_width - 2])
                stdscr.attroff(curses.color_pair(self.colors['help']))

            # Ayuda
            if safe_height > 3:
                help_text = "←/→: Cambiar página | Esc: Volver"
                help_pos = max(1, (safe_width - len(help_text)) // 2)
                stdscr.attron(curses.color_pair(self.colors['help']))
                stdscr.addstr(safe_height - 2, help_pos, help_text[:safe_width - 2])
                stdscr.attroff(curses.color_pair(self.colors['help']))

            stdscr.refresh()

            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_LEFT and current_page > 0:
                current_page -= 1
            elif key == curses.KEY_RIGHT and current_page < pages - 1:
                current_page += 1


    def close(self):
        """Cierra la conexión del cliente."""
        if self.client_socket:
            self.client_socket.close()
            self.status_message = "[-] Conexión cerrada."