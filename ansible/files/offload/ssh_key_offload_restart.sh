#!/bin/bash
# Managed by Ansible
# Restarted offload service after deployment of SSH key, iff already running

SERVICE="ont-platform-data-offload.service"
STATUS="$(/bin/systemctl is-active ${SERVICE})"

if [[ "${STATUS}" == "failed" ]]
then
    echo "Restarting ${SERVICE}"
    /bin/systemctl restart $SERVICE
else
    echo "Service ${SERVICE} not running, ignoring"
fi
