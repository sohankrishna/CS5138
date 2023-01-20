#!/usr/bin/env python3
# coding: utf-8

import sys
from socket import inet_ntop, AF_INET, AF_INET6
from bcc import BPF, DEBUG_PREPROCESSOR
import ctypes as ct
from struct import pack

# Keep in sync with connect_evt in connect.bcc
class TcpEvt(ct.Structure):
    _fields_ = [
        ("pid", ct.c_ulong),
        ("ip_version", ct.c_ulonglong),
        ("saddr", ct.c_ulonglong * 2),
        ("comm", ct.c_char * 81),
    ]

def tcp_connect_event_printer(cpu, data, size):
    """
    This function is called every time that there is a new
    event retrieved through the kernel/userspace communication
    buffer (tcp_connect_event).

    cpu: ??
    data: The data structure (TcpEvt) generated by the kernel.
    size: The size of data.
    """
    event = ct.cast(data, ct.POINTER(TcpEvt)).contents

    # Decode address
    if event.ip_version == 4:
        saddr = inet_ntop(AF_INET, pack("=I", event.saddr[0]))
    elif event.ip_version == 6:
        saddr = inet_ntop(AF_INET6, event.saddr)
    else:
        print("Could not decode the address!")
        return

    comm = event.comm.decode("utf-8")
    print(f"{event.pid} {saddr} {comm}")

if __name__ == "__main__":
    # Build probe.
    b = BPF(src_file="connect.bcc")
    # Open the tcp_connect_event kernel/userspace communication
    # buffer. Tell Python to invoke tcp_connect_event_printer
    # for every event that comes from the kernel.
    b["tcp_connect_event"].open_perf_buffer(tcp_connect_event_printer)

    # Print a header to describe the output format.
    print(f"PID Address Path")

    # Now, let's roll.
    while True:
        b.perf_buffer_poll(1)
