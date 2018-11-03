# Reworked from asyn.py / sonoff.py Peter Hinch (c) 2017

import gc
import utime as time
import uasyncio as asyncio
from umqtt.robust import MQTTClient
from machine import Pin, Signal
import ujson

# MQTT Information
SERVER = '10.0.1.5'
CLIENT = 'sonoff1'
T_IN = b'cmnd/sonoff1/power'
T_RESULT = b'stat/sonoff1/result'
T_OUT = b'stat/sonoff1/power'
R_ON = b'{"POWER": "ON"}'
M_ON = b'ON'
R_OFF = b'{"POWER": "OFF"}'
M_OFF = b'OFF'
M_BUTTON = b'BUTTON PRESSED'

# event loop
loop = asyncio.get_event_loop()

class Sonoff():
    led = Signal(Pin(13, Pin.OUT, value = 1), invert = True)
    relay = Pin(12, Pin.OUT, value = 0)
    button = Pin(0, Pin.IN, Pin.PULL_UP)
    mqtt = MQTTClient(CLIENT, SERVER)
    q = []

    def __init__(self):
        self.q.insert(0, self.led.value())

    def sub_cb(self, topic, msg):
        if topic == T_IN:
            # set state
            self.q.insert(0, int(msg == M_ON))

    def notify(self, topic, msg):
        task = loop.create_task(self.pub_msg(topic, msg))

    async def pub_msg(self, topic, msg):
        self.mqtt.publish(topic, msg)

    async def push_button(self):
        while True:
            start = time.ticks_ms()
            while self.button.value() == 0:
                pass
            pushed = time.ticks_diff(time.ticks_ms(), start)
            if pushed > 20:
                self.notify(T_OUT, M_BUTTON)
                self.q.insert(0, not self.led.value())
                pushed = 0
            await asyncio.sleep_ms(10)

    async def switch(self):
        while True:
            if self.q:
                state = self.q.pop()
                self.relay(state)
                self.led(state)
                if state == 1:
                    self.notify(T_RESULT, R_ON)
                    self.notify(T_OUT, M_ON)
                else:
                    self.notify(T_RESULT, R_OFF)
                    self.notify(T_OUT, M_OFF)
            await asyncio.sleep_ms(500)

    async def main(self):
        self.mqtt.connect()
        self.mqtt.set_callback(self.sub_cb)
        self.mqtt.subscribe(T_IN)
        task1 = loop.create_task(self.switch())
        task2 = loop.create_task(self.push_button())
        while True:
            self.mqtt.check_msg()
            await asyncio.sleep_ms(500)
        print('exiting')

def run():
    MQTTClient.DEBUG = True
    sw = Sonoff()
    try:
        loop.run_until_complete(sw.main())
    finally:
        loop.close()
