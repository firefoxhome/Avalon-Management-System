# -*- coding: utf-8; -*-
#
# Copyright (C) 2014-2015  DING Changchang
#
# This file is part of Avalon Management System (AMS).
#
# AMS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AMS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AMS. If not, see <http://www.gnu.org/licenses/>.

import socket
import json
import logging


class Miner():
    name = 'Miner'

    def __init__(self, ip, port, module_list):
        self.ip = ip
        self.port = port
        self.module_list = module_list
        self.log = logging.getLogger('AMS.Miner')

    def __str__(self):
        ip = '({})'.format(self.ip) if ':' in self.ip else self.ip
        return '[{}:{}]'.format(ip, self.port)

    def _collect(self, retry):
        if not self._ping(retry):
            for command in ['summary', 'edevs', 'estats', 'pools']:
                self.raw[command] = None
            return False

        for command in ['summary', 'edevs', 'estats', 'pools']:
            for r in range(1, retry + 1):
                try:
                    response = self.put(command, timeout=r/2)
                    if not response:
                        continue
                    else:
                        break
                except socket.error:
                    response = None
                    if r == retry:
                        self.log.error('{} Failed fetching {}. Giving up.'
                                       .format(self, command))
                    else:
                        self.log.debug('{} Failed fetching {}. Retry {}'
                                       .format(self, command, r))
            self.raw[command] = response
        return True

    def _ping(self, retry):
        for r in range(1, retry + 1):
            for res in socket.getaddrinfo(
                    self.ip, 80,
                    socket.AF_UNSPEC,
                    socket.SOCK_STREAM):

                af, socktype, proto, canonname, sa = res
                try:
                    s = socket.socket(af, socktype, proto)
                except socket.error:
                    self.log.debug(
                        '{} Error in ping test: socket init. '
                        'Retry: {}.'.format(self, r)
                    )
                    s = None
                    continue
                s.settimeout(r/2)
                try:
                    s.connect(sa)
                except socket.error:
                    self.log.debug(
                        '{} Error in ping test: socket connect. '
                        'Retry: {}.'.format(self, r)
                    )
                    s.close()
                    s = None
                    continue
                break
            if s is None:
                continue
            else:
                s.close()
                return True
        self.log.error('{} Error in ping test: connection failed.'.format(self))
        return False

    def _generate_sql_summary(self, run_time):
        pass

    def _generate_sql_edevs(self, run_time):
        pass

    def _generate_sql_estats(self, run_time):
        pass

    def _generate_sql_pools(self, run_time):
        pass

    def run(self, run_time, sql_queue, retry):
        self.raw = {}
        self.sql_queue = sql_queue
        self._collect(retry)
        self._generate_sql_summary(run_time)
        self._generate_sql_edevs(run_time)
        self._generate_sql_estats(run_time)
        self._generate_sql_pools(run_time)

    def put(self, command, parameter=None, timeout=3):
        if parameter is None:
            request = '{{"command": "{}"}}'.format(command)
        else:
            request = '{{"command": "{}", "parameter": "{}"}}'.format(
                command, parameter)

        for res in socket.getaddrinfo(
                self.ip,
                self.port,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM):

            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
            except socket.error:
                self.log.debug('{} Error in fetching {}: socket init.'
                               .format(self, command))
                s = None
                continue
            s.settimeout(timeout)
            try:
                s.connect(sa)
            except socket.error:
                self.log.debug('{} Error in fetching {}: socket connect.'
                               .format(self, command))
                s.close()
                s = None
                continue
            break
        if s is None:
            raise socket.error
        s.sendall(request.encode())
        response = s.recv(32768)
        while True:
            recv = s.recv(32768)
            if not recv:
                break
            else:
                response += recv
        response = ''.join(
            [x if ord(x) >= 32 else '' for x in response.decode()]
        )
        try:
            obj = json.loads(response)
            return obj
        except Exception as e:
            self.log.error('{} Error decoding json: {}'.format(self, e))
            self.log.debug('{} Error decoding json: {}'.format(self, response))
            return False


def db_init(sql_queue, temp=False):
    column_summary = [
        {'name': 'time',
         'type': 'TIMESTAMP DEFAULT 0'},
        {'name': 'ip',
         'type': 'VARCHAR(40)'},
        {'name': 'port',
         'type': 'SMALLINT UNSIGNED'},
        {'name': 'precise_time',
         'type': 'TIMESTAMP DEFAULT 0'},
        {'name': 'elapsed',
         'type': 'BIGINT'},
        {'name': 'mhs_av',
         'type': 'DOUBLE'},
        {'name': 'mhs_5s',
         'type': 'DOUBLE'},
        {'name': 'mhs_1m',
         'type': 'DOUBLE'},
        {'name': 'mhs_5m',
         'type': 'DOUBLE'},
        {'name': 'mhs_15m',
         'type': 'DOUBLE'},
        {'name': 'mhs',
         'type': 'DOUBLE'},
        {'name': 'found_blocks',
         'type': 'INT UNSIGNED'},
        {'name': 'getworks',
         'type': 'BIGINT'},
        {'name': 'accepted',
         'type': 'BIGINT'},
        {'name': 'rejected',
         'type': 'BIGINT'},
        {'name': 'hardware_errors',
         'type': 'INT'},
        {'name': 'utility',
         'type': 'DOUBLE'},
        {'name': 'discarded',
         'type': 'BIGINT'},
        {'name': 'stale',
         'type': 'BIGINT'},
        {'name': 'get_failures',
         'type': 'INT UNSIGNED'},
        {'name': 'local_work',
         'type': 'INT UNSIGNED'},
        {'name': 'remote_failures',
         'type': 'INT UNSIGNED'},
        {'name': 'network_blocks',
         'type': 'INT UNSIGNED'},
        {'name': 'total_mh',
         'type': 'DOUBLE'},
        {'name': 'work_utility',
         'type': 'DOUBLE'},
        {'name': 'difficulty_accepted',
         'type': 'DOUBLE'},
        {'name': 'difficulty_rejected',
         'type': 'DOUBLE'},
        {'name': 'difficulty_stale',
         'type': 'DOUBLE'},
        {'name': 'best_share',
         'type': 'BIGINT UNSIGNED'},
        {'name': 'device_hardware',
         'type': 'DOUBLE'},
        {'name': 'device_rejected',
         'type': 'DOUBLE'},
        {'name': 'pool_rejected',
         'type': 'DOUBLE'},
        {'name': 'pool_stale',
         'type': 'DOUBLE'},
        {'name': 'last_getwork',
         'type': 'TIMESTAMP DEFAULT 0'}
    ]
    column_pools = [
        {'name': 'time',
         'type': 'TIMESTAMP DEFAULT 0'},
        {'name': 'ip',
         'type': 'VARCHAR(40)'},
        {'name': 'port',
         'type': 'SMALLINT UNSIGNED'},
        {'name': 'precise_time',
         'type': 'TIMESTAMP DEFAULT 0'},
        {'name': 'pool_id',
         'type': 'TINYINT UNSIGNED'},
        {'name': 'pool',
         'type': 'INT'},
        {'name': 'url',
         'type': 'VARCHAR(64)'},
        {'name': 'status',
         'type': 'CHAR(1)'},
        {'name': 'priority',
         'type': 'INT'},
        {'name': 'quota',
         'type': 'INT'},
        {'name': 'long_poll',
         'type': 'CHAR(1)'},
        {'name': 'getworks',
         'type': 'INT UNSIGNED'},
        {'name': 'accepted',
         'type': 'BIGINT'},
        {'name': 'rejected',
         'type': 'BIGINT'},
        {'name': 'works',
         'type': 'INT'},
        {'name': 'discarded',
         'type': 'INT UNSIGNED'},
        {'name': 'stale',
         'type': 'INT UNSIGNED'},
        {'name': 'get_failures',
         'type': 'INT UNSIGNED'},
        {'name': 'remote_failures',
         'type': 'INT UNSIGNED'},
        {'name': 'user',
         'type': 'VARCHAR(32)'},
        {'name': 'last_share_time',
         'type': 'TIMESTAMP DEFAULT 0'},
        {'name': 'diff1_shares',
         'type': 'BIGINT'},
        {'name': 'proxy_type',
         'type': 'VARCHAR(32)'},
        {'name': 'proxy',
         'type': 'VARCHAR(64)'},
        {'name': 'difficulty_accepted',
         'type': 'DOUBLE'},
        {'name': 'difficulty_rejected',
         'type': 'DOUBLE'},
        {'name': 'difficulty_stale',
         'type': 'DOUBLE'},
        {'name': 'last_share_difficulty',
         'type': 'DOUBLE'},
        {'name': 'has_stratum',
         'type': 'BOOL'},
        {'name': 'stratum_active',
         'type': 'BOOL'},
        {'name': 'stratum_url',
         'type': 'BIGINT'},
        {'name': 'has_gbt',
         'type': 'BOOL'},
        {'name': 'best_share',
         'type': 'BIGINT UNSIGNED'},
        {'name': 'pool_rejected',
         'type': 'DOUBLE'},
        {'name': 'pool_stale',
         'type': 'DOUBLE'}
    ]
    if temp:
        name = ['miner_temp', 'pool_temp']
    else:
        sql_queue.put({
            'command': 'create',
            'name': 'hashrate',
            'column_def': [{'name': 'time', 'type': 'TIMESTAMP DEFAULT 0'}],
            'additional': 'PRIMARY KEY (`time`)',
        })
        name = ['miner', 'pool']
    sql_queue.put({
        'command': 'create',
        'name': name[0],
        'column_def': column_summary,
        'additional': 'PRIMARY KEY(`time`, `ip`, `port`)',
    })
    sql_queue.put({
        'command': 'create',
        'name': name[1],
        'column_def': column_pools,
        'additional': 'PRIMARY KEY(`time`, `ip`, `port`, `pool_id`)',
    })
