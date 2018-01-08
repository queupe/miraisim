#!/usr/bin/env python3

import argparse
import heapq
import json
import logging
import random
import resource
import sys

import bots
import hosts

import sim


DIST_EXPONENTIAL = 'Exponential'
DIST_UNIFORM = 'Uniform'


def create_parser(): # {{{
    desc = '''Botnet simulator'''

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--config-json',
            dest='configfn',
            action='store',
            metavar='FILE',
            type=str,
            required=True,
            help='JSON file containing simulation configuration')

    return parser
# }}}


def parse_dist(distcfg, name):# {{{
    logging.debug('  %s: %s', name, json.dumps(distcfg))
    if distcfg['dist'] == DIST_EXPONENTIAL:
        assert len(distcfg['params']) == 1
        fn = lambda: random.expovariate(1/float(distcfg['params'][0]))
    elif distcfg['dist'] == DIST_UNIFORM:
        assert len(distcfg['params']) == 2
        lower, upper = distcfg['params']
        fn = lambda: random.uniform(float(lower), float(upper))
    else:
        logging.fatal('error passing distribution %s', json.dumps(distcfg))
        raise ValueError('error parsing distribution %s' % json.dumps(distcfg))
    average = sum(fn() for _ in range(1000))/1000.0
    logging.debug('    1000 samples with average %f', average)
    return fn
# }}}


def main():#{{{
    resource.setrlimit(resource.RLIMIT_AS, (1 << 31, 1 << 31))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 35, 1 << 35))

    parser = create_parser()
    opts = parser.parse_args()
    with open(opts.configfn, 'r') as fd:
        sim.config = json.load(fd)

    logfile = sim.config.get('logfile', 'log.txt')
    logging.basicConfig(filename=logfile, format='%(message)s',
                        level=logging.NOTSET)
    logging.info('%s', json.dumps(sim.config))

    logging.info('initializing distributions:')
    sim.dist_host_on_time = parse_dist(sim.config['dists']['host_on_time'], 'on-time')
    sim.dist_host_off_time = parse_dist(sim.config['dists']['host_off_time'], 'off-time')

    sim.host_tracker = hosts.HostTracker(sim.config)
    logging.info('%s', sim.host_tracker)

    sim.e2e_latency = hosts.E2ELatency(sim.config)
    logging.info('%s', sim.e2e_latency)

    sim.botcache_factory = botcache.create_factory(sim.config)
    logging.info('%s', repr(sim.botcache_factory))

    if not bots.parse_scan_strat(sim.config):
        logging.fatal('Could not parse bot scanning strategy')
        logging.fatal('scan_strat %s', sim.config['scan_strat'])
        sys.exit(1)
    logging.info('Bot scanning strategy: %s', sim.config['scan_strat'])

    for hid in range(sim.hosttracker.vulnerable_period,
                     sim.config['maxhid'] + 1,
                     sim.hosttracker.vulnerable_period):
        off_time = sim.dist_host_off_time()
        ev = (sim.now + off_time, hosts.Host.bootup, hid)
        sim.enqueue(ev)
    logging.info('Created %d bootup events', len(sim.evqueue))
    assert len(sim.evqueue) == sim.config['maxhid']//sim.hosttracker.vulnerable_period

    logging.info('Initializing master bot')
    master = hosts.Host(0, hosts.STATUS_VULNERABLE)
    master.infect()
    sim.hosttracker.add(master)

    while sim.evqueue and sim.now < sim.config['endtime']:
        now, fn, data = sim.dequeue()
        logging.debug('%.6f dequeue len %d', sim.now, len(sim.evqueue))
        fn(data)
#}}}


if __name__ == '__main__':
    sys.exit(main())
