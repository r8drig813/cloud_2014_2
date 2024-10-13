import subprocess

def mostrar_menu():
    print("\nBienvenido")
    print("\nMenú:")
    print("1. Listar Slices")
    print("2. Crear Slices")
    print("3. Editar Slices")
    print("4. Borrar Slices")
    print("5. Salir")

def main():
    while True:
        mostrar_menu()
        opcion = input("\nSelecciona una opción: ")
        
        if opcion == "1":
            print("Has seleccionado: Listar Slices")
        elif opcion == "2":
            print("Has seleccionado: Crear Slices")
            subprocess.run(["python", "Crear_Slices.py"])
        elif opcion == "3":
            print("Has seleccionado: Editar Slices")
        elif opcion == "4":
            print("Has seleccionado: Borrar Slices")
        elif opcion == "5":
            print("Gracias por usar el programa. ¡Hasta luego!")
            break
        else:
            print("Opción no válida. Por favor, intenta de nuevo.")

if __name__ == "__main__":
    main()