# Reworked from asyn.py / sonoff.py Peter Hinch (c) 2017

#import uasyncio as asyncio
from umqtt.robust import MQTTClient
from machine import Pin, Signal
import ujson

# MQTT Information
SERVER = '10.0.1.5'
CLIENT = 'sonoff1'
T_IN = b'cmnd/sonoff1/power'
T_RESULT = b'stat/sonoff1/RESULT'
T_OUT = b'stat/sonoff1/POWER'
M_ON = b'ON'
M_OFF = b'OFF'

#loop = asyncio.get_event_loop()
# moved content to test.py

class Sonoff():
    led = Signal(Pin(13, Pin.OUT, value = 1), invert = True)
    relay = Pin(12, Pin.OUT, value = 0)
#    button = Pushbutton(Pin(0, Pin.IN))
    mqtt = MQTTClient(CLIENT, SERVER)

    def __init__(self):
        self.state = self.led.value()

    def sub_cb(self, topic, msg):
        if topic == T_IN:
            if msg == M_ON:
                self.relay.on()
                self.led.on()
            elif msg == M_OFF:
                self.relay.off()
                self.led.off()
            self.pub_msg(T_OUT, msg)
            self.state = self.led.value()

    def pub_msg(self, topic, msg):
        m_out = {}
        m_out['POWER'] = msg
        self.mqtt.publish(T_RESULT, ujson.dumps(m_out))
        self.mqtt.publish(topic, msg)

    def main(self):
        self.mqtt.connect()
        self.mqtt.set_callback(self.sub_cb)
        self.mqtt.subscribe(T_IN)
        while True:
            self.mqtt.wait_msg()
        print('exiting')

def run():
    MQTTClient.DEBUG = True
    switch = Sonoff()
    switch.main()
