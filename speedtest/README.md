# Rsync speedtest script

This script is used to do concurrent rsync "speed tests" on multiple sources
to the same destination, in order to ascertain aggregate throughput.

To run, load an SSH key which has access to all source and destination servers
into your SSH agent.

## InfluxDB wrapper

This script is designed to be used on a schedule (cron job) and send results to
an InfluxDB instance. It will optionally pull the SSH private key passphrase
from a Hashicorp Vault server.
