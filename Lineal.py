import sys
import paramiko
import networkx as nx
import matplotlib.pyplot as plt

def ejecutar_comando_ssh(ssh, comando, sudo=False):
    if sudo:
        comando = f"echo zenbook13 | sudo -S {comando}"
    stdin, stdout, stderr = ssh.exec_command(comando)
    return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')

def conectar_ssh(hostname, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        return ssh
    except Exception as e:
        print(f"Error al conectar por SSH a {hostname}: {e}")
        return None

def visualizar_topologia(vms, topologia):
    G = nx.Graph()
    
    # Añadir nodos (VMs)
    for vm in vms:
        G.add_node(vm['nombre'])
    
    # Añadir conexiones según la topología
    if topologia.lower() == "lineal":
        for i in range(len(vms) - 1):
            G.add_edge(vms[i]['nombre'], vms[i+1]['nombre'])
    
    # Dibujar el grafo
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_color='lightgreen', node_size=3000, font_size=12, font_weight='bold')
    
    # Añadir etiquetas con información adicional
    node_labels = {vm['nombre']: f"{vm['nombre']}\nRAM: {vm['ram']}GB\nStorage: {vm['almacenamiento']}GB\nInternet: {'Sí' if vm['internet'] else 'No'}\nWorker: {vm['worker']}" for vm in vms}
    nx.draw_networkx_labels(G, pos, node_labels, font_size=8)
    
    plt.title(f"Topología de Red: {topologia}")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def configurar_vms(topologia):
    print(f"\nConfiguración de VMs para topología {topologia}")
    
    # Configuración de SSH para headnode
    headnode_ssh = conectar_ssh('10.20.12.187', 5800, 'ubuntu', 'zenbook13')
    if not headnode_ssh:
        return

    # Ejecutar init_headnode.sh
    print("Ejecutando init_headnode.sh...")
    out, err = ejecutar_comando_ssh(headnode_ssh, "./init_headnode.sh br-int ens5", sudo=True)
    print(out)
    if err:
        print(f"Error: {err}")

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

    # Configurar cada VM y crear VLANs
    vms = []
    vlan_commands = []
    for i in range(1, num_vms + 1):
        print(f"\nConfiguración para VM{i}:")
        ram = int(input(f"Cantidad de RAM (GB) para la VM{i}: "))
        storage = int(input(f"Cantidad de almacenamiento (GB) para la VM{i}: "))
        internet = input(f"¿Desea que la VM{i} tenga conexión a internet? (s/n): ").lower() == 's'
        worker_num = input('Selecciona un worker (1-3): ')
        worker = f"Worker {worker_num}"

        vms.append({
            "nombre": f"VM{i}",
            "ram": ram,
            "almacenamiento": storage,
            "internet": internet,
            "worker": worker,
            "worker_num": worker_num,
            "vlan_tag": i * 100
        })

        vlan_tag = i * 100
        ip_base = f"192.168.{i}"
        vlan_commands.append(f"vlan{vlan_tag} {vlan_tag} {ip_base}.0/24 {ip_base}.50,{ip_base}.100")

    # Visualizar la topología antes de ejecutar los comandos
    visualizar_topologia(vms, topologia)

    # Preguntar al usuario si desea continuar
    continuar = input("¿Desea continuar con la configuración? (s/n): ").lower()
    if continuar != 's':
        print("Configuración cancelada.")
        return

    # Ejecutar create_multiple_vlans.sh
    vlan_command = "./create_multiple_vlans.sh " + "     ".join(vlan_commands)
    print("Ejecutando create_multiple_vlans.sh...")
    out, err = ejecutar_comando_ssh(headnode_ssh, vlan_command, sudo=True)
    print(out)
    if err:
        print(f"Error: {err}")

    # Configurar comunicación entre VLANs para topología lineal
    if topologia.lower() == "lineal":
        for i in range(1, num_vms):
            vlan1 = i * 100
            vlan2 = (i + 1) * 100
            print(f"Habilitando comunicación entre VLAN {vlan1} y VLAN {vlan2}...")
            out, err = ejecutar_comando_ssh(headnode_ssh, f"./enable_vlan_communication.sh {vlan1} {vlan2}", sudo=True)
            print(out)
            if err:
                print(f"Error: {err}")

    # Habilitar acceso a internet para VMs seleccionadas
    for vm in vms:
        if vm['internet']:
            vlan = vm['vlan_tag']
            print(f"Habilitando acceso a internet para VLAN {vlan}...")
            out, err = ejecutar_comando_ssh(headnode_ssh, f"./enable_vlan_internet_access.sh {vlan}", sudo=True)
            print(out)
            if err:
                print(f"Error: {err}")

    # Desplegar VMs en workers
    worker_ips = {'1': '10.0.0.30', '2': '10.0.0.40', '3': '10.0.0.50'}
    for vm in vms:
        worker_ip = worker_ips[vm['worker_num']]
        print(f"Conectando al {vm['worker']} ({worker_ip})...")

        # Crear VM en el worker
        create_vm_command = f"ssh {worker_ip} 'echo zenbook13 | sudo -S ./create_vm.sh {vm['nombre']} br-int {vm['vlan_tag']} {vm['vlan_tag'] // 100}'"
        print(f"Comando a ejecutar: {create_vm_command}")
        print(f"Creando {vm['nombre']} en {vm['worker']}...")
        out, err = ejecutar_comando_ssh(headnode_ssh, create_vm_command)
        print(out)
        if err:
            print(f"Error al crear VM: {err}")
        
        # Inicializar worker
        init_worker_command = f"ssh {worker_ip} 'echo zenbook13 | sudo -S ./init_worker.sh br-int ens4'"
        out, err = ejecutar_comando_ssh(headnode_ssh, init_worker_command)
        print(out)
        if err:
            print(f"Error al inicializar worker: {err}")
            continue

    headnode_ssh.close()

    # Mostrar resumen de la configuración
    print("\nResumen de la configuración:")
    print(f"Topología: {topologia}")
    for vm in vms:
        print(f"\n{vm['nombre']}:")
        print(f"  RAM: {vm['ram']} GB")
        print(f"  Almacenamiento: {vm['almacenamiento']} GB")
        print(f"  Conexión a internet: {'Sí' if vm['internet'] else 'No'}")
        print(f"  Desplegada en: {vm['worker']}")
        print(f"  VLAN tag: {vm['vlan_tag']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        configurar_vms(sys.argv[1])
    else:
        print("Error: No se especificó la topología.")