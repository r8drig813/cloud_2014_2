import paramiko

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

def limpiar_topologia():
    print("\nIniciando limpieza de la topología")
    
    # Configuración de SSH para headnode
    headnode_ssh = conectar_ssh('10.20.12.187', 5800, 'ubuntu', 'zenbook13')
    if not headnode_ssh:
        return

    # Limpiar headnode
    print("Limpiando headnode...")
    out, err = ejecutar_comando_ssh(headnode_ssh, "./cleanup_ovs.sh", sudo=True)
    print(out)
    if err:
        print(f"Error en headnode: {err}")

    # Limpiar workers
    worker_ips = {'1': '10.0.0.30', '2': '10.0.0.40', '3': '10.0.0.50'}
    for worker_num, worker_ip in worker_ips.items():
        print(f"Limpiando Worker {worker_num} ({worker_ip})...")
        cleanup_worker_command = f"ssh {worker_ip} 'echo zenbook13 | sudo -S ./cleanup_ovs_interfaces.sh'"
        out, err = ejecutar_comando_ssh(headnode_ssh, cleanup_worker_command)
        print(out)
        if err:
            print(f"Error al limpiar Worker {worker_num}: {err}")

    headnode_ssh.close()
    print("Proceso de limpieza completado.")

if __name__ == "__main__":
    limpiar_topologia()