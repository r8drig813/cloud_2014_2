import requests
import getpass
import subprocess

# Solicitar credenciales al usuario
username = input("Por favor, introduce tu nombre de usuario: ")
password = getpass.getpass("Por favor, introduce tu contraseña: ")

# URL del servidor FastAPI
url = "http://10.20.12.106:5810/login"

# Datos de login
data = {
    "username": username,
    "password": password
}

# Realizar la solicitud POST al servidor FastAPI
try:
    response = requests.post(url, json=data)
    
    # Comprobar la respuesta del servidor
    if response.status_code == 200:
        print("¡Login exitoso!")
        print("Respuesta del servidor:", response.json())
        subprocess.run(["python3", "menu.py"])
    else:
        print("Error de login:", response.status_code)
        print("Detalles:", response.text)

except requests.ConnectionError:
    print("Error: No se pudo conectar al servidor.")