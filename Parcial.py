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

def visualizar_topologia(vms_anillo, vms_lineal, vm_conexion):
    G = nx.Graph()
    
    # Añadir nodos (VMs)
    for vm in vms_anillo + vms_lineal:
        G.add_node(vm['nombre'])
    
    # Añadir conexiones para topología de anillo
    for i in range(len(vms_anillo)):
        G.add_edge(vms_anillo[i]['nombre'], vms_anillo[(i+1) % len(vms_anillo)]['nombre'])
    
    # Añadir conexiones para topología lineal
    for i in range(len(vms_lineal) - 1):
        G.add_edge(vms_lineal[i]['nombre'], vms_lineal[i+1]['nombre'])
    
    # Añadir conexión entre topologías
    G.add_edge(vm_conexion['nombre'], vms_lineal[0]['nombre'])
    
    # Dibujar el grafo
    pos = nx.spring_layout(G)
    plt.figure(figsize=(15, 10))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=3000, font_size=12, font_weight='bold')
    
    # Añadir etiquetas con información adicional
    node_labels = {vm['nombre']: f"{vm['nombre']}\nRAM: {vm['ram']}GB\nStorage: {vm['almacenamiento']}GB\nInternet: {'Sí' if vm['internet'] else 'No'}\nWorker: {vm['worker']}" for vm in vms_anillo + vms_lineal}
    nx.draw_networkx_labels(G, pos, node_labels, font_size=8)
    
    # Resaltar la VM de conexión
    nx.draw_networkx_nodes(G, pos, nodelist=[vm_conexion['nombre']], node_color='yellow', node_size=3500)
    
    plt.title("Topología de Red Combinada: Anillo y Lineal")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def configurar_vms():
    print("\nConfiguración de VMs para topología combinada (Anillo y Lineal)")
    
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

    # Configurar VMs para topología de anillo
    num_vms_anillo = int(input("Ingrese número de VMs para la topología de anillo: "))
    vms_anillo = configurar_vms_grupo("anillo", num_vms_anillo)

    # Configurar VMs para topología lineal
    num_vms_lineal = int(input("Ingrese número de VMs para la topología lineal: "))
    vms_lineal = configurar_vms_grupo("lineal", num_vms_lineal, start_index=len(vms_anillo)+1)

    # Elegir VM de conexión entre topologías
    print("\nElija la VM del anillo que se conectará con la topología lineal:")
    for i, vm in enumerate(vms_anillo):
        print(f"{i+1}. {vm['nombre']}")
    vm_conexion_index = int(input("Ingrese el número de la VM: ")) - 1
    vm_conexion = vms_anillo[vm_conexion_index]

    # Visualizar la topología antes de ejecutar los comandos
    visualizar_topologia(vms_anillo, vms_lineal, vm_conexion)

    # Preguntar al usuario si desea continuar
    continuar = input("¿Desea continuar con la configuración? (s/n): ").lower()
    if continuar != 's':
        print("Configuración cancelada.")
        return

    # Crear VLANs y configurar comunicación
    crear_vlans(headnode_ssh, vms_anillo + vms_lineal)
    configurar_comunicacion_anillo(headnode_ssh, vms_anillo)
    configurar_comunicacion_lineal(headnode_ssh, vms_lineal)
    
    # Conectar topologías
    print(f"Conectando {vm_conexion['nombre']} con {vms_lineal[0]['nombre']}...")
    out, err = ejecutar_comando_ssh(headnode_ssh, f"./enable_vlan_communication.sh {vm_conexion['vlan_tag']} {vms_lineal[0]['vlan_tag']}", sudo=True)
    print(out)
    if err:
        print(f"Error: {err}")

    # Habilitar acceso a internet y desplegar VMs
    habilitar_internet(headnode_ssh, vms_anillo + vms_lineal)
    desplegar_vms(headnode_ssh, vms_anillo + vms_lineal)

    headnode_ssh.close()

    # Mostrar resumen de la configuración
    mostrar_resumen(vms_anillo + vms_lineal, vm_conexion)

def configurar_vms_grupo(tipo, num_vms, start_index=1):
    vms = []
    for i in range(start_index, start_index + num_vms):
        print(f"\nConfiguración para VM{i} ({tipo}):")
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
    return vms

def crear_vlans(ssh, vms):
    vlan_commands = [f"vlan{vm['vlan_tag']} {vm['vlan_tag']} 192.168.{vm['vlan_tag']//100}.0/24 192.168.{vm['vlan_tag']//100}.50,192.168.{vm['vlan_tag']//100}.100" for vm in vms]
    vlan_command = "./create_multiple_vlans.sh " + "     ".join(vlan_commands)
    print("Ejecutando create_multiple_vlans.sh...")
    out, err = ejecutar_comando_ssh(ssh, vlan_command, sudo=True)
    print(out)
    if err:
        print(f"Error: {err}")

def configurar_comunicacion_anillo(ssh, vms):
    for i in range(len(vms)):
        vlan1 = vms[i]['vlan_tag']
        vlan2 = vms[(i + 1) % len(vms)]['vlan_tag']
        print(f"Habilitando comunicación entre VLAN {vlan1} y VLAN {vlan2}...")
        out, err = ejecutar_comando_ssh(ssh, f"./enable_vlan_communication.sh {vlan1} {vlan2}", sudo=True)
        print(out)
        if err:
            print(f"Error: {err}")

def configurar_comunicacion_lineal(ssh, vms):
    for i in range(len(vms) - 1):
        vlan1 = vms[i]['vlan_tag']
        vlan2 = vms[i + 1]['vlan_tag']
        print(f"Habilitando comunicación entre VLAN {vlan1} y VLAN {vlan2}...")
        out, err = ejecutar_comando_ssh(ssh, f"./enable_vlan_communication.sh {vlan1} {vlan2}", sudo=True)
        print(out)
        if err:
            print(f"Error: {err}")

def habilitar_internet(ssh, vms):
    for vm in vms:
        if vm['internet']:
            print(f"Habilitando acceso a internet para VLAN {vm['vlan_tag']}...")
            out, err = ejecutar_comando_ssh(ssh, f"./enable_vlan_internet_access.sh {vm['vlan_tag']}", sudo=True)
            print(out)
            if err:
                print(f"Error: {err}")

def desplegar_vms(ssh, vms):
    worker_ips = {'1': '10.0.0.30', '2': '10.0.0.40', '3': '10.0.0.50'}
    for vm in vms:
        worker_ip = worker_ips[vm['worker_num']]
        print(f"Conectando al {vm['worker']} ({worker_ip})...")

        create_vm_command = f"ssh {worker_ip} 'echo zenbook13 | sudo -S ./create_vm.sh {vm['nombre']} br-int {vm['vlan_tag']} {vm['vlan_tag'] // 100}'"
        print(f"Creando {vm['nombre']} en {vm['worker']}...")
        out, err = ejecutar_comando_ssh(ssh, create_vm_command)
        print(out)
        if err:
            print(f"Error al crear VM: {err}")
        
        init_worker_command = f"ssh {worker_ip} 'echo zenbook13 | sudo -S ./init_worker.sh br-int ens4'"
        out, err = ejecutar_comando_ssh(ssh, init_worker_command)
        print(out)
        if err:
            print(f"Error al inicializar worker: {err}")

def mostrar_resumen(vms, vm_conexion):
    print("\nResumen de la configuración:")
    print("Topología: Combinada (Anillo y Lineal)")
    print(f"VM de conexión entre topologías: {vm_conexion['nombre']}")
    for vm in vms:
        print(f"\n{vm['nombre']}:")
        print(f"  RAM: {vm['ram']} GB")
        print(f"  Almacenamiento: {vm['almacenamiento']} GB")
        print(f"  Conexión a internet: {'Sí' if vm['internet'] else 'No'}")
        print(f"  Desplegada en: {vm['worker']}")
        print(f"  VLAN tag: {vm['vlan_tag']}")

if __name__ == "__main__":
    configurar_vms()