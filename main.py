import curses
import argparse
from socket import socket
import threading

from client.client import Client  # Asegúrate de importar correctamente la clase Client
from server import Server

def run_server(server):
    server.start()  # Iniciar el servidor en segundo plano
    print("[+] Servidor escuchando...")

def create_executable(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Creando ejecutable...")  # Mensaje de creación de ejecutable
    stdscr.refresh()
    curses.napms(1000)
    stdscr.addstr(1, 0, "Ejecutable creado con éxito. (mentira)")
    stdscr.refresh()
    stdscr.getch()

def view_connections(stdscr,server):
    current_row = 0  # Índice de la fila actualmente resaltada
    current_col = 0  # Índice de la columna actualmente resaltada
    items_per_col = 10  # Número de elementos para mostrar por columna
    num_columns = 1  # Número de columnas para mostrar



    page_size = items_per_col * num_columns  # Total de elementos por página
    current_page = 0  # Índice de la página actual

    while True:
        connected_clients = server.connected_clients # Obtener la lista de conexiones activas
        total_connections = len(connected_clients)
        stdscr.clear()
        stdscr.addstr(0, stdscr.getmaxyx()[1] // 2 - len("Conexiones activas:") // 2, "Conexiones activas:",
                      curses.A_BOLD)

        start_index = current_page * page_size
        min(start_index + page_size, total_connections)
        if len(connected_clients) == 0:
            stdscr.addstr(stdscr.getmaxyx()[0] // 2, stdscr.getmaxyx()[1] // 2 - len("No hay conexiones activas") // 2,
                          "No hay conexiones activas")
            stdscr.refresh()
            stdscr.getch()  # Esperar a que el usuario presione una tecla
            break
        for row in range(items_per_col):
            for col in range(num_columns):
                actual_index = start_index + row + (col * items_per_col)
                if actual_index < total_connections:
                    x = (stdscr.getmaxyx()[1] // 2 - (num_columns * 20) + col * 40) + 13
                    y = (stdscr.getmaxyx()[0] // 2 - (items_per_col // 2) + row)

                    display_text = f"{actual_index + 1}. {connected_clients[actual_index]}"

                    # Resaltar el elemento seleccionado
                    if row == current_row and col == current_col:

                        stdscr.attron(curses.color_pair(1))

                        stdscr.addstr(y, x, display_text)
                        stdscr.attroff(curses.color_pair(1))  # Apagar el resaltado
                    else:
                        stdscr.addstr(y, x, display_text )

        # Mostrar información de paginación
        total_pages = (total_connections + page_size - 1) // page_size  # Calcular total de páginas
        stdscr.addstr(stdscr.getmaxyx()[0] - 2, 0,
                      f"Página {current_page + 1} de {total_pages}")
        stdscr.addstr(stdscr.getmaxyx()[0] - 1, 0,
                      "Use Up/Down to navigate, Left/Right to switch columns, Enter to select, 'q' to quit.")

        stdscr.refresh()
        key = stdscr.getch()

        # Navegación
        if key == curses.KEY_DOWN:
            if current_row < items_per_col - 1:
                current_row += 1
            elif current_row == items_per_col - 1 and current_col < num_columns - 1: # Mover a la siguiente columna si se llega al final
                current_row = 0
                current_col += 1
            elif current_row == 0 and current_col == 0:
                current_row  = items_per_col - 1
            else: # Mover a la siguiente página si se llega al final
                if (start_index + page_size) < total_connections:
                    current_page += 1 # Mover a la siguiente página
                    current_row = 0  # Reiniciar a la primera fila de la nueva página
                    current_col = 0  # Reiniciar a la primera columna

        elif key == curses.KEY_UP:
            if current_row > 0:
                current_row -= 1
            elif current_row == 0 and current_col > 0:
                current_col -= 1
                current_row = items_per_col - 1  # Ir a la última fila de la nueva columna
            else:
                # Mover a la página anterior si se está en la primera fila
                if current_page > 0:
                    current_page -= 1
                    current_row = items_per_col - 1  # Ir a la última fila de la nueva página
                    current_col = 0  # Reiniciar a la primera columna
        elif key == curses.KEY_LEFT:
            if current_col > 0:
                current_col -= 1  # Mover a la columna anterior
            elif current_page > 0:
                current_page -= 1  # Mover a la página anterior
                current_col = num_columns - 1  # Ir a la última columna de la nueva página
                current_row = min(current_row,
                                  items_per_col - 1)  # Ajustar la fila actual para mantenerse dentro de los límites
        elif key == curses.KEY_RIGHT:
            if current_col < num_columns - 1:
                current_col += 1  # Mover a la siguiente columna
                current_row = min(current_row,
                                  items_per_col - 1)  # Ajustar la fila actual para mantenerse dentro de los límites
            else:  # Mover a la siguiente página si se llega al final
                if (start_index + page_size) < total_connections:
                    current_page += 1  # Mover a la siguiente página
                    current_row = 0  # Reiniciar a la primera fila de la nueva página
                    current_col = 0  # Reiniciar a la primera columna


        elif key == curses.KEY_ENTER or key in [10, 13]:
            # Conectarse al cliente seleccionado
            selected_client_index = start_index + current_row + (current_col * items_per_col)
            if selected_client_index < total_connections:
                selected_client: Client = connected_clients[selected_client_index]
                stdscr.addstr(stdscr.getmaxyx()[0] - 1, 0, "Conectando al cliente...")  # Mensaje de depuración
                stdscr.refresh()
                if isinstance(selected_client, Client):  # Verifica si es una instancia de Client
                    if not selected_client.connect("127.0.0.1","8080"):  # Asegúrate de que connect() se ejecute correctamente
                        stdscr.addstr(stdscr.getmaxyx()[0] - 1, 0, "Error al conectar al cliente.")
                        stdscr.refresh()
                        stdscr.getch()
                        continue  # Vuelve al menú de conexiones

                    selected_client.display_commands(stdscr)  # Pasar el cliente seleccionado al menú del cliente
        elif key == ord("q"):
            break

        # Limitar current_row y current_col a los máximos disponibles
        current_row = min(current_row, items_per_col - 1)
        current_col = min(current_col, num_columns - 1)

        # Asegurarse de que no se intente acceder a un índice fuera de rango
        if start_index + current_row + (current_col * items_per_col) >= total_connections:
            current_row = 0
            current_col = 0


def menu_init(stdscr, logo, menu, current_row):
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Verifica si hay suficiente espacio para el logo
    if height < len(logo) + 5:  # Asegúrate de que haya suficiente espacio para el logo y el menú
        stdscr.addstr(0, 0, "La ventana es demasiado pequeña para mostrar el logo.")
        stdscr.refresh()
        stdscr.getch()  # Esperar a que el usuario presione una tecla
        return

    # Mostrar el logo centrado en la parte superior
    for i, line in enumerate(logo):
        x = width // 2 - len(line) // 2
        stdscr.addstr(i + 5, x, line, curses.A_BOLD)

    # Mostrar el menú centrado en la pantalla
    for idx, row in enumerate(menu):
        x = width // 2 - len(row) // 2
        y = height // 2 - len(menu) // 2 + idx
        if idx == current_row:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, row)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, row)


def client_menu(stdscr, client: Client):
    if not client.connect("127.0.0.1","8080"):
        return

    name = client.commands["hostname"]()  # Obtiene el nombre del cliente
    logo = [f"Menu cliente: {name}".capitalize(), "-------------------------------------"]
    menu = list(client.commands.keys())  # Lista de comandos
    current_row = 0

    while True:
        menu_init(stdscr, logo, menu, current_row)

        key = stdscr.getch()

        # Navegación del menú
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            # Ejecuta la opción seleccionada
            selected_command = menu[current_row]
            command = f"{selected_command}"  # Llama al comando directamente

            # Manda el comando al servidor
            client.client_socket.send(command.encode('utf-8'))

            # Espera la respuesta del servidor
            response = client.client_socket.recv(4096).decode('utf-8')

            # Muestra la respuesta en la pantalla
            stdscr.clear()  # Limpia la pantalla
            stdscr.addstr(0, 0, f"Comando ejecutado: {selected_command}")
            stdscr.addstr(1, 0, f"Respuesta del cliente: {response}")
            stdscr.addstr(2, 0, "Presione cualquier tecla para volver al menú...")
            stdscr.refresh()  # Refresca la pantalla

            stdscr.getch()  # Espera a que el usuario presione una tecla

            # Restablece el menú después de mostrar la respuesta
            current_row = 0  # Restablece la fila resaltada
        stdscr.refresh()


def main_menu(stdscr, server):
    # Configuración del logo y opciones de menú
    logo = [
        " T I T U L O ",
        "-------------------------------------"
    ]
    menu = ["CREAR EJECUTABLE", "VER CONEXIONES", "SALIR"]
    current_row = 0

    # Bucle principal del menú
    while True:
        menu_init(stdscr, logo, menu, current_row)

        key = stdscr.getch()

        # Navegación del menú
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            # Ejecuta la opción seleccionada
            if menu[current_row] == "CREAR EJECUTABLE":
                create_executable(stdscr)
            elif menu[current_row] == "VER CONEXIONES":
                view_connections(stdscr, server)
            elif menu[current_row] == "SALIR":
                break
        elif key == ord("q"):
            exit(0)
        stdscr.refresh()

def main(stdscr):
    parser = argparse.ArgumentParser(description="Servidor Simulado")
    parser.add_argument('--create', action='store_true', help='Crear un ejecutable al inicio')
    parser.add_argument('--view', action='store_true', help='Ver las conexiones al inicio')
    args = parser.parse_args()

    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)

    stdscr.addstr(0, 0, "Iniciando el servidor en segundo plano...")
    stdscr.refresh()

    server = Server()  # Crear una instancia del servidor
    server_thread = threading.Thread(target=run_server, args=(server,))

    server_thread.daemon = True
    server_thread.start()
    server_thread.join(1)  # Esperar 1 segundo para que el servidor se inicie

    if args.create:
        create_executable(stdscr)
    elif args.view:
        view_connections(stdscr, server)
    else:
        # Muestra el menú principal
        main_menu(stdscr, server)

if __name__ == "__main__":
    curses.wrapper(main)
