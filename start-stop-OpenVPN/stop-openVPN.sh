#!/usr/bin/env bash

# Kill the openvpn daemon
pid=$(pgrep -x openvpn)

# Check if the process is running.
if [[ -n $pid ]]; then
  # Kill the process.
  kill -9 $pid
  echo "Process killed successfully."
else
  echo "Process is not running."
fi

exit 0
