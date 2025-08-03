import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
ADAPTER_PATH = '/org/bluez/hci0'

SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        if interface != 'org.bluez.LEAdvertisement1':
            raise Exception('Invalid interface')
        if prop == 'Type':
            return 'peripheral'
        elif prop == 'ServiceUUIDs':
            return dbus.Array([SERVICE_UUID], signature='s')
        elif prop == 'LocalName':
            return 'RaspberryPi-GATT'
        elif prop == 'Includes':
            return dbus.Array(['tx-power'], signature='s')
        elif prop == 'Discoverable':
            return True
        raise Exception('Invalid property')

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        return {
            'Type': 'peripheral',
            'ServiceUUIDs': dbus.Array([SERVICE_UUID], signature='s'),
            'LocalName': 'RaspberryPi-GATT',
            'Includes': dbus.Array(['tx-power'], signature='s'),
        }

    @dbus.service.method('org.bluez.LEAdvertisement1', in_signature='')
    def Release(self):
        print('🔕 Advertising released')

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = dbus.Interface(bus.get_object('org.bluez', ADAPTER_PATH), ADVERTISING_MANAGER_IFACE)

    ad = Advertisement(bus, 0)
    adapter.RegisterAdvertisement(ad.get_path(), {},
        reply_handler=lambda: print('📣 Advertising iniciado com sucesso.'),
        error_handler=lambda e: print('❌ Erro ao iniciar advertising:', e))

    GLib.MainLoop().run()

if __name__ == '__main__':
    main()
