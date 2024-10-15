#!/usr/bin/python3

import os
import re
import socket

sheets_dir = "/data/sample_sheets"
data_dir = "/data/nihr_kcl_22k"
hostname = socket.gethostname()

for entry in os.scandir(sheets_dir):
    if not re.match(r"^(Promethion|sample-sheet-csv).+\.csv$", entry.name):
        continue

    output_file = "%s/OUTPUT_%s" % (sheets_dir, entry.name)

    if os.path.exists(output_file):
        continue

    date = os.stat(entry.path).st_mtime
    data = []

    with open(entry.path, "r") as f:
        lines = f.readlines()

    columns = lines[0].strip().split(",")

    for line in lines[1:]:
        data.append(dict(zip(columns, line.strip().split(","))))

    matched = 0

    for row in data:
        sample_dir = "%s/%s/kcl/%s" % (data_dir, row["sample_id"], hostname)
        flow_cell_ids = []
        if os.path.isdir(sample_dir):
            for flow_cell_id in os.scandir(sample_dir):
                if re.match(r"^[A-Z0-9]{8}$", flow_cell_id.name) and flow_cell_id.is_dir() and abs(os.stat(flow_cell_id.path).st_mtime - date) < 2419200:
                    flow_cell_ids.append(flow_cell_id.name)

        if len(flow_cell_ids) == 1:
            row["flow_cell_id"] = flow_cell_ids[0]
            matched += 1

    with open(output_file, "w") as f:
        f.write(",".join(columns) + "\n")
        for row in data:
            f.write(",".join([row[col] for col in columns]) + "\n")
