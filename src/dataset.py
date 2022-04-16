# coding=utf-8

import os
import sys
import glob
from tqdm import tqdm
import pickle

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
TOTAL_PACKET = 256


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


def make_packets(packets, filename):
    basename = os.path.basename(filename)

    vpn, type, app = TYPES[basename]

    idx = 0
    for packet in tqdm(PcapReader(filename)):
        if idx > TOTAL_PACKET:
            return

        if omit_packet(packet):
            continue

        idx += 1
        if Ether in packet:
            content = bytes(packet.payload)
        else:
            content = bytes(packet)

        content = content[:1024]
        packets.append((vpn, type, app, content))


def main():
    packets = []
    pattern = os.path.join(dirname, 'data/*/', '*.pcap*')
    files = glob.glob(pattern)
    for filename in files:
        make_packets(packets, filename)

    with open(packets_filename, 'wb') as file:
        file.write(pickle.dumps(packets))


if __name__ == '__main__':
    main()
