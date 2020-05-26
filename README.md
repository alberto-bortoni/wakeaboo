# Glucalarm

## GPIO pins in BCM mode

wack pins:
  ```console
  wacks (R->L)
  - buttons: 26, 13, 19
  - leds: 20, 21, 16
  - ground: (pin 39)
  timers (T->B)
  - buttons: 17, 27
  - ground: (pin 20)
  power
  - button: 24
  - leds: 22
  - ground: (pin 20)
  high-power led
  - led: 18 (PWM)
  - ground: (pin 14)
  matrices (pins):
  - power: 4
  - ground: 6
  - sda: 3
  - scl: 5
  - Address: disp16 (0x71), disp8 (0x70)
  ```

## Add autorun files
Copy file glucalarm.desktop from ./other and make sure that code can run

  ```console
  cd /home/boo/glucalarm
  sudo cp ./other/glucalarm.desktop /etc/xdg/autostart/glucalarm.desktop
  
  sudo chmod 777 *.py
  sudo chmod 777 *.sh
  ```
