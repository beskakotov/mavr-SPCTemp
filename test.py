from control import RODOS
from time import sleep
RODOS.search_sensors()
RODOS.__set_temperature_precision__(3)
i = 0
while True:
    RODOS.__skip_rom_convert__()
    print(f"{i:04d}", RODOS.__get_temperature__(RODOS.__sensors__[0]), ' '*25, end='\r')
    sleep(1)
    i += 1