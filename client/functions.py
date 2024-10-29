import socket
import subprocess

def get_hostname():
    """Obtiene el nombre de host de la máquina cliente."""
    try:
        return socket.gethostname().split('.')[0]
    except Exception as e:
        return f"Error: {e}"

def get_ip():
    """Obtiene la dirección IP de la máquina cliente."""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        return f"Error: {e}"

def get_os():
    """Obtiene el sistema operativo de la máquina cliente."""
    try:
        return subprocess.check_output("ver", shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

def get_users():
    """Obtiene los usuarios activos en la máquina cliente."""
    try:
        return subprocess.check_output("net user", shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

def get_processes():
    """Obtiene los procesos en ejecución en la máquina cliente."""
    try:
        return subprocess.check_output("tasklist", shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

def get_drives():
    """Obtiene los discos duros de la máquina cliente."""
    try:
        return subprocess.check_output("fsutil fsinfo drives", shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

def get_files():
    """Obtiene los archivos en la carpeta actual de la máquina cliente."""
    try:
        return subprocess.check_output("dir", shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

def get_network():
    """Obtiene la configuración de red de la máquina cliente."""
    try:
        return subprocess.check_output("ipconfig /all", shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

def get_services():
    """Obtiene los servicios de la máquina cliente."""
    try:
        return subprocess.check_output("net start", shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"Error: {e}"
