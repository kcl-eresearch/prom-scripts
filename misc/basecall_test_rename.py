#!/usr/bin/python3

import json
import os
import re

exp_data = {}
suffix = "recoverd"

for i in os.scandir("/data/queued_reads"):
    if i.is_dir() and i.name.startswith("complete_reads_"):
        for j in os.scandir(i.path):
            if re.match(r"^experiment_data_[0-9a-f-]+\.json$", j.name):
                with open(j.path) as f:
                    data = json.load(f)
                    exp_data[data["tracking_id"]["sample_id"]] = {
                        "hostname": data["tracking_id"]["hostname"],
                        "device_id": data["tracking_id"]["device_id"],
                        "flow_cell_id": data["tracking_id"]["flow_cell_id"],
                    }

for i in os.scandir("/data/basecall_test"):
    if i.is_dir():
        sample_id = i.name
        for j in os.scandir(i.path):
            m = re.match(r"^(2024[0-9]{4})_([0-9]{4})_.+_$", j.name)
            if m:
                date = m.group(1)
                time = m.group(2)
                print("mkdir -vp /data/basecall_test/%s/kcl/%s/%s" % (sample_id, exp_data[sample_id]["hostname"], exp_data[sample_id]["flow_cell_id"]))
                print("mv -vn %s /data/basecall_test/%s/kcl/%s/%s/%s_%s_%s_%s_%s" % (j.path, sample_id, exp_data[sample_id]["hostname"], exp_data[sample_id]["flow_cell_id"], date, time, exp_data[sample_id]["device_id"], exp_data[sample_id]["flow_cell_id"], suffix))
