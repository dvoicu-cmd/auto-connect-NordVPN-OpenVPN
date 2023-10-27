#!/usr/bin/env bash

# navigate to config file location in repo
echo Starting openVPN daemon
cd ..

# arg $1 -> username, arg $2 -> password
VPN_USER=$1
VPN_PASSWORD=$2

# Do a quick check and notify user
if [ -z "$VPN_USER" ]; then
  echo VPN_USER param is empty
  exit 1
fi
if [ -z "$VPN_PASSWORD" ]; then
  echo VPN_PASSWORD param is empty
  exit 1
fi

# start openvpn daemon with the config file
openvpn --auth-user-pass --daemon --config saved-config-file/config.ovpn --auth-user-pass <(echo -e "$VPN_USER\n$VPN_PASSWORD")
echo Started given the credentials in server_target.cfg

# return directory
cd start-stop-OpenVPN/
exit 0
