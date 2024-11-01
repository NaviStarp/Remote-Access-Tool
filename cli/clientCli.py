import curses
from math import ceil

from client.functions import execute_command  # Asegúrate de que esta función esté definida correctamente

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

    # Definir los pares de colores
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Título
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Selección
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Estado activo
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)  # Estado inactivo
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Estado de ayuda o aviso


def draw_box(win, y, x, height, width):
    """Dibuja un marco alrededor de una región, evitando la última posición."""
    max_y, max_x = win.getmaxyx()
    height = min(height, max_y - y - 1)  # Ajustar dimensiones
    width = min(width, max_x - x - 1)

    # Dibujar las esquinas y líneas
    win.addch(y, x, curses.ACS_ULCORNER)
    win.addch(y, x + width - 1, curses.ACS_URCORNER)
    win.addch(y + height - 1, x, curses.ACS_LLCORNER)
    win.hline(y, x + 1, curses.ACS_HLINE, width - 2)
    win.hline(y + height - 1, x + 1, curses.ACS_HLINE, width - 2)
    win.vline(y + 1, x, curses.ACS_VLINE, height - 2)
    win.vline(y + 1, x + width - 1, curses.ACS_VLINE, height - 2)
    win.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)


def get_command_args(stdscr, command, command_args):
    """Solicita los argumentos necesarios para un comando."""
    if command not in command_args:
        return []

    height, width = stdscr.getmaxyx()
    args = []

    stdscr.clear()
    draw_box(stdscr, 0, 0, height - 1, width - 1)

    title = f"Ingrese argumentos para {command}"
    title_pos = max(1, (width - len(title)) // 2)
    stdscr.attron(curses.color_pair(colors['header']) | curses.A_BOLD)
    stdscr.addstr(1, title_pos, title)
    stdscr.attroff(curses.color_pair(colors['header']) | curses.A_BOLD)

    # Solicitar cada argumento
    curses.echo()
    curses.curs_set(1)

    prompt = command_args[command][1]
    stdscr.addstr(3, 2, prompt)
    stdscr.refresh()

    input_win = curses.newwin(1, width - len(prompt) - 4, 3, len(prompt) + 2)
    input_win.refresh()

    # Obtener entrada
    arg = input_win.getstr().decode('utf-8')
    args.append(arg)

    curses.noecho()
    curses.curs_set(0)
    return args


def display_commands(stdscr, client):
    init_colors()
    curses.curs_set(0)
    current_row = 0
    command_list = list(client.commands.keys())

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        safe_height = height - 1
        safe_width = width - 1

        draw_box(stdscr, 0, 0, safe_height, safe_width)

        title = "Panel de Control - Seleccione un comando"
        title_pos = max(1, (safe_width - len(title)) // 2)
        stdscr.attron(curses.color_pair(colors['header']) | curses.A_BOLD)
        stdscr.addstr(1, title_pos, title[:safe_width - 2])
        stdscr.attroff(curses.color_pair(colors['header']) | curses.A_BOLD)

        commands_height = min(len(command_list) + 4, safe_height - 6)
        commands_width = min(30, safe_width - 4)
        commands_y = 3
        commands_x = max(1, (safe_width - commands_width) // 2)
        draw_box(stdscr, commands_y, commands_x, commands_height, commands_width)

        visible_commands = min(commands_height - 4, len(command_list))

        for idx in range(visible_commands):
            y = commands_y + idx + 2
            x = commands_x + 2
            if y < safe_height - 1:
                command = command_list[idx]
                if idx == current_row:
                    stdscr.attron(curses.color_pair(colors['selected']))
                    stdscr.addstr(y, x, f" {command} ".ljust(commands_width - 4)[:commands_width - 4])
                    stdscr.attroff(curses.color_pair(colors['selected']))
                else:
                    stdscr.addstr(y, x, command[:commands_width - 4])

        if status_message and safe_height > 4:
            status_y = safe_height - 2
            color = colors['status_ok'] if "[+]" in status_message else colors['status_error']
            stdscr.attron(curses.color_pair(color))
            stdscr.addstr(status_y, 2, status_message[:safe_width - 4])
            stdscr.attroff(curses.color_pair(color))

        if safe_height > 5:
            help_text = "↑/↓: Navegar | Enter: Ejecutar | Q: Salir"
            help_pos = max(1, (safe_width - len(help_text)) // 2)
            stdscr.attron(curses.color_pair(colors['help']))
            stdscr.addstr(safe_height - 3, help_pos, help_text[:safe_width - 2])
            stdscr.attroff(curses.color_pair(colors['help']))

        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(command_list) - 1:
            current_row += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            selected_command = command_list[current_row]
            args = get_command_args(stdscr, selected_command, client.command_args)  # Obtiene argumentos
            output = execute_command(stdscr, selected_command, args)  # Pasa los argumentos a la función
            show_output(stdscr, output)
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

        if pages > 1 and safe_height > 4:
            page_info = f"Página {current_page + 1}/{pages}"
            page_pos = max(1, (safe_width - len(page_info)) // 2)
            stdscr.attron(curses.color_pair(colors['help']))
            stdscr.addstr(safe_height - 3, page_pos, page_info[:safe_width - 2])
            stdscr.attroff(curses.color_pair(colors['help']))

        if safe_height > 3:
            help_text = "←/→: Cambiar página | Esc: Volver"
            help_pos = max(1, (safe_width - len(help_text)) // 2)
            stdscr.attron(curses.color_pair(colors['help']))
            stdscr.addstr(safe_height - 2, help_pos, help_text[:safe_width - 2])
            stdscr.attroff(curses.color_pair(colors['help']))

        stdscr.refresh()

        key = stdscr.getch()
        if key == 27:  # ESC
            break
        elif key == curses.KEY_LEFT and current_page > 0:
            current_page -= 1
        elif key == curses.KEY_RIGHT and current_page < pages - 1:
            current_page += 1
