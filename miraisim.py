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

from datetime import datetime
from graph_results import show_results

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
    loglevel = getattr(logging, sim.config.get('loglevel', 'INFO'))
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


    #i = len(sim.count_history)
    h_max = 0
    i_max = 0
    o_max = 0

    h_min = sim.config['maxhid']
    i_min = sim.config['maxhid']
    o_min = sim.config['maxhid']

    #i = 0
    #avg_1 = 0
    #avg_total = 0
    #hour_ant = 0
    i = 0
    h_i = 0
    i_i = 0
    o_i = 0

    avg_heal  = 0
    avg_infec = 0
    avg_off   = 0

    time_heal  = 0
    time_infec = 0
    time_off   = 0

    time_b_heal  = 0
    time_b_infec = 0
    time_b_off   = 0

    h_lst = list()
    i_lst = list()
    o_lst = list()

    for hist in sim.count_history:
        (qtd_heal, qtd_inf, qtd_off, hour, hid, status, status_before) = hist
        i += 1

        if (hour > sim.config['endtime']/2):
            #avg_1 += qtd * (hour - hour_ant)
            #avg_total += hour - hour_ant

            if qtd_heal < h_min :
                h_min = qtd_heal
            if qtd_heal > h_max:
                h_max = qtd_heal
            if qtd_inf < i_min :
                i_min = qtd_inf
            if qtd_inf > i_max:
                i_max = qtd_inf
            if qtd_off < o_min :
                o_min = qtd_off
            if qtd_off > o_max:
                o_max = qtd_off

            str_status = ''
            # Average
            if (status == sim._SUSCETIBLE_):
                h_i += 1
                str_status = 'susceptible'
                time_b_heal   = hour
                avg_off  += qtd_off * (hour - time_b_off)
                time_off  += hour - time_b_off
                h_lst.append((hour,qtd_heal, qtd_inf, qtd_off))

            elif (status == sim._INFECTED_):
                i_i +1
                str_status = 'infected'
                time_b_infec = hour
                avg_heal  += qtd_heal * (hour - time_b_heal)
                time_heal  += hour - time_b_heal
                i_lst.append((hour,qtd_heal, qtd_inf, qtd_off))

            elif (status == sim._SHUTDOWN_):
                o_i += 1
                str_status = 'off'
                time_b_off   = hour
                if status_before == sim._INFECTED_:
                    avg_infec  += qtd_inf * (hour - time_b_infec)
                    time_infec += hour - time_b_infec
                else:
                    avg_heal  += qtd_heal * (hour - time_b_heal)
                    time_heal  += hour - time_b_heal
                o_lst.append((hour,qtd_heal, qtd_inf, qtd_off))


            str_evt = "Evt[{0:>3d}]".format(i)
            str_qtd = "H:{0:>3d}[{1:>2.2f}%]\tI:{2:>3d}[{3:>2.2f}%]\tO:{4:>3d}[{5:>2.2f}%]\tT:{6:>3d}".format(qtd_heal, float(qtd_heal*100)/(sim.config['maxhid']+1) ,
                                                                                                              qtd_inf , float(qtd_inf*100) /(sim.config['maxhid']+1) ,
                                                                                                              qtd_off , float(qtd_off*100) /(sim.config['maxhid']+1) ,
                                                                                                              qtd_heal+qtd_inf+qtd_off )
            str_tim = "time:{0:>4.3f}".format(hour)
            str_hid = "ID:{0:>4d}".format(hid)
            print("{}\t{}\t{}\t{}\t{}".format(str_evt, str_tim, str_qtd, str_hid, str_status))

        #hour_ant = hour
        else:
            if (status == sim._SUSCETIBLE_):
                h_lst.append((hour,qtd_heal, qtd_inf, qtd_off))
            elif(status == sim._INFECTED_):
                i_lst.append((hour,qtd_heal, qtd_inf, qtd_off))
            elif(status == sim._SHUTDOWN_):
                o_lst.append((hour,qtd_heal, qtd_inf, qtd_off))


        #print(str(i) + "\t"+ str(qtd)+ "\t" + str(hour))
        #print("Evt[{0:>3d}] \ttime:{1:>4.3f} \tinfected:{2:>4d}[{3:>2.2f}%]".format(i,hour,qtd,float(qtd*100)/(sim.config['maxhid']+1)))

    # Average conclude
    #avg_all   = (avg_heal + avg_infec + avg_off) / (time_heal + time_infec + time_off)
    avg_heal  = avg_heal  / time_heal
    avg_infec = avg_infec / time_infec
    avg_off   = avg_off   / time_off
    avg_all   = avg_heal + avg_infec + avg_off

    # Status time evolution
    h_prob = avg_heal  / sim.config['maxhid']
    i_prob = avg_infec / sim.config['maxhid']
    o_prob = avg_off   / sim.config['maxhid']
    a_prob = avg_all   / sim.config['maxhid']

    h_hst = np.array(h_lst)
    i_hst = np.array(i_lst)
    o_hst = np.array(o_lst)
    all_hst = np.array(sim.count_history)

    # Show the informations
    # standard output
    print("\n\tmin \tmax \taverage \tprobability")
    print("heal:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format(h_min, h_max, avg_heal, h_prob))
    print("infec:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format(i_min, i_max, avg_infec, i_prob))
    print("off:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format(o_min, o_max, avg_off, o_prob))
    print("Total:\t- \t- \t{:8.4f}  \t{:>1.4f}".format(avg_all, a_prob))

    # Plotting
    plt.plot(h_hst[:,0], h_hst[:,1]/sim.config['maxhid'], label='susceptible', color='b')
    plt.plot(i_hst[:,0], i_hst[:,2]/sim.config['maxhid'], label='infected'   , color='r')
    plt.plot(o_hst[:,0], o_hst[:,3]/sim.config['maxhid'], label='off'        , color='g')
    plt.plot(all_hst[:,3], (all_hst[:,0]+all_hst[:,1]+all_hst[:,2])/sim.config['maxhid'], label='total', color='y')
    plt.xlabel('time')
    plt.ylabel('proportion of')
    plt.ylim((0.0,1.5))
    plt.legend(loc='upper right')
    plt.show()
# }}}


if __name__ == '__main__':
    #start = time.time()
    start_time = datetime.now()
    results = main()
    #end = time.time()
    time_elapsed = datetime.now() - start_time
    print("Time elapsed: {0}".format(time_elapsed))
    sys.exit(results)
