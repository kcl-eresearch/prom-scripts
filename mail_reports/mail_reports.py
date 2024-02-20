#!/usr/bin/python3
# Find sequencing reports and email them
# Xand Meaden, King's College London

import datetime
import json
import os
import platform
import re
import smtplib
import ssl
import sys
import yaml
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    with open("/etc/ont_mail_reports.yaml") as fh:
        config = yaml.safe_load(fh)
except Exception as e:
    sys.exit("Failed to load config: %s" % e)

try:
    with open("/etc/prom_id") as fh:
        prom_id = fh.read().strip()
except Exception as e:
    sys.exit("Failed to load prom_id: %s" % e)

hostname = platform.node()

now = datetime.datetime.now()
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
max_size = config["max_size"] * 1000000

to_mail = []
for item in os.scandir(config["reports_dir"]):
    if re.match(r"^report_[^\s]+\.html$", item.name):
        if not os.path.exists("%s.mailed.yaml" % item.path):
            to_mail.append(item.path)

if len(to_mail) == 0:
    sys.exit(0)

header_from = "<%s>" % config["mail_from"]
header_to = ""
for address in config["mail_to"]:
    header_to += "<%s>, " % address
header_to = header_to.rstrip(", ")

segments = [{}]
mailed = []

segment = 0
segment_size = 0

for item in to_mail:
    try:
        with open(item, "rb") as fh:
            part = MIMEBase("text", "html")
            part.set_payload(fh.read())
    except Exception as e:
        sys.stderr.write("Failed to load %s: %s\n" % (item, e))
        continue

    encoders.encode_base64(part)
    filename = os.path.basename(item)
    part.add_header(
        "Content-Disposition",
        "attachment; filename=%s" % filename
    )

    part_size = len(part.as_string())
    if segment_size + part_size >= max_size:
        segment += 1
        segments.append({})
        segment_size = part_size
    else:
        segment_size += part_size

    segments[segment][filename] = part

segment_count = len(segments)
for i in range(segment_count):
    message = MIMEMultipart()
    message["From"] = header_from
    message["To"] = header_to
    message["Subject"] = "Sequencing reports from %s (%s) at %s [%d of %d]" % (prom_id, hostname, timestamp, i + 1, segment_count)
    body = "Attached are %d reports from %s (%s). This is email number %d of %d sent at %s.\n" % (len(segments[i]), prom_id, hostname, i + 1, segment_count, timestamp)
    body += "\n- ".join([""] + list(segments[i].keys()))
    message.attach(MIMEText(body, "plain"))

    for filename, part in segments[i].items():
        message.attach(part)

    message_text = message.as_string()

    try:
        smtp = smtplib.SMTP(config["mail_host"], config["mail_port"])
        smtp.starttls(context=ssl.create_default_context())
        if "mail_user" in config:
            smtp.login(config["mail_user"], config["mail_password"])
        smtp.sendmail(config["mail_from"], config["mail_to"], message_text)
        smtp.quit()
    except Exception as e:
        sys.stderr.write("Failed sending message %d: %s\n" % (i + 1, e))
        continue

    mailed.extend(list(segments[i].keys()))

for item in mailed:
    mailed_file = "%s/%s.mailed.yaml" % (config["reports_dir"], item)
    try:
        with open(mailed_file, "w") as fh:
            yaml.dump(
                {
                    "timestamp": timestamp,
                    "recipients": config["mail_to"],
                },
                fh, default_flow_style=False
            )
    except Exception as e:
        sys.stderr.write("Failed writing %s: %s\n" % (mailed_file, e))
