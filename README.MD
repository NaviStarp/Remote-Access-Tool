# Remote Access Tool

**Remote Access Tool** es una aplicación en Python para gestionar conexiones remotas desde la consola. Permite monitorear y conectarse a clientes activos, mostrando una lista de conexiones en una interfaz interactiva.

## Características
- **Creación de ejecutables**: Convierte el script en un ejecutable para Windows, Linux y macOS.
- **Visualización de Conexiones Activas**: Muestra las conexiones remotas organizadas en columnas y filas.
- **Navegación de Páginas**: Cambia automáticamente entre páginas cuando hay más conexiones de las que caben en pantalla.
- **Conexión Rápida**: Conéctate directamente a clientes seleccionados desde la interfaz.
- **Ejecución de Comandos**: Envía comandos a los clientes conectados y recibe la respuesta en tiempo real.

## Requisitos

- Python 3.7 o superior
- Librería `curses` (preinstalada en Python en Linux y macOS; en Windows se requiere `windows-curses`).
- Librerias 'winreg', 'pyinstaller', 'psutil', 'browser_history'
## Instalación y Uso

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/NaviStarp/remote-access-tool.git
   cd remote-access-tool
    ```
2. instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. **Ejecuta la aplicación**:
   ```bash
    python main.py
    ```

