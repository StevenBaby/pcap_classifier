# coding=utf-8

import os
import sys
import glob
import pickle
import concurrent.futures

from scapy.all import PcapReader
from scapy.all import Ether, IP, TCP, UDP, DNS, Padding
import numpy as np
import matplotlib.pyplot as plt
from logger import logger
from classify import *  # noqa

plt.set_loglevel("info")

dirname = os.path.dirname(__file__)
packets_filename = os.path.join(dirname, 'data/packets.pickle')


# 每个文件最大处理包数量
TOTAL_PACKET = 128
MTU_LENGTH = 1024


# 是否需要忽略改包
def omit_packet(packet):
    # SYN, ACK or FIN flags set to 1 and no payload
    if TCP in packet and (packet.flags & 0x13):
        # not payload or contains only padding
        layers = packet[TCP].payload.layers()
        if not layers or (Padding in layers and len(layers) == 1):
            return True

    # DNS segment
    if DNS in packet:
        return True

    return False


def make_packets(filename):
    packets = []

    basename = os.path.basename(filename)

    vpn, ty, app = TYPES[basename]

    idx = 0
    for packet in PcapReader(filename):
        if idx > TOTAL_PACKET:
            break

        if omit_packet(packet):
            continue

        idx += 1
        if Ether in packet:
            content = bytes(packet.payload)
        else:
            content = bytes(packet)

        if len(content) > MTU_LENGTH:
            # logger.warning("content length %d > mtu length %d", len(content), MTU_LENGTH)
            pass

        content = content[:MTU_LENGTH]
        packets.append((vpn, ty, app, content))

    logger.debug("finish %s", basename)

    return packets


def main():
    packets = []
    pattern = os.path.join(dirname, 'data/*/', '*.pcap*')
    files = glob.glob(pattern)

    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(make_packets, filename)
            for filename in files
        ]

        for future in concurrent.futures.as_completed(futures):
            packets.extend(future.result())

    with open(packets_filename, 'wb') as file:
        file.write(pickle.dumps(packets))


if __name__ == '__main__':
    main()
