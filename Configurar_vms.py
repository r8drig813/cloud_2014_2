import sys

def configurar_vms(topologia):
    print(f"\nConfiguración de VMs para topología {topologia}")
    
    # Solicitar número de VMs
    while True:
        try:
            num_vms = int(input("Ingrese número de máquinas virtuales (VM): "))
            if num_vms > 0:
                break
            else:
                print("Por favor, ingrese un número positivo.")
        except ValueError:
            print("Por favor, ingrese un número válido.")

    # Configurar cada VM
    vms = []
    for i in range(1, num_vms + 1):
        print(f"\nConfiguración para VM{i}:")
        while True:
            try:
                ram = int(input(f"Cantidad de RAM (GB) para la VM{i}: "))
                if ram > 0:
                    break
                else:
                    print("Por favor, ingrese un número positivo.")
            except ValueError:
                print("Por favor, ingrese un número válido.")

        while True:
            try:
                storage = int(input(f"Cantidad de almacenamiento (GB) para la VM{i}: "))
                if storage > 0:
                    break
                else:
                    print("Por favor, ingrese un número positivo.")
            except ValueError:
                print("Por favor, ingrese un número válido.")

        # Preguntar sobre la conexión a internet
        while True:
            internet = input(f"¿Desea que la VM{i} tenga conexión a internet? (s/n): ").lower()
            if internet in ['s', 'n']:
                internet = True if internet == 's' else False
                break
            else:
                print("Por favor, responda 's' para sí o 'n' para no.")

        # Seleccionar worker para despliegue
        print("\nDonde quieres que se despliegue la VM:")
        print("1. Worker 1")
        print("2. Worker 2")
        print("3. Worker 3")
        
        while True:
            worker = input("Selecciona un worker (1-3): ")
            if worker in ["1", "2", "3"]:
                worker = f"Worker {worker}"
                break
            else:
                print("Opción no válida. Por favor, selecciona 1, 2 o 3.")

        vms.append({
            "nombre": f"VM{i}",
            "ram": ram,
            "almacenamiento": storage,
            "internet": internet,
            "worker": worker
        })

    # Mostrar resumen de la configuración
    print("\nResumen de la configuración:")
    print(f"Topología: {topologia}")
    for vm in vms:
        print(f"\n{vm['nombre']}:")
        print(f"  RAM: {vm['ram']} GB")
        print(f"  Almacenamiento: {vm['almacenamiento']} GB")
        print(f"  Conexión a internet: {'Sí' if vm['internet'] else 'No'}")
        print(f"  Desplegada en: {vm['worker']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        configurar_vms(sys.argv[1])
    else:
        print("Error: No se especificó la topología.")