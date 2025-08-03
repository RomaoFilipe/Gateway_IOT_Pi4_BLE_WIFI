import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import subprocess
import os

BLUEZ_SERVICE_NAME = 'org.bluez'
ADAPTER_PATH = '/org/bluez/hci0'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHARACTERISTIC_IFACE = 'org.bluez.GattCharacteristic1'

SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'
SSID_UUID = '12345678-1234-5678-1234-56789abcdef1'
PASS_UUID = '12345678-1234-5678-1234-56789abcdef2'
SCAN_UUID = '12345678-1234-5678-1234-56789abcdef3'

class WifiCharacteristic(dbus.service.Object):
    def __init__(self, bus, path, uuid, service, is_readable=False):
        self.path = path
        self.uuid = uuid
        self.service = service
        self.value = b""
        self.is_readable = is_readable
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='ss', out_signature='v')
    def Get(self, interface, property):
        if interface != GATT_CHARACTERISTIC_IFACE:
            raise Exception('Invalid interface')
        if property == 'UUID':
            return self.uuid
        elif property == 'Service':
            return dbus.ObjectPath(self.service.path)
        elif property == 'Flags':
            flags = ['read'] if self.is_readable else ['write']
            return dbus.Array(flags, signature='s')
        else:
            raise Exception('Invalid property')

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        if self.is_readable:
            return
        decoded = bytes(value).decode()
        self.value = decoded.encode()
        print(f"🔹 {self.uuid} recebeu: {decoded}")

        if self.uuid == PASS_UUID:
            ssid = self.service.ssid.value.decode()
            password = decoded
            if ssid and password:
                self.configure_wifi(ssid, password)

    def configure_wifi(self, ssid, password):
        # Verificar se já existe no wpa_supplicant.conf
        try:
            with open("/etc/wpa_supplicant.conf", "r") as f:
                content = f.read()
                if ssid in content:
                    print(f"⚠️ SSID '{ssid}' já existe. Ignorar gravação duplicada.")
                    return
        except FileNotFoundError:
            pass

        config = f"""network={{
    ssid=\"{ssid}\"
    psk=\"{password}\"
}}
"""
        try:
            with open("/etc/wpa_supplicant.conf", "a") as f:
                f.write(config)
            print("💾 Wi-Fi gravado em /etc/wpa_supplicant.conf")
        except Exception as e:
            print(f"❌ Erro ao gravar: {e}")
            return

        result = subprocess.run(["wpa_cli", "-i", "wlan0", "reconfigure"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Wi-Fi reiniciado com sucesso")
        else:
            print(f"❌ Falha ao reiniciar Wi-Fi: {result.stderr}")

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        if self.uuid == SCAN_UUID:
            print("📡 A fazer scan de redes Wi-Fi...")
            try:
                result = subprocess.check_output("sudo iwlist wlan0 scan | grep 'ESSID'", shell=True, text=True)
                ssids = [line.split('ESSID:"')[1].strip('"') for line in result.strip().split('\n') if 'ESSID' in line]
                ssids = list(set([s for s in ssids if s.strip()]))  # remover duplicados e vazios
                redes = ','.join(ssids)
                print(f"📶 Redes encontradas: {redes}")
                return dbus.ByteArray(redes.encode())
            except Exception as e:
                print(f"❌ Erro no scan: {e}")
                return dbus.ByteArray(b"Erro")
        return dbus.ByteArray(self.value)

class WifiService(dbus.service.Object):
    def __init__(self, bus, path):
        self.path = path
        self.uuid = SERVICE_UUID
        dbus.service.Object.__init__(self, bus, path)
        self.ssid = WifiCharacteristic(bus, path + '/char0', SSID_UUID, self)
        self.password = WifiCharacteristic(bus, path + '/char1', PASS_UUID, self)
        self.scan = WifiCharacteristic(bus, path + '/char2', SCAN_UUID, self, is_readable=True)

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='ss', out_signature='v')
    def Get(self, interface, property):
        if interface != GATT_SERVICE_IFACE:
            raise Exception('Invalid interface')
        if property == 'UUID':
            return self.uuid
        elif property == 'Primary':
            return True
        elif property == 'Characteristics':
            return dbus.Array([self.ssid.path, self.password.path, self.scan.path], signature='o')
        else:
            raise Exception('Invalid property')

class GattApplication(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        dbus.service.Object.__init__(self, bus, self.path)
        self.service = WifiService(bus, '/wifi/service0')

    @dbus.service.method('org.freedesktop.DBus.ObjectManager', out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        return {
            self.service.path: {
                GATT_SERVICE_IFACE: {
                    'UUID': self.service.uuid,
                    'Primary': True,
                    'Characteristics': dbus.Array([
                        self.service.ssid.path,
                        self.service.password.path,
                        self.service.scan.path
                    ], signature='o')
                }
            },
            self.service.ssid.path: {
                GATT_CHARACTERISTIC_IFACE: {
                    'UUID': self.service.ssid.uuid,
                    'Service': dbus.ObjectPath(self.service.path),
                    'Flags': dbus.Array(['write'], signature='s')
                }
            },
            self.service.password.path: {
                GATT_CHARACTERISTIC_IFACE: {
                    'UUID': self.service.password.uuid,
                    'Service': dbus.ObjectPath(self.service.path),
                    'Flags': dbus.Array(['write'], signature='s')
                }
            },
            self.service.scan.path: {
                GATT_CHARACTERISTIC_IFACE: {
                    'UUID': self.service.scan.uuid,
                    'Service': dbus.ObjectPath(self.service.path),
                    'Flags': dbus.Array(['read'], signature='s')
                }
            }
        }

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, ADAPTER_PATH), GATT_MANAGER_IFACE)
    app = GattApplication(bus)

    adapter.RegisterApplication(app.path, {},
        reply_handler=lambda: print("✅ GATT Server registado."),
        error_handler=lambda e: print("❌ Erro:", e))

    GLib.MainLoop().run()

if __name__ == '__main__':
    main()
