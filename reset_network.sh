#!/bin/bash
echo "🧹 A restaurar modo Wi-Fi cliente..."

# Parar e desativar serviços do AP
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo systemctl disable hostapd
sudo systemctl disable dnsmasq

# Limpar IP e reiniciar interface
sudo ip addr flush dev wlan0
sudo ip link set wlan0 down
sleep 2
sudo ip link set wlan0 up

# Ativar wpa_supplicant e DHCP
sudo systemctl enable wpa_supplicant
sudo systemctl restart wpa_supplicant

# Se tiver dhcpcd instalado, reiniciar
if systemctl list-units --type=service | grep -q dhcpcd; then
  sudo systemctl enable dhcpcd
  sudo systemctl restart dhcpcd
fi

echo "✅ Wi-Fi restaurado. Podes agora ligar-te à rede real."
