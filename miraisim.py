#!/usr/bin/env python3

import argparse
import json
import logging
import random
import resource
import sys

import bots
import hosts
import targeting

import sim


DIST_EXPONENTIAL = 'Exponential'
DIST_UNIFORM = 'Uniform'


def create_parser():  # {{{
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


def parse_dist(distcfg, name):  # {{{
    logging.info('%s: %s', name, json.dumps(distcfg))
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


class SimulationTimeFilter(logging.Filter):  # {{{
    def filter(self, record):
        record.TIME = sim.now
        return True
# }}}


def main():  # {{{
    resource.setrlimit(resource.RLIMIT_AS, (1 << 32, 1 << 32))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 35, 1 << 35))

    parser = create_parser()
    opts = parser.parse_args()
    with open(opts.configfn, 'r') as fd:
        sim.config = json.load(fd)

    logfile = sim.config.get('logfile', 'log.txt')
    loglevel = getattr(logging, sim.config.get('loglevel', 'DEBUG'))
    logging.basicConfig(filename=logfile,
                        format='%(TIME)f %(filename)s:%(lineno)d/%(funcName)s %(message)s',
                        level=loglevel)
    logger = logging.getLogger()
    logger.addFilter(SimulationTimeFilter())
    logging.info('%s', json.dumps(sim.config))

    sim.dist_host_on_time = parse_dist(sim.config['dists']['host_on_time'],
                                       'on-time')
    sim.dist_host_off_time = parse_dist(sim.config['dists']['host_off_time'],
                                        'off-time')
    logging.info('initialized on/off time distributions')

    sim.targeting_factory = targeting.create_factory(sim.config)
    logging.info('%s', sim.targeting_factory)

    sim.bot_factory = bots.create_factory(sim.config)
    logging.info('%s', sim.bot_factory)

    sim.host_tracker = hosts.HostTracker(sim.config)
    logging.info('%s', sim.host_tracker)

    sim.e2e_latency = hosts.E2ELatency(sim.config)
    logging.info('%s', sim.e2e_latency)

    master = hosts.Host(0, hosts.STATUS_VULNERABLE)
    master.on_time = 1e100
    master.infect()
    sim.host_tracker.add(master)
    logging.info('initialized master bot')

    for hid in range(sim.host_tracker.vulnerable_period,
                     sim.config['maxhid'] + 1,
                     sim.host_tracker.vulnerable_period):
        off_time = sim.dist_host_off_time()
        ev = (sim.now + off_time, hosts.Host.bootup, hid)
        sim.enqueue(ev)
    logging.info('created %d bootup events', len(sim.evqueue))

    assert (len(sim.evqueue) ==
            (sim.config['maxhid'] // sim.host_tracker.vulnerable_period) + 1)

    while sim.evqueue and sim.now < sim.config['endtime']:
        _now, fn, data = sim.dequeue()
        logging.debug('dequeue len %d', len(sim.evqueue))
        fn(data)
# }}}


if __name__ == '__main__':
    sys.exit(main())
