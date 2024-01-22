# PromethION scripts

This repo is a collection of assorted sysadmin tasks for managing
Oxford Nanopore PromethION sequencers (or more acurately, the data
acquisition machines that accompany them).

None of this work is expected to be in any way portable to other
devices.

`prom-luks-data` will destroy the existing filesystem mounted on
/data and replace it with a encrypted LUKS volume. The password
set will then need to be provided on each reboot. WARNING: this
configuration has been found to be unsuitable at higher sample
throughput (> 16 samples).
