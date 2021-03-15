#!/usr/bin/env python3

from rak811v2 import Rak811v2

joinmode = 'ABP'

print('Initialising Rak811 library')
lora = Rak811v2()

print('Hard reset of module')
lora.hard_reset()

print('Issue module help command and display response')
lora.help()
resp=lora.get_info()
for x in resp:
    print('\t',x)

print('Get lora status from module')
lora.get_config('lora:status')
resp=lora.get_info()
for x in resp:
    print('\t',x)

print('Set loRa work mode to 0')
status= lora.set_config('lora:work_mode:0')
resp=lora.get_info()
for x in resp:
    print('\t',x)

print('Set loRa region')
lora.set_config('lora:region:EU868')

if joinmode == 'OTA':
    print('Set join mode to OTA and configure appropriate keys')
    lora.set_config('lora:join_mode:0')
    lora.set_config('lora:app_eui:XXXXXXXXXXXXXX')
    lora.set_config('lora:app_key:XXXXXXXXXXXXXX')
else:
    print('Set join mode to ABP and set appropriate keys')
    lora.set_config('lora:join_mode:1')
    lora.set_config('lora:dev_addr:XXXXXXXXXXXXXX')
    lora.set_config('lora:nwks_key:XXXXXXXXXXXXXX')
    lora.set_config('lora:apps_key:XXXXXXXXXXXXXX')

print('Set data rate to 5')
lora.set_config('lora:dr:5')

print('Join to LoRa network')
status = lora.join()

print('Set LoRa to confirmation mode')
lora.set_config('lora:confirm:1')

print('Send data via LoRa on port 5')
status = lora.send_lora('Hello World', port=5)
print('Wait for and display confirmation response')
events=lora.get_events(timeout=10)
for x in events:
    print('\t',x)

print('Close connection to module')
lora.close()