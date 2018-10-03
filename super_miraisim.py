#!/usr/bin/env python3

import argparse
import json
import logging
import random
import resource
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

import bots
import hosts
import targeting
import sim

from graph_results import show_results

DIST_EXPONENTIAL = 'Exponential'
DIST_UNIFORM = 'Uniform'

ROUNDS = 10


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
    loglevel = getattr(logging, sim.config.get('loglevel', 'INFO'))
    logging.basicConfig(filename=logfile,
                        format='%(TIME)f %(filename)s:%(lineno)d/%(funcName)s %(message)s',
                        level=loglevel)
    logger = logging.getLogger()
    logger.addFilter(SimulationTimeFilter())
    logging.info('%s', json.dumps(sim.config))

    mean_list = list()
    vari_list = list()

    for round in range(1,ROUNDS+1):
        print('Round {0:>3d}'.format(round))

        logging.info('Starting round: {0:>2d}'.format(round))
        sim.dist_host_on_time = parse_dist(sim.config['dists']['host_on_time'],'on-time')
        sim.dist_host_off_time = parse_dist(sim.config['dists']['host_off_time'], 'off-time')
        logging.info('initialized on/off time distributions')

        sim.config['maxhid'] = sim.config['maxhid'] + (round-1)*2000

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
        i = len(sim.count_history)
        #off_hst = np.zeros((i,2))
        max = 0
        min = sim.config['maxhid']
        i = 0
        avg_local = 0
        avg_weight = 0
        hour_ant = 0

        for hist in sim.count_history:
            (qtd_heal, qtd, qtd_off, hour, hid, status, status_before) = hist
            i = i+1
            # Average
            if (hour > sim.config['endtime']/2):
                avg_local += qtd * (hour - hour_ant)
                avg_weight += hour - hour_ant
                if qtd < min :
                    min = qtd
                if qtd > max:
                    max = qtd

            hour_ant = hour

            #print(str(i) + "\t"+ str(qtd)+ "\t" + str(hour))

        avg_local = (float(avg_local)/(avg_weight))
        avg_weight = float(avg_weight) / len(sim.count_history)


        # Standard deviance compute
        dev_std = 0
        hour_ant = 0
        hour_tot = 0
        for hist in sim.count_history:
            (qtd_heal, qtd, qtd_off, hour, hid, status, status_before) = hist
            if (hour > sim.config['endtime']/2):
                hour_tot += hour - hour_ant
                dev_std += ((qtd - avg_local)**2)*(hour - hour_ant)

        var_local = np.sqrt(dev_std / hour_tot)

        #for hist in sim.count_heal

        print("Infect min: {0:>2.4f} \tmax   : {1:>2.4f}".format(float(min)/sim.config['maxhid'], float(max)/sim.config['maxhid']))
        print("Prob infec: {0:>2.4f} \tTotal : {1:>4d}".format(avg_local/sim.config['maxhid'], sim.config['maxhid']))
        print("Rate infec: {0:>2.4f} \theal  : {1:>2.4f}".format(avg_weight, avg_weight))
        print("Average   : {0:>2.4f} \tStd dv: {1:>4.2f}\n".format(avg_local, var_local))
        #infected_hst = np.array(sim.count_history)
        #off_hst = np.array(sim.count_off_history)
        #inf_hst = np.array(sim.count_history)
        #show_results(infected_hst[:,0],infected_hst[:,1])
        #plt.plot(inf_hst[:,1], inf_hst[:,0]/sim.config['maxhid'])
        #plt.plot(off_hst[:,1], off_hst[:,0]/sim.config['maxhid'])
        #plt.show()
        #plt.clf()

        sim.count_history = list()
        sim.count_off_history = list()
        sim.infected_hosts = 0
        sim.off_hosts = 0
        sim.now = 0
        sim.evqueue = list()
        sim.evseq = 0
# }}}


if __name__ == '__main__':
    start = time.time()
    results = main()
    end = time.time()
    print("Time elapsed: {0:>4.3f}".format(end - start))
    sys.exit(results)
