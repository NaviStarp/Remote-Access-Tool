# client/__main__.py
from client.client import Client
if __name__ == "__main__":
    SERVER_HOST = '127.0.0.1'  # Cambia a la IP del servidor
    SERVER_PORT = 8080         # Puerto del servidor

    client = Client(SERVER_HOST, SERVER_PORT)
    client.connect(SERVER_HOST, SERVER_PORT)



