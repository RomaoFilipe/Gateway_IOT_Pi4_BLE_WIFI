"""
Script BLE Listener com bluepy - Raspberry Pi 4
Recebe SSID e Password via Bluetooth BLE e guarda em /etc/wpa_supplicant.conf
"""

from bluepy.btle import DefaultDelegate
import subprocess
import os
import platform

class WifiConfigDelegate(DefaultDelegate):
    def __init__(self):
        super().__init__()
        self.ssid = "SSID_EXEMPLO"
        self.password = "PASS_EXEMPLO"
        self.apply_wifi_config()

    def apply_wifi_config(self):
        config = f"""
network={{
    ssid="{self.ssid}"
    psk="{self.password}"
}}
"""
        try:
            with open("/etc/wpa_supplicant.conf", "a") as f:
                f.write(config)
            print("💾 Configuração Wi-Fi gravada.")
        except PermissionError:
            print("❌ Erro: Permissão negada para escrever no wpa_supplicant.conf.")
            return

        # Verifica se estamos em WSL
        if "microsoft" in platform.uname().release.lower():
            print("⚠️ Ambiente WSL detetado — a reinicialização do Wi-Fi será ignorada.")
        else:
            print("🔁 A tentar reiniciar Wi-Fi com wpa_cli...")
            result = subprocess.run(["wpa_cli", "-i", "wlan0", "reconfigure"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Wi-Fi reiniciado com sucesso.")
            else:
                print("❌ Falha ao reiniciar Wi-Fi:", result.stderr)

        os._exit(0)

def main():
    print("🔍 A iniciar serviço BLE com bluepy...")
    WifiConfigDelegate()

if __name__ == "__main__":
    main()
