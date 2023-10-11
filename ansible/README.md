A collection of playbooks for configuring various aspects of Promethion servers.

In the `example_configs` and `example_files` directories you may find samples to copy into `configs` and `files` with appropriate local modifications.

# Security warning

Some of the scripts will deploy sensitive files such as SSH private keys. Ensure they are suitably protected on the machine from which you run Ansible, e.g. only present when the playbooks are run.

# Playbook descriptions

## bootstrap

Does initial configuration enabling the other playbooks to work e.g. creates a `sysadmin` user for management access.

## configure_all

Combines all of the other playbooks (except `bootstrap`).

## configure_minknow

Configures the Minknow service - currently just deploys the user_conf file.

## configure_misc

Configures some things such as bash prompt and enhancements, use or customise according to taste.

## configure_offload

Configures the offload service to support rsync-over-SSH and its destination, include private key for this (see warning above).

## configure_security

Sets a known password for the `prom` user, disables root login access. Only allows `sysadmin` user to SSH in.

## conifugre_telegraf

Installs [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) and configures it.

