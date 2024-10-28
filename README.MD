# Remote Access Tool

**Remote Access Tool** es una aplicación en Python para gestionar conexiones remotas desde la consola. Permite monitorear y conectarse a clientes activos, mostrando una lista de conexiones en una interfaz interactiva.

## Características

- **Visualización de Conexiones Activas**: Muestra las conexiones remotas organizadas en columnas y filas.
- **Navegación de Páginas**: Cambia automáticamente entre páginas cuando hay más conexiones de las que caben en pantalla.
- **Conexión Rápida**: Conéctate directamente a clientes seleccionados desde la interfaz.

## Requisitos

- Python 3.7 o superior
- Librería `curses` (preinstalada en Python en Linux y macOS; en Windows se requiere `windows-curses`).

## Instalación y Uso

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/tuusuario/remote-access-tool.git
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
## Controles 
Flechas Arriba/Abajo: Moverse entre las conexiones
Enter: Conectar a un cliente
Q: Salir de la aplicación

# Licecia 
Este proyecto está bajo la licencia MIT. Para más información, revisa el archivo LICENSE.
