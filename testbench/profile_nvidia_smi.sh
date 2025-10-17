#!/bin/bash

LOGFILE="${LOGFILE:-nvidia_gpu_profile.csv}"
INTERVAL=1  # in seconds

echo "timestamp,gpu_usage_percent,vram_used_mib,temp_celsius,power_watts" > "$LOGFILE"

while true; do
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

  STATS=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu,power.draw --format=csv,noheader,nounits | head -n 1)

  # Split the comma-separated values
  USAGE=$(echo "$STATS" | cut -d ',' -f1 | xargs)
  MEM=$(echo "$STATS" | cut -d ',' -f2 | xargs)
  TEMP=$(echo "$STATS" | cut -d ',' -f3 | xargs)
  POWER=$(echo "$STATS" | cut -d ',' -f4 | xargs)

  echo "$TIMESTAMP,$USAGE,$MEM,$TEMP,$POWER" >> "$LOGFILE"

  sleep $INTERVAL
done
