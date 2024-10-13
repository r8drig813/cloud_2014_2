#!/bin/bash

# Parámetros
VM_NAME=$1
OVS_NAME=$2
VLAN_ID=$3
VNC_PORT=$4
IMAGE_CHOICE=$5
RAM=$6  # Nueva variable para la RAM (en MB)
CPU=$7  # Nueva variable para el número de CPUs

# Imágenes disponibles
CIRROS_IMAGE="cirros-0.6.2-x86_64-disk.img"
UBUNTU_IMAGE="focal-server-cloudimg-amd64.img"

# Función para verificar si se está ejecutando como root
check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo "Este script debe ser ejecutado como root" 1>&2
        exit 1
    fi
}

# Función para crear la interfaz TAP
create_tap_interface() {
    echo "Creando interfaz TAP ${VM_NAME}-tap..."
    ip tuntap add mode tap name ${VM_NAME}-tap
    ip link set ${VM_NAME}-tap up
}

# Función para conectar la interfaz TAP al OvS con VLAN ID
connect_tap_to_ovs() {
    echo "Conectando ${VM_NAME}-tap al OvS $OVS_NAME con VLAN ID $VLAN_ID..."
    ovs-vsctl add-port $OVS_NAME ${VM_NAME}-tap tag=$VLAN_ID
}

# Función para crear y iniciar la VM
create_and_start_vm() {
    local disk_image

    case $IMAGE_CHOICE in
        1)
            disk_image=$CIRROS_IMAGE
            echo "Usando imagen CirrOS: $disk_image"
            ;;
        2)
            disk_image=$UBUNTU_IMAGE
            echo "Usando imagen Ubuntu: $disk_image"
            ;;
    esac

    echo "Creando y iniciando la VM $VM_NAME..."
    qemu-system-x86_64 \
    -enable-kvm \
    -name $VM_NAME \
    -m $RAM \
    -smp $CPU \
    -vnc 0.0.0.0:$VNC_PORT \
    -netdev tap,id=${VM_NAME}-tap,ifname=${VM_NAME}-tap,script=no,downscript=no \
    -device e1000,netdev=${VM_NAME}-tap,mac=$(printf '52:54:00:%02X:%02X:%02X\n' $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256))) \
    -daemonize \
    -snapshot \
    $disk_image
}

# Verificar el número correcto de argumentos
if [ $# -ne 7 ]; then
    echo "Uso: $0 <VM_NAME> <OVS_NAME> <VLAN_ID> <VNC_PORT> <IMAGE_CHOICE> <RAM_MB> <CPU_COUNT>"
    echo "IMAGE_CHOICE: 1 para CirrOS, 2 para Ubuntu"
    echo "RAM_MB: Cantidad de RAM en megabytes"
    echo "CPU_COUNT: Número de CPUs virtuales"
    exit 1
fi

# Ejecución principal
check_root
create_tap_interface
connect_tap_to_ovs
create_and_start_vm

echo "VM $VM_NAME creada con $RAM MB de RAM y $CPU CPUs, conectada al OvS $OVS_NAME con VLAN ID $VLAN_ID y VNC en el puerto $VNC_PORT."