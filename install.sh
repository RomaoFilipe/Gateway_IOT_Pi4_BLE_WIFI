#!/bin/bash

echo "🔄 Atualizar pacotes..."
sudo apt update && sudo apt upgrade -y

echo "📦 A instalar dependências BLE..."
sudo apt install -y bluez python3-dbus libglib2.0-dev bluetooth pi-bluetooth

echo "🔧 A ativar Bluetooth + modo LE Advertising..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo hciconfig hci0 up
sudo hciconfig hci0 leadv

echo "🧹 A limpar estrutura duplicada do projeto..."
rm -rf ~/gateway_ble/gateway_ble
rm -rf ~/gateway_ble/.venv

echo "✅ Tudo pronto!"

echo ""
echo "🚀 Para correr o GATT Server:"
echo "cd ~/gateway_ble/ble_config"
echo "sudo python3 gatt_server.py"
