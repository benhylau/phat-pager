pHAT Pager
==========

A toy pager that receives messages from a MQTT broker when it can connect via WiFi, and prints the most recent message on an eInk display. Messages are published from the same server running the MQTT broker, which is only accessible from authenticated devices via an encrypted tunnel. Communication between _Server_ and _Pager_ is end-to-end encrypted using Yggdrasil, and permissioned by iptables firewall pinning to the persistent Yggdrasil IPv6 address.

![phat-pager](phat-pager.gif)

Pager hardware from Adafruit:

- [Pimoroni Inky pHAT](https://www.adafruit.com/product/3933) eInk display
- [Raspberry Pi Zero W](https://www.adafruit.com/product/3400) with header
- [C4Labs Zebra Zero](https://www.adafruit.com/product/3003) case

## Configuring the Server

Start with a Debian Stretch VM with a publicly accessible IP address and configure MQTT:

- Install [Mosquitto](https://mosquitto.org) with the `mosquitto` and `mosquitto-clients` Debian packages and ensure the MQTT broker's `systemd` service is running
- Install `jq` for JSON processing in bash
- Copy the `send-message` script and publish a message like this:
    ```
    ./send-message "pHAT PAGER" "featuring" "+ indexed-colour PNGs" "+ _extra_ Entropy"
    ```

Configure end-to-end encryption and IP address authentication with Yggdrasil:

- Install [Yggdrasil](https://yggdrasil-network.github.io) and ensure its `systemd` service is running
- Install `iptables-persistent`
- Add a rule to `/etc/iptables/rules.v6` that exposes the MQTT port `1883` only to `PAGER_YGGDRASIL_IPv6`:
    ```
    -A INPUT -p tcp -s PAGER_YGGDRASIL_IPv6 --dport 1883 -j ACCEPT
    ```
- Apply the firewall rule with:
    ```
    ip6tables-apply /etc/iptables/rules.v6
    ```

## Configuring the Pager

Prepare your Raspberry Pi Zero W:

- Flash [Raspbian Stretch Lite](https://www.raspberrypi.org/downloads/raspbian/) on SD card
- Enable SSH access and connect to device via SSH
- Use `sudo raspi-config` to enable WiFi and set a new password

Install drivers for eInk display:

- Follow [Getting Started with Inky pHAT](https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-inky-phat)
- Try some of the examples to ensure the eInk display is working

Configure Yggdrasil and peer with the Server:

- Install the [Yggdrasil build for armhf](https://yggdrasil-network.github.io/builds.html)
- Enable and start the `yggdrasil` service in `systemd`
- Add the Server as a peer in `/etc/yggdrasil.conf` and restart the service
- Install `haveged` (otherwise Yggdrasil may wait a _long_ time to start after a reboot waiting for sufficient entropy)
- Try to `ping6 SERVER_YGGDRASIL_IPv6` to ensure the Pager can reach the Server over the Yggdrasil encrypted tunnel

Configure MQTT and pHAT Pager script:

- Install the [Python MQTT client](https://www.eclipse.org/paho/) with `sudo pip install paho-mqtt`
- Copy the contents of `sub` to `/home/pi/phat-pager/` on device
- In `/home/pi/phat-pager/phat-pager.py`, change the `MQTT_HOST` to `SERVER_YGGDRASIL_IPv6`
- In `/home/pi/phat-pager/phat-pager.service`, change the colour on the `ExecStart` line to that of your Inky pHAT model
- Move the `phat-pager.service` file to `/etc/systemd/system/` then `daemon-reload`, `enable`, and `start` the service
- The eInk display should refresh and show the most recent message
- Push a new message from the Server and the Pager eInk display should refresh immediately
- Reboot the Pager and verify that the Pager eInk display refreshes immediately after boot and each time a new message is published to the MQTT broker