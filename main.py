import gc

from utime import sleep
sleep(4)

import control
control.run()

gc.collect()
