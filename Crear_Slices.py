import subprocess

def mostrar_opciones_topologia():
    print("\nOpciones de Topología:")
    print("1. Lineal")
    print("2. Anillo")
    print("3. Bus")
    print("4. Árbol")

def crear_topologia():
    while True:
        mostrar_opciones_topologia()
        opcion = input("\nSelecciona una topología: ")
        
        if opcion in ["1", "2", "3"]:
            topologias = {
                "1": "Lineal",
                "2": "Anillo",
                "3": "Parcial",
                #"4": "Arbol"  # Nota: sin tilde para coincidir con el nombre del archivo.
            }
            script_name = f"{topologias[opcion]}.py"
            print(f"Has seleccionado la topología {topologias[opcion]}")
            try:
                # Pasa la topología como argumento
                subprocess.run(["python", script_name, topologias[opcion]], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error al ejecutar el script {script_name}: {e}")
            break
        else:
            print("Opción no válida. Por favor, intenta de nuevo.")

if __name__ == "__main__":
    print("Bienvenido a la creación de topologías para Slices")
    crear_topologia()
    input("Presiona Enter para volver al menú principal...")
