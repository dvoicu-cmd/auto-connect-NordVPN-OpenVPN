#!/usr/bin/env bash

# Kill the openvpn daemon
ps ax | grep 'openvpn' | awk -F ' ' '{print $1}' | xargs sudo kill -9
echo process killed
exit 0
