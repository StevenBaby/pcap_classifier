# coding=utf-8

import os
import sys
import glob
import sqlite3
from tqdm import tqdm
import json

from scapy.all import PcapReader
import numpy as np
import matplotlib.pyplot as plt
from logger import logger
from classify import *  # noqa

plt.set_loglevel("info")

dirname = os.path.dirname(__file__)
train_database = os.path.join(dirname, 'data/train_packets.db')
test_database = os.path.join(dirname, 'data/test_packets.db')

# 每个文件最大处理包数量
TRAIN_PACKET = 128
TEST_PACKET = 128

CREATE_TABLES = [
    '''
    CREATE TABLE IF NOT EXISTS "packets" (
        "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "index" integer NOT NULL,
        "vpn" integer NOT NULL,
        "type" integer NOT NULL,
        "app" integer NOT NULL,
        "content" blob(1024) NOT NULL
    );'''
]


def make_packets(train_cur, test_cur, filename):
    basename = os.path.basename(filename)

    vpn, type, app = TYPES[basename]

    SQL = '''INSERT INTO
        "packets"("index", "vpn", "type", "app", "content")
        VALUES (?, ?, ?, ?, ?)'''

    for idx, packet in tqdm(enumerate(PcapReader(filename))):
        if idx < TRAIN_PACKET:
            cur = train_cur
        elif (idx - TRAIN_PACKET) < TEST_PACKET:
            cur = test_cur
        else:
            return

        content = bytes(packet.payload)
        content = content[:1024]
        cur.execute(SQL, (idx, vpn, type, app, content))


def main():
    pattern = os.path.join(dirname, 'data/*/', '*.pcap*')

    with sqlite3.connect(train_database) as train_db, sqlite3.connect(test_database) as test_db:
        train_cur = train_db.cursor()
        test_cur = test_db.cursor()

        for sql in CREATE_TABLES:
            train_cur.execute(sql)
            test_cur.execute(sql)
        pattern = os.path.join(dirname, 'data/*/', '*.pcap*')
        files = glob.glob(pattern)
        for filename in files:
            make_packets(train_cur, test_cur, filename)

        train_db.commit()
        test_db.commit()


if __name__ == '__main__':
    main()
