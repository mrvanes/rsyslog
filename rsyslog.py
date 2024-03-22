#!/usr/bin/env python
import ssl
from datetime import datetime, timedelta, timezone

# https://github.com/aboehm/pysyslogclient
import pysyslogclient   # pip install syslog-py

# https://github.com/systemd/python-systemd
from systemd import journal     # pip install systemd-python
                                # Requires libsystemd-dev to compile
                                # or install python3-systemd


SERVER = 'rsyslog'
PORT = 6514

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
# context.verify_mode = ssl.CERT_REQUIRED


def sclient(SERVER, PORT):
    client = pysyslogclient.SyslogClientRFC5424(SERVER, PORT, proto="TCP")
    r = client.connect()
    client.socket = context.wrap_socket(client.socket, server_hostname=client.server)

    print(f"r: {r}")
    print(f"socket: {client.socket}")
    print(f"veresion: {client.socket.version()}")
    return client


def rsyslog(client, entry):
    if not entry.get('_PID'):
        return
    # print(f"{entry}")
    print(f"{entry['MESSAGE']}")
    client.log(entry['MESSAGE'],
               # timestamp=entry['__REALTIME_TIMESTAMP'],
               facility=entry['SYSLOG_FACILITY'],
               severity=entry['PRIORITY'],
               program=entry['SYSLOG_IDENTIFIER'],
               # hostname=entry['_HOSTNAME'],
               pid=entry['_PID']
               )


client = sclient(SERVER, PORT)
# exit(0)

# Send single entry
entry = {
    'MESSAGE': "Hello syslog server",
    'SYSLOG_FACILITY': pysyslogclient.FAC_SYSTEM,
    'PRIORITY': pysyslogclient.SEV_EMERGENCY,
    'SYSLOG_IDENTIFIER': "Logger",
    '_HOSTNAME': "minivanes.l",
    '__REALTIME_TIMESTAMP': datetime(2024, 3, 22, 13, 3, 19, 864606, tzinfo=timezone(timedelta(seconds=3600), 'CET')),
    '_PID': 1234
}

# rsyslog(client, entry)
# exit(0)

# Log last minute
j = journal.Reader(path='/var/log/journal/5074a19ba5674941bc51befbc15f2ec9')
j.seek_realtime(datetime.now() - timedelta(minutes=1))
for entry in j:
    rsyslog(client, entry)

# Tail journal
j.seek_tail()
while True:
    r = j.wait(timeout=5)  # Blocing until timeout or indefinately for 0 (default)
    if r == journal.NOP:
        print("NOP")
    elif r == journal.INVALIDATE:
        print("INVALIDATE")
    elif r == journal.APPEND:
        print("APPEND")
        for entry in j:
            rsyslog(client, entry)

j.close()
client.close()
