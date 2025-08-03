#!/bin/bash
# 🔧 Script de configuração automática do AP + BLE com NGINX
# ⚠️ Usar com cabo Ethernet ligado (eth0), não por Wi-Fi (wlan0)

set -e

SSID="Gateway-IoT"
WLAN_IFACE="wlan0"
STATIC_IP="192.168.4.1"

# 1. Parar serviços de rede temporariamente
sudo systemctl stop wpa_supplicant.service || true
sudo systemctl stop dhcpcd || true
sudo ifconfig $WLAN_IFACE down
sleep 1

# 2. Definir IP estático no wlan0 para o AP
sudo ip link set $WLAN_IFACE up
sudo ip addr add $STATIC_IP/24 dev $WLAN_IFACE

# 3. Configurar dnsmasq (DHCP + DNS local)
echo "interface=$WLAN_IFACE
dhcp-range=192.168.4.10,192.168.4.100,255.255.255.0,24h
domain-needed
bogus-priv
address=/#/$STATIC_IP" | sudo tee /etc/dnsmasq.conf > /dev/null

# 4. Configurar hostapd (Access Point)
echo "interface=$WLAN_IFACE
ssid=$SSID
hw_mode=g
channel=7
wmm_enabled=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=gateway1234
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP" | sudo tee /etc/hostapd/hostapd.conf > /dev/null

sudo sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

# 5. Ativar NGINX para servir a app Web BLE
echo "<html><body><h1>🔧 Gateway BLE Pronto</h1><p>A configurar via BLE...</p></body></html>" | sudo tee /var/www/html/index.html > /dev/null
sudo systemctl enable nginx
sudo systemctl restart nginx

# 6. Ativar serviços do AP
sudo systemctl enable dnsmasq
sudo systemctl enable hostapd
sudo systemctl start dnsmasq
sudo systemctl start hostapd

# 7. Confirmar
echo "✅ AP criado como $SSID (IP: $STATIC_IP)"
echo "🌐 Abre o browser e acede a http://$STATIC_IP para configurar via BLE"
echo "ℹ️ Quando terminar, corre o script de reset: reset_network.sh"
