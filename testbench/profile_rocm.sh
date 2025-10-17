#!/bin/bash

LOGFILE="${LOGFILE:-rocm_gpu_profile.csv}"
INTERVAL=1  # in seconds

echo "timestamp,gpu_usage_percent,vram_used_mib,temp_celsius,power_watts" > "$LOGFILE"

while true; do
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

  USAGE=$(rocm-smi --showuse | grep -m1 'GPU\[0\]' | awk -F ':' '{print $3}' | tr -d ' %' | xargs)
  MEM=$(rocm-smi --showmemuse | grep -m1 'GPU\[0\]' | awk -F ':' '{print $3}' | tr -d ' MiB' | xargs)
  TEMP=$(rocm-smi --showtemp | grep -m1 'GPU\[0\]' | awk -F ':' '{print $3}' | tr -d ' Cc' | xargs)
  POWER=$(rocm-smi --showpower | grep -m1 'GPU\[0\]' | awk -F ':' '{print $3}' | tr -d ' Ww' | xargs)

  echo "$TIMESTAMP,$USAGE,$MEM,$TEMP,$POWER" >> "$LOGFILE"

  sleep $INTERVAL
done
