import paramiko
import networkx as nx
import matplotlib.pyplot as plt
import json

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

def ver_slices():
    print("\nRecuperando información de los slices...")
    
    # Configuración de SSH para headnode
    headnode_ssh = conectar_ssh('10.20.12.187', 5800, 'ubuntu', 'zenbook13')
    if not headnode_ssh:
        return

    # Obtener información de las VMs
    print("Obteniendo información de las VMs...")
    out, err = ejecutar_comando_ssh(headnode_ssh, "cat /home/ubuntu/vm_info.json", sudo=True)
    if err:
        print(f"Error al obtener información de las VMs: {err}")
        return

    try:
        vm_info = json.loads(out)
        topologia = vm_info["topologia"]
        vms = vm_info["vms"]
    except json.JSONDecodeError:
        print("Error al decodificar la información de las VMs.")
        return
    except KeyError:
        print("El formato del archivo JSON no es el esperado.")
        return

    # Mostrar información de las VMs
    print(f"\nTopología: {topologia}")
    print(f"Número total de VMs: {len(vms)}")
    for vm in vms:
        print(f"\n{vm['nombre']}:")
        print(f"  RAM: {vm['ram']} GB")
        print(f"  Almacenamiento: {vm['almacenamiento']} GB")
        print(f"  Conexión a internet: {'Sí' if vm['internet'] else 'No'}")
        print(f"  Desplegada en: {vm['worker']}")
        print(f"  VLAN tag: {vm['vlan_tag']}")

    # Visualizar la topología
    visualizar_topologia(vms, topologia)

    headnode_ssh.close()

if __name__ == "__main__":
    ver_slices()