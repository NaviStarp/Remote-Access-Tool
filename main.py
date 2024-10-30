import curses
import argparse
import threading
from typing import Union
from client import Client
from server import Server


# Manejo de las funciones del servidor
def run_server(server):
    server.start()
    print("[+] Servidor escuchando...")


def create_executable(stdscr):
    stdscr.clear()
    show_message(stdscr, "Creando ejecutable...", 0)
    curses.napms(1000)
    show_message(stdscr, "Ejecutable creado con éxito. (mentira)", 1)
    stdscr.getch()


# Funciones auxiliares de navegación y display
def show_message(stdscr, message, y, x):
    stdscr.addstr(y, x, message)
    stdscr.refresh()


def show_connections(stdscr, server):
    connected_clients = [Client(f"Cliente {i}", f"127.0.0.{i}") for i in range(100)]
    total_connections = len(connected_clients)
    current_row = 0
    page_size = 10
    current_page = 0

    total_pages = (total_connections + page_size - 1) // page_size  # Cálculo de total de páginas

    while True:
        stdscr.clear()
        show_message(stdscr, "Conexiones activas:", 0, stdscr.getmaxyx()[1] // 2 - len("Conexiones activas:") // 2)

        start_index = current_page * page_size

        # Mostrar clientes en la página actual
        for idx in range(page_size):
            actual_index = start_index + idx
            if actual_index < total_connections:
                name = connected_clients[actual_index].execute_command('hostname')
                display_text = f"{actual_index + 1}. {name}"
                y, x = get_display_position(stdscr, idx)
                show_client_row(stdscr, y, stdscr.getmaxyx()[1] // 2 - len("Conexiones activas:") // 2, display_text, current_row == idx)

        # Mostrar información de paginación
        pagination_info = f"Página {current_page + 1} de {total_pages}"
        show_message(stdscr, pagination_info, stdscr.getmaxyx()[0] - 2,0 )

        stdscr.refresh()

        # Navegación en la lista de clientes
        result = navigate_client_list(stdscr, connected_clients, page_size, current_row, current_page, total_pages)

        if result == "quit":
            break  # Salir del bucle para volver al menú principal
        elif isinstance(result, tuple):
            current_row, current_page = result
        else:
            selected_client: Client = result  # Cliente seleccionado por el usuario

            if selected_client and isinstance(selected_client, Client):
                stdscr.clear()
                show_message(stdscr, f"Cliente seleccionado: {selected_client}", 0, 0)
                selected_client.display_commands(stdscr)
                stdscr.refresh()
                stdscr.getch()


def get_display_position(stdscr, row):
    y = (stdscr.getmaxyx()[0] // 2 - 5 + row)
    x = stdscr.getmaxyx()[1] // 2 - 20
    return y, x


def show_client_row(stdscr, y, x, display_text, highlighted):
    if highlighted:
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(y, x, display_text)
        stdscr.attroff(curses.color_pair(1))
    else:
        stdscr.addstr(y, x, display_text)


def navigate_client_list(stdscr, connected_clients, page_size, current_row, current_page, total_pages) -> Union[
    tuple, str, Client]:
    total_connections = len(connected_clients)
    key = stdscr.getch()

    if key == curses.KEY_DOWN:
        if current_row < page_size - 1 and (current_page * page_size + current_row + 1) < total_connections:
            current_row += 1
        elif (current_page + 1) * page_size < total_connections:
            current_page += 1
            current_row = 0  # Resetea la fila al inicio de la nueva página

    elif key == curses.KEY_UP:
        if current_row > 0:
            current_row -= 1
        elif current_page > 0:
            current_page -= 1
            current_row = page_size - 1  # Resetea a la última fila de la página anterior

    elif key == curses.KEY_RIGHT:  # Navegación a la derecha
        if current_page < total_pages - 1:
            current_page += 1
            current_row = 0  # Resetea la fila al inicio de la nueva página

    elif key == curses.KEY_LEFT:  # Navegación a la izquierda
        if current_page > 0:
            current_page -= 1
            current_row = 0  # Resetea la fila al inicio de la nueva página

    elif key in [10, 13]:  # Enter key
        selected_client = select_client(connected_clients, current_row, current_page, page_size)
        if selected_client:
            return selected_client

    elif key == ord("q"):
        return "quit"

    return current_row, current_page


def select_client(connected_clients, current_row, current_page, page_size) -> Client:
    selected_index = current_page * page_size + current_row
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
