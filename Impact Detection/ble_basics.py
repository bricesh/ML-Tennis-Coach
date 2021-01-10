import bluepy.btle as btle
import struct

def enable_notify(peri,  chara_uuid):
    setup_data = b"\x01\x00"
    notify = peri.getServiceByUUID(list(services)[2].uuid).getCharacteristics(chara_uuid)[0]
    notify_handle = notify.getHandle() + 1
    peri.writeCharacteristic(notify_handle, setup_data, withResponse=True)

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        # ... initialise here

    def handleNotification(self, cHandle, data):
        print(struct.unpack('f', data)[0])
        # ... perhaps check cHandle
        # ... process 'data'


# Initialisation  -------
p = btle.Peripheral("4f:34:42:8e:e0:00")
p.setDelegate(MyDelegate())
services = p.getServices()
enable_notify(p, list(services)[2].getCharacteristics()[0].uuid)
enable_notify(p, list(services)[2].getCharacteristics()[1].uuid)
enable_notify(p, list(services)[2].getCharacteristics()[2].uuid)

# Setup to turn notifications on, e.g.
#   svc = p.getServiceByUUID( service_uuid )
#   ch = svc.getCharacteristics( char_uuid )[0]
#   ch.write( setup_data )
#services = p.getServices()
#s = p.getServiceByUUID(list(services)[2].uuid)

#for c in s.getCharacteristics():
#    print(struct.unpack('f', c.read())[0])
# Main loop --------

while True:
    if p.waitForNotifications(5.0):
        # handleNotification() was called
        continue

    print("Waiting...")
    # Perhaps do something else here


#import bluepy.btle as btle
#from time import sleep
#import struct

#p = btle.Peripheral("4f:34:42:8e:e0:00")
#services = p.getServices()
#s = p.getServiceByUUID(list(services)[2].uuid)

#for c in s.getCharacteristics():
#    print(struct.unpack('f', c.read())[0])

#c = s.getCharacteristics()[0]
#while (1):
#    c.write(b'\x00', withResponse=True)
#    sleep(1)
#    c.write(b'\x01', withResponse=True)
#    sleep(1)

p.disconnect()



# from bluepy.btle import Scanner, DefaultDelegate
# 
# class ScanDelegate(DefaultDelegate):
#     def __init__(self):
#         DefaultDelegate.__init__(self)
# 
#     def handleDiscovery(self, dev, isNewDev, isNewData):
#         if isNewDev:
#             print("Discovered device", dev.addr)
#         elif isNewData:
#             print("Received new data from", dev.addr)
# 
# scanner = Scanner().withDelegate(ScanDelegate())
# devices = scanner.scan(10.0)
# 
# for dev in devices:
#     print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
#     for (adtype, desc, value) in dev.getScanData():
#         print("  %s = %s" % (desc, value))