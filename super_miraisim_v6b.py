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
import atexit
import os
from shutil import copy

import bots
import hosts
import targeting
import sim

from os import path
from datetime import datetime
from graph_results import show_results

DIST_EXPONENTIAL = 'Exponential'
DIST_UNIFORM = 'Uniform'
DIST_CONSTANT = 'Constant'


# Directorys importants
_GRAPH_      = 'graph/'
_WEB_LOCAL_  = 'web/'
_IMG_LOCAL_  = 'web/img/'
_WEB_REMOTE_ = '/home/vilc/GoogleDrive/followavoid/results/www/'
_IMG_REMOTE_ = '/home/vilc/GoogleDrive/followavoid/results/www/img/'


ROUNDS = 10
PARAMS = 1

PRINT_ROUND = True
PLOT_ROUND = True
PLOT_PARAM = True
WEB_ROUND = False
WEB_PARAM = False

my_dpi = 100
size_w = 600
size_h = 300

# COUNTER
def read_counter():
    return json.loads(open("counter.json", "r").read()) + 1 if path.exists("counter.json") else 0

def write_counter():
    with open("counter.json", "w") as f:
        f.write(json.dumps(counter))

counter = read_counter()
atexit.register(write_counter)

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
    #logging.info('%s: %s', name, json.dumps(distcfg))
    if distcfg['dist'] == DIST_EXPONENTIAL:
        assert len(distcfg['params']) == 1
        fn = lambda: random.expovariate(1/float(distcfg['params'][0]))
    elif distcfg['dist'] == DIST_UNIFORM:
        assert len(distcfg['params']) == 2
        lower, upper = distcfg['params']
        fn = lambda: random.uniform(float(lower), float(upper))
    elif distcfg['dist'] == DIST_CONSTANT:
        assert len(distcfg['params']) == 1
        fn = lambda: distcfg['params'][0]
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

def main():
    resource.setrlimit(resource.RLIMIT_AS, (1 << 32, 1 << 32))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 35, 1 << 35))

    parser = create_parser()
    opts = parser.parse_args()
    #with open(opts.configfn, 'r') as fd:
    #    sim.config = json.load(fd)

    end_values_vec = np.array([ 8, 20,  50,  500]) * 1e-5
    exo_values_vec = np.array([ 5, 32, 200, 2000]) * 1e-2
    up_time_vec    = np.array([18, 40,  65,  260])

    evt = 1000
    for end_values in end_values_vec:
        with open(opts.configfn, 'r') as fd:
            sim.config = json.load(fd)
        sim.config['bot']['params'][0] = end_values
        simulation(opts, evt)
        evt += 1

    evt = 2000
    for exo_values in exo_values_vec:
        with open(opts.configfn, 'r') as fd:
            sim.config = json.load(fd)
        sim.config['bot']['master'][0] = exo_values
        simulation(opts, evt)
        evt += 10

    evt = 3000
    for up_time in up_time_vec:
        with open(opts.configfn, 'r') as fd:
            sim.config = json.load(fd)
        sim.config['dists']['host_on_time']['params'][0] = up_time
        simulation(opts, evt)
        evt += 100


    return 0


def simulation(opts, evt):  # {{{

    logfile = sim.config.get('logfile', 'log.txt')
    loglevel = getattr(logging, sim.config.get('loglevel', 'INFO'))
    logging.basicConfig(filename=logfile,
                        format='%(TIME)f %(filename)s:%(lineno)d/%(funcName)s %(message)s',
                        level=loglevel)
    logger = logging.getLogger()
    logger.addFilter(SimulationTimeFilter())
    #logging.info('%s', json.dumps(sim.config))

    str_param  = ''
    elem_param = 0
    tam        = 0
    values     = [0]
    X_pos      = 0

    for param in range(PARAMS):
        #with open(opts.configfn, 'r') as fd:
        #    sim.config = json.load(fd)

        info_average_proportional = list()
        info_average_from_unitary = list()
        info_time_between_events  = list()

        h_p_lst = list()
        i_p_lst = list()
        o_p_lst = list()
        a_p_lst = list()

        for rnd in range(ROUNDS):

            # ==================================================================
            # ==================================================================
            # Config Setting
            # ==================================================================

            # change the parameters
            # Number of elements
            if param == 0:
                if rnd == 0:
                    value_std = sim.config['maxhid']
                    value_min = sim.config['min']['maxhid']
                    value_max = sim.config['max']['maxhid']
                    #print (value_std, value_max, value_min)
                    if value_min > 1:
                        value_min = 1.0/float(value_min)
                    if value_max < 1:
                        value_max = 1.0/float(value_max)

                    value_min *= value_std
                    value_max *= value_std
                    values_A = np.linspace(value_min,value_std,num=int(ROUNDS/2), dtype=int, endpoint=False)
                    values_B = np.linspace(value_std,value_max,num=(ROUNDS - int(ROUNDS/2)),dtype=int, endpoint=True)
                    values = np.concatenate((values_A,values_B))
                    #print (values, int(ROUNDS/2), (ROUNDS - int(ROUNDS/2)), value_std, value_max, value_min)
                    #return 1
                    #values[-1] = 50000
                    str_param =  'number of elements'
                    str_values = list()
                    for val in values:
                        str_values.append('{:d}'.format(val) )
                #sim.config['maxhid'] += rnd * tam
                sim.config['maxhid'] = values[rnd]
                elem_param = sim.config['maxhid']


            # Endogenous infection rate
            elif param == 1:
                if rnd == 0:
                    value_std = sim.config['bot']['params'][0]
                    value_min = sim.config['min']['bot']['params'][0]
                    value_max = sim.config['max']['bot']['params'][0]

                    if value_min > 1:
                        value_min = 1.0/float(value_min)
                    if value_max < 1:
                        value_max = 1.0/float(value_max)

                    value_min *= value_std
                    value_max *= value_std
                    values_A = np.logspace(np.log10(value_min),np.log10(value_std),num = int(ROUNDS/2), dtype=float, endpoint = False)
                    values_B = np.logspace(np.log10(value_std),np.log10(value_max),num = (ROUNDS - int(ROUNDS/2)), dtype=float, endpoint = True)
                    values = np.concatenate((values_A,values_B))
                    str_param = 'Endogenous infection rate'
                    str_values = list()
                    for val in values:
                        str_values.append('{:.3e}'.format(val) )
                sim.config['bot']['params'][0] = values[rnd]
                elem_param = sim.config['bot']['params'][0]

            # Exogenous infection rate
            elif param == 2:
                if rnd == 0:
                    value_std = sim.config['bot']['master'][0]
                    value_min = sim.config['min']['bot']['master'][0]
                    value_max = sim.config['max']['bot']['master'][0]

                    if value_min > 1:
                        value_min = 1.0/float(value_min)
                    if value_max < 1:
                        value_max = 1.0/float(value_max)

                    value_min *= value_std
                    value_max *= value_std
                    values_A = np.logspace(np.log10(value_min),np.log10(value_std),num = int(ROUNDS/2), dtype=float, endpoint = False)
                    values_B = np.logspace(np.log10(value_std),np.log10(value_max),num = (ROUNDS - int(ROUNDS/2)), dtype=float, endpoint = True)
                    values = np.concatenate((values_A,values_B))
                    str_param = 'Exogenous infection rate'
                    str_values = list()
                    for val in values:
                        str_values.append('{:.3e}'.format(val) )
                sim.config['bot']['master'][0] = values[rnd]
                elem_param = sim.config['bot']['master'][0]

            # Average host on time
            elif param == 3:
                if rnd == 0:
                    value_std = sim.config['dists']['host_on_time']['params'][0]
                    value_min = sim.config['min']['dists']['host_on_time']['params'][0]
                    value_max = sim.config['max']['dists']['host_on_time']['params'][0]

                    if value_min > 1:
                        value_min = 1.0/float(value_min)
                    if value_max < 1:
                        value_max = 1.0/float(value_max)

                    value_min *= value_std
                    value_max *= value_std
                    values_A = np.linspace(value_min,value_std,num=int(ROUNDS/2), dtype=int, endpoint=False)
                    values_B = np.linspace(value_std,value_max,num=(ROUNDS - int(ROUNDS/2)),dtype=int, endpoint=True)
                    values = np.concatenate((values_A,values_B))
                    #print (values, int(ROUNDS/2), (ROUNDS - int(ROUNDS/2)), value_std, value_max, value_min)
                    #return 1
                    str_param = 'Average host on time'
                    str_values = list()
                    for val in values:
                        str_values.append('{:.3e}'.format(val) )
                sim.config['dists']['host_on_time']['params'][0] = values[rnd]
                elem_param = sim.config['dists']['host_on_time']['params'][0]

            # Average host off time
            elif param == 4:
                if rnd == 0:
                    value_std = sim.config['dists']['host_off_time']['params'][0]
                    value_min = sim.config['min']['dists']['host_off_time']['params'][0]
                    value_max = sim.config['max']['dists']['host_off_time']['params'][0]

                    if value_min > 1:
                        value_min = 1.0/float(value_min)
                    if value_max < 1:
                        value_max = 1.0/float(value_max)

                    value_min *= value_std
                    value_max *= value_std
                    values_A = np.linspace(value_min,value_std,num=int(ROUNDS/2), dtype=int, endpoint=False)
                    values_B = np.linspace(value_std,value_max,num=(ROUNDS - int(ROUNDS/2)),dtype=int, endpoint=True)
                    values = np.concatenate((values_A,values_B))
                    str_param = 'Average host off time'
                    str_values = list()
                    for val in values:
                        str_values.append('{:.3e}'.format(val) )
                sim.config['dists']['host_off_time']['params'][0] = values[rnd]
                elem_param = sim.config['dists']['host_off_time']['params'][0]


            else:
                return -1


            # ==================================================================
            # ==================================================================
            # Simulation Setting
            # ==================================================================
            sim.dist_host_on_time  = parse_dist(sim.config['dists']['host_on_time'] , 'on-time')
            sim.dist_host_off_time = parse_dist(sim.config['dists']['host_off_time'], 'off-time')
            logging.info('initialized on/off time distributions')

            sim.targeting_factory = targeting.create_factory(sim.config)
            logging.info('%s', sim.targeting_factory)

            sim.bot_factory = bots.create_factory(sim.config)
            logging.info('%s', sim.bot_factory)

            sim.master_bot_factory = bots.master_create_factory(sim.config)
            logging.info('%s', sim.master_bot_factory)

            sim.host_tracker = hosts.HostTracker(sim.config)
            logging.info('%s', sim.host_tracker)

            sim.e2e_latency = hosts.E2ELatency(sim.config)
            logging.info('%s', sim.e2e_latency)

            master = hosts.Host(0, hosts.STATUS_VULNERABLE)
            master.on_time = 1e100
            master.master_infect(from_hid = 0)
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

            # ==================================================================
            # ==================================================================
            # Simulation Perform
            # ==================================================================
            while sim.evqueue and sim.now < sim.config['endtime']:
                _now, fn, data = sim.dequeue()
                logging.debug('dequeue len %d', len(sim.evqueue))
                fn(data)

            # ==================================================================
            # ==================================================================
            # Simulation Analisys
            # ==================================================================

            # h - susceptible or health and on
            # i - infected and on
            # n - infected by endogenous source
            # x - infected by exogenous source
            # o - off

            # Starting max and min values
            # absolute values
            h_max = 0
            i_max = 0
            n_max = 0
            x_max = 0
            o_max = 0

            h_min = sim.config['maxhid']
            i_min = sim.config['maxhid']
            n_min = sim.config['maxhid']
            x_min = sim.config['maxhid']
            o_min = sim.config['maxhid']

            # Count index
            i   = 0

            # Starting counter to calculate the absolute average
            avg_h  = 0
            avg_i  = 0
            avg_n  = 0
            avg_x  = 0
            avg_o  = 0
            avg_a  = 0

            # Starting counter to calculate the proportional average
            avgt_h  = 0
            avgt_i  = 0
            avgt_n  = 0
            avgt_x  = 0
            avgt_o  = 0

            # Starting time marker
            time_t  = 0 # total time

            # Starting time marker (before)
            time_b   = 0

            # Starting structure to keep all history by host
            # History of each node (host)
            hist_bots = list()
            for j in range(sim.config['maxhid']+1):
                hist_bots.append(list())


            # Treat each history entry
            for hist in sim.count_history:
                (qtd_heal, qtd_inf, qtd_off, time_now, hid, status, status_before, qtd_end, qtd_exo) = hist
                i += 1
                qtd_all = qtd_heal + qtd_inf + qtd_off + qtd_end + qtd_exo

                hist_bots[hid].append((time_now, status))

                # Sum the number of host by instant time passed
                avg_h  += (qtd_heal) * (time_now - time_b)
                avg_i  += (qtd_inf ) * (time_now - time_b)
                avg_o  += (qtd_end ) * (time_now - time_b)
                avg_n  += (qtd_exo ) * (time_now - time_b)
                avg_x  += (qtd_off ) * (time_now - time_b)
                avg_a  += (qtd_all ) * (time_now - time_b)

                # Protection to division by zero (0)
                if qtd_all > 0:
                    # Sum the proportional host by instant time passed
                    avgt_h += (qtd_heal / qtd_all) * (time_now - time_b)
                    avgt_i += (qtd_inf  / qtd_all) * (time_now - time_b)
                    avgt_n += (qtd_end  / qtd_all) * (time_now - time_b)
                    avgt_x += (qtd_exo  / qtd_all) * (time_now - time_b)
                    avgt_o += (qtd_off  / qtd_all) * (time_now - time_b)

                time_t += (time_now - time_b)
                time_b = time_now

                # Get max and min
                if (time_now > sim.config['endtime']/2):
                    # Extreme points MIN and MAX
                    # Minimum
                    if qtd_heal < h_min :
                        h_min = qtd_heal
                    if qtd_inf < i_min :
                        i_min = qtd_inf
                    if qtd_end < n_min :
                        n_min = qtd_end
                    if qtd_exo < x_min :
                        x_min = qtd_exo
                    if qtd_off < o_min :
                        o_min = qtd_off
                    # Maximum
                    if qtd_heal > h_max:
                        h_max = qtd_heal
                    if qtd_inf > i_max:
                        i_max = qtd_inf
                    if qtd_end > n_max:
                        n_max = qtd_end
                    if qtd_exo > x_max:
                        x_max = qtd_exo
                    if qtd_off > o_max:
                        o_max = qtd_off

            # end for - Treat each history entry
            time_last = time_b

            # Average conclude
            # Divides the average by the time total
            if time_t > 0:
                avg_h  = avg_h  / time_t
                avg_i  = avg_i  / time_t
                avg_n  = avg_n  / time_t
                avg_x  = avg_x  / time_t
                avg_o  = avg_o  / time_t
                avg_a  = avg_a  / time_t

                avgt_h = avgt_h / time_t
                avgt_i = avgt_i / time_t
                avgt_n = avgt_n / time_t
                avgt_x = avgt_x / time_t
                avgt_o = avgt_o / time_t
            else:
                avgt_h = 0
                avgt_i = 0
                avgt_n = 0
                avgt_x = 0
                avgt_o = 0

            # Verify if the sum of proportion is one
            avgt_a = avgt_h + avgt_i + avgt_n + avgt_x + avgt_o

            # Make the vectors to take the information for each host
            # Total time passes in status by host
            total_unit_h = [0] * (sim.config['maxhid'] + 1)
            total_unit_i = [0] * (sim.config['maxhid'] + 1)
            total_unit_n = [0] * (sim.config['maxhid'] + 1)
            total_unit_x = [0] * (sim.config['maxhid'] + 1)
            total_unit_o = [0] * (sim.config['maxhid'] + 1)
            # Average between events
            avg_btwn_h =   [0] * (sim.config['maxhid'] + 1)
            avg_btwn_i =   [0] * (sim.config['maxhid'] + 1)
            avg_btwn_n =   [0] * (sim.config['maxhid'] + 1)
            avg_btwn_x =   [0] * (sim.config['maxhid'] + 1)
            avg_btwn_o =   [0] * (sim.config['maxhid'] + 1)
            avg_btwn_a_h = 0
            avg_btwn_a_i = 0
            # Number of times in status
            num_h =        [0] * (sim.config['maxhid'] + 1)
            num_i =        [0] * (sim.config['maxhid'] + 1)
            num_n =        [0] * (sim.config['maxhid'] + 1)
            num_x =        [0] * (sim.config['maxhid'] + 1)
            num_o =        [0] * (sim.config['maxhid'] + 1)

            # Get information to each host
            for k in range(sim.config['maxhid'] + 1):
                hist_uni = hist_bots[k]

                # Insert the last event to close history
                # The time_b is the last time before
                p = len(hist_uni) # length of unitary history
                hist_uni.append((time_b, hist_uni[p-1][1]))
                tmp_unit_h = 0
                tmp_unit_i = 0
                tmp_unit_n = 0
                tmp_unit_x = 0
                tmp_unit_o = 0

                # time of firt event
                time_base = hist_uni[0][0]

                # Status counter
                h_i = 0
                i_i = 0
                n_i = 0
                x_i = 0
                o_i = 0


                # Calculation to all events in the unitary history
                for j in range(p):
                    (tmp_time,tmp_status) = hist_uni[j]

                    # Increase the status counter
                    if tmp_status == sim._SUSCETIBLE_:
                        h_i += 1
                    elif tmp_status == sim._INFECTED_:
                        i_i += 1
                    elif tmp_status == sim._INFECTED_END_:
                        n_i += 1
                    elif tmp_status == sim._INFECTED_EXO_:
                        x_i += 1
                    elif tmp_status == sim._SHUTDOWN_:
                        o_i += 1

                    (tmp_time_next, tmp_status_next)  = hist_uni[j+1]

                    if tmp_status == sim._SUSCETIBLE_:
                        tmp_unit_h += tmp_time_next - tmp_time
                    elif tmp_status == sim._INFECTED_:
                        tmp_unit_i += tmp_time_next - tmp_time
                    elif tmp_status ==  sim._INFECTED_END_:
                        tmp_unit_n += tmp_time_next - tmp_time
                    elif tmp_status ==  sim._INFECTED_EXO_:
                        tmp_unit_x += tmp_time_next - tmp_time
                    elif tmp_status == sim._SHUTDOWN_:
                        tmp_unit_o += tmp_time_next - tmp_time

                # end for - Calculation to all events in the unitary history



                if h_i > 0:
                    total_unit_h[k] = float(tmp_unit_h)
                    num_h[k] = h_i
                if i_i > 0:
                    total_unit_i[k] = float(tmp_unit_i)
                    num_i[k] = i_i
                if n_i > 0:
                    total_unit_n[k] = float(tmp_unit_n)
                    num_n[k] = n_i
                if x_i > 0:
                    total_unit_x[k] = float(tmp_unit_x)
                    num_x[k] = x_i
                if o_i > 0:
                    total_unit_o[k] = float(tmp_unit_o)
                    num_o[k] = o_i

            # end for - Get information to each host
            avg2_h = np.mean(total_unit_h)
            avg2_i = np.mean(total_unit_i)
            avg2_n = np.mean(total_unit_n)
            avg2_x = np.mean(total_unit_x)
            avg2_o = np.mean(total_unit_o)

            total_sum = np.array(total_unit_h) + np.array(total_unit_i) + np.array(total_unit_n) + np.array(total_unit_x) + np.array(total_unit_o)
            avgt2_h = np.mean(np.array(total_unit_h) / total_sum)
            avgt2_i = np.mean(np.array(total_unit_i) / total_sum)
            avgt2_n = np.mean(np.array(total_unit_n) / total_sum)
            avgt2_x = np.mean(np.array(total_unit_x) / total_sum)
            avgt2_o = np.mean(np.array(total_unit_o) / total_sum)
            avgt2_a = avgt2_h + avgt2_i + avgt2_n + avgt2_x + avgt2_o


            # Events exclude the Master (exogenous)
            tot_unit_host_h = np.array(total_unit_h[1:])
            tot_unit_host_i = np.array(total_unit_i[1:])
            tot_unit_host_n = np.array(total_unit_n[1:])
            tot_unit_host_x = np.array(total_unit_x[1:])
            tot_unit_host_o = np.array(total_unit_o[1:])

            num_h_array      = np.array(num_h[1:])
            num_i_array      = np.array(num_i[1:])
            num_n_array      = np.array(num_n[1:])
            num_x_array      = np.array(num_x[1:])
            num_o_array      = np.array(num_o[1:])

            avg_u_h = np.mean(tot_unit_host_h)
            avg_u_i = np.mean(tot_unit_host_i)
            avg_u_n = np.mean(tot_unit_host_n)
            avg_u_x = np.mean(tot_unit_host_x)
            avg_u_o = np.mean(tot_unit_host_o)

            total_time_unit = tot_unit_host_h[0] + tot_unit_host_i[0] + tot_unit_host_n[0] + tot_unit_host_x[0] + tot_unit_host_o[0]
            avg_prop_u_h = np.mean(tot_unit_host_h / total_time_unit)
            avg_prop_u_i = np.mean(tot_unit_host_i / total_time_unit)
            avg_prop_u_n = np.mean(tot_unit_host_n / total_time_unit)
            avg_prop_u_x = np.mean(tot_unit_host_x / total_time_unit)
            avg_prop_u_o = np.mean(tot_unit_host_o / total_time_unit)
            avg_prop_u_a = avg_prop_u_h + avg_prop_u_i + avg_prop_u_n + avg_prop_u_x + avg_prop_u_o

            rate_u_h = np.mean(num_h_array/total_time_unit)
            rate_u_i = np.mean(num_i_array/total_time_unit)
            rate_u_n = np.mean(num_n_array/total_time_unit)
            rate_u_x = np.mean(num_x_array/total_time_unit)
            rate_u_o = np.mean(num_o_array/total_time_unit)

            # Average time between events
            # the average time between susceptible
            time_btw_h   = np.mean(tot_unit_host_i + tot_unit_host_n + tot_unit_host_x)
            # the average time between infected
            time_btw_i   = np.mean(tot_unit_host_h + tot_unit_host_o)
            # the average time between OFF
            time_btw_off = np.mean(tot_unit_host_h + tot_unit_host_i + tot_unit_host_n + tot_unit_host_x)
            # the average time between ON
            time_btw_on  = np.mean(tot_unit_host_o)


            # Save parameters of round
            round_info_avg_t = (rnd, elem_param, avgt2_h, avgt2_i, avgt2_n, avgt2_x, avgt2_o, avgt2_a)
            round_info_avg_u = (rnd, elem_param, avg_u_h, avg_u_i, avg_u_n, avg_u_x, avg_u_o)
            round_info_time_btw = (rnd, elem_param, time_btw_h, time_btw_i, time_btw_off, time_btw_on)

            info_average_proportional.append(round_info_avg_t)
            info_average_from_unitary.append(round_info_avg_u)
            info_time_between_events.append(round_info_time_btw)

            # h_p_lst.append((rnd, elem_param, avgt_h))
            # i_p_lst.append((rnd, elem_param, avgt_i))
            # n_p_lst.append((rnd, elem_param, avgt_n))
            # x_p_lst.append((rnd, elem_param, avgt_x))
            # o_p_lst.append((rnd, elem_param, avgt_o))
            # a_p_lst.append((rnd, elem_param, avgt_a))


            # =================================================================
            # Plot Round
            if PLOT_ROUND or WEB_ROUND:
                #(qtd_heal, qtd_inf, qtd_off, time_now, hid, status, status_before, qtd_end, qtd_exo)
                #   0     ,   1    ,   2    ,  3  ,  4 ,   5   ,      6       ,   7    ,   8



                # Plotting
                hist_array = np.array(sim.count_history)
                # Suscetible
                plt.plot(hist_array[:,3], hist_array[:,0]/(sim.config['maxhid'] +1), label='suscetível'   , color='b')
                # Infected (without origin)
                plt.plot(hist_array[:,3], (hist_array[:,7]+hist_array[:,8])/(sim.config['maxhid'] +1), label='infectado'      , color='r')
                # OFF
                plt.plot(hist_array[:,3], hist_array[:,2]/(sim.config['maxhid'] +1), label='desligado'           , color='g')
                # Total
                #total_array = hist_array[:,0] + hist_array[:,1] + hist_array[:,7] + hist_array[:,8] + hist_array[:,2]
                #plt.plot(hist_array[:,3], total_array    /(sim.config['maxhid'] +1), label='total'         , color='k')

                hist_infect_array = np.array(sim.hist_infect)
                print(hist_infect_array.shape)
                total_infected = sim.attempt_infected_endogeno + sim.attempt_infected_exogeno
                # Acumulated endogenous infection
                # plt.plot(hist_infect_array[:,0],hist_infect_array[:,4]/total_infected, label='endogenous acumulated', color='c')
                # Acumulated exogenous infection
                # plt.plot(hist_infect_array[:,0],hist_infect_array[:,5]/total_infected, label='exogenous acumulated' , color='m')

                plt.xlabel('time')
                plt.ylabel('proportion of')
                if rnd == 0:
                    xend = sim.config['endtime']
                    #print (1.1*xend)
                    #return 0
                    plt.xlim((0.0, 1.2 * xend))
                    plt.legend(loc='lower right')
                #plt.ylim((0.0,1.7))
                #plt.legend(loc='upper right')
                fig_round_name ='img/fig_exec-{:>03d}_{:02d}_param-{:>02d}_round-{:>02d}.png'.format(counter, evt,param,rnd)
                fig_round_name_pdf ='img/fig_exec-{:>03d}_{:02d}_param-{:>02d}_round-{:>02d}.pdf'.format(counter,evt,param,rnd)
                plt.savefig(_WEB_LOCAL_+ fig_round_name, dpi=my_dpi)
                plt.savefig(_WEB_LOCAL_+ fig_round_name_pdf,  bbox_inches='tight')
                #plt.show()
                plt.clf()
                copy(_WEB_LOCAL_ + fig_round_name, _WEB_REMOTE_+ fig_round_name ) # shutil
                copy(_WEB_LOCAL_ + fig_round_name_pdf, _WEB_REMOTE_+ fig_round_name_pdf ) # shutil

                # Print again with proportional graph filled
                # Infected
                total_array = hist_array[:,0] + hist_array[:,1] + hist_array[:,7] + hist_array[:,8] + hist_array[:,2]
                plt.fill_between(hist_array[:,3], total_array/(sim.config['maxhid'] +1), label='infectado'   , color='r')
                # Suscetible
                plt.fill_between(hist_array[:,3], (hist_array[:,0]+hist_array[:,2])/(sim.config['maxhid'] +1), label='suscetível'      , color='b')
                # OFF
                plt.fill_between(hist_array[:,3], hist_array[:,2]/(sim.config['maxhid'] +1), label='desligado'           , color='g')
                # Total
                #total_array = hist_array[:,0] + hist_array[:,1] + hist_array[:,7] + hist_array[:,8] + hist_array[:,2]
                #plt.plot(hist_array[:,3], total_array    /(sim.config['maxhid'] +1), label='total'         , color='k')

                hist_infect_array = np.array(sim.hist_infect)
                print(hist_infect_array.shape)
                total_infected = sim.attempt_infected_endogeno + sim.attempt_infected_exogeno
                # Acumulated endogenous infection
                # plt.plot(hist_infect_array[:,0],hist_infect_array[:,4]/total_infected, label='endogenous acumulated', color='c')
                # Acumulated exogenous infection
                # plt.plot(hist_infect_array[:,0],hist_infect_array[:,5]/total_infected, label='exogenous acumulated' , color='m')

                plt.xlabel('time')
                plt.ylabel('proportion of')
                if rnd == 0:
                    xend = sim.config['endtime']
                    #print (1.1*xend)
                    #return 0
                    plt.xlim((0.0, 1.2 * xend))
                    plt.legend(loc='lower right')
                #plt.ylim((0.0,1.7))
                #plt.legend(loc='upper right')
                fig_round_name_pdf2 ='img/fig_filled-{:>03d}_{:02d}_param-{:>02d}_round-{:>02d}.pdf'.format(counter,evt,param,rnd)
                plt.savefig(_WEB_LOCAL_+ fig_round_name_pdf2,  bbox_inches='tight')
                #plt.show()
                plt.clf()
                copy(_WEB_LOCAL_ + fig_round_name_pdf2, _WEB_REMOTE_+ fig_round_name_pdf2 ) # shutil


                # Proportional of endogenous and exogenous infections
                # Endogenous infected
                inf_rnd_plt = hist_array[:,7]+hist_array[:,8]
                end_rnd_plt = np.ones( len(inf_rnd_plt),dtype=float)
                exo_rnd_plt = hist_array[:,8] / inf_rnd_plt
                '''
                print(hist_array[:,3])
                print(end_rnd_plt)
                print(exo_rnd_plt)
                print(len(hist_array[:,3]))
                print(len(end_rnd_plt))
                print(len(exo_rnd_plt))
                '''

                plt.fill_between(hist_array[:,3], end_rnd_plt, linewidth=0.0, label='infecção endógena' , color='m')
                # Exogenous infected
                plt.fill_between(hist_array[:,3], exo_rnd_plt, linewidth=0.0, label='infecção exógena'  , color='c')
                plt.xlabel('time')
                plt.ylabel('proportion of')
                if rnd == 0:
                    plt.xlim((0.0, 1.2 * xend))
                    plt.legend(loc='lower right')
                #plt.ylim((0.0,1.7))
                #plt.legend(loc='upper right')
                fig_round_name2 ='img/fig_end_exo-{:>03d}_{:02d}_param-{:>02d}_round-{:>02d}.pdf'.format(counter, evt,param,rnd)
                plt.savefig(_WEB_LOCAL_+ fig_round_name2,  bbox_inches='tight')
                #plt.show()
                plt.clf()
                copy(_WEB_LOCAL_ + fig_round_name2, _WEB_REMOTE_+ fig_round_name2 ) # shutil


                # Show the informations
                # round_name ='_exec-{:>03d}_param-{:>02d}_round-{:>02}.png'.format(counter,param,rnd)
                #with open("info/infect_info"+round_name+".txt", "w") as f1:
                #    for h in sim.hist_infect:
                #        f1.write("Time:{:f},End:{:d},Exo:{:d}\n".format(h[0], h[4], h[5]))

                if WEB_ROUND:
                    # head
                    head_html_name = 'head.html'
                    html_round_name ='exec-{:>03d}_param-{:>02d}_round-{:>02}.html'.format(counter,param,rnd)
                    with open(_WEB_LOCAL_+ head_html_name) as f:
                        with open(_WEB_LOCAL_+ html_round_name, "w") as f1:
                            for line in f:
                                f1.write(line)

                    # Body with graphs
                    with open(_WEB_LOCAL_+ html_round_name,"a") as the_html:
                        the_html.write("      <figure><img src=\"{}\" alt=\"{}\">\n".format(fig_round_name,str_param))
                        the_html.write("        <figcaption>\n")
                        the_html.write("          <h2> Simulation {:03d}; {:>02d}</h2>\n".format(counter, rnd))
                        the_html.write("          <ul>\n")
                        the_html.write("                <li>Number of elements:</li>\n")
                        the_html.write("                <li>{:d}</li>\n".format(sim.config['maxhid']))
                        the_html.write("          </ul>\n          <ul>\n")
                        the_html.write("                <li>Infection rate (all):</li>\n")
                        the_html.write("                <li>{:.5e}</li>\n".format(sim.config['bot']['params'][0]))
                        the_html.write("          </ul>\n          <ul>\n")
                        the_html.write("                <li>Infection rate (master):</li>\n")
                        the_html.write("                <li>{:.5e}</li>\n".format(sim.config['bot']['master'][0]))
                        the_html.write("          </ul>\n          <ul>\n")
                        the_html.write("                <li>Average on time:</li>\n")
                        the_html.write("                <li>{}</li>\n".format(sim.config['dists']['host_on_time']['dist']))

                        for val in sim.config['dists']['host_on_time']['params']:
                            the_html.write("                <li>;{:.5e}</li>\n".format(val))

                        the_html.write("          </ul>\n          <ul>\n")
                        the_html.write("                <li>Average off time:</li>\n")
                        the_html.write("                <li>{}</li>\n".format(sim.config['dists']['host_off_time']['dist']))

                        for val in sim.config['dists']['host_off_time']['params']:
                            the_html.write("                <li>;{:.5e}</li>\n".format(val))

                        the_html.write("          </ul>\n")
                        the_html.write("          <ul>\n")
                        the_html.write("                <li><footer class=\"more\"><a href=\"#\" onclick=\"goBack()\">Return &raquo;</a></footer></li>\n")
                        the_html.write("                <li><footer class=\"more\"><a href=\"index.html\">Home &raquo;</a></footer></li>\n")
                        the_html.write("          </ul>\n")
                        the_html.write("        </figcaption>\n")
                        the_html.write("      </figure>\n")
                        the_html.write("    </section>\n")
                        the_html.write("    <script>\n")
                        the_html.write("      function goBack() {\n")
                        the_html.write("        window.history.back();\n")
                        the_html.write("      }\n")
                        the_html.write("    </script>\n")

                        the_html.write("    <div id=\"line_one\" >\n")
                        the_html.write("      <section class=\"clear\">\n")
                        the_html.write("        <!-- article 1 -->\n")
                        the_html.write("        <article class=\"six_sixth\">\n")
                        the_html.write("        <BR>")
                        the_html.write("        Parameters[{}]:{}: {} \t Round:{:>2d}\n".format(param+1,str_param, elem_param,rnd+1))
                        the_html.write("        <table>\n")
                        the_html.write("          <tr>\n")
                        the_html.write("            <th>                     </th> <th> min </th> <th> max </th> <th> average </th> <th> proportion2</th> <th> without master </th> \n")
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Susceptible         </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (h_min, h_max, avg_h  , avgt2_h , avg_prop_u_h))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Infected            </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (i_min, i_max, avg_i  , avgt2_i, avg_prop_u_i))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Endogenous Infected </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (n_min, n_max, avg_n  , avgt2_n  , avg_prop_u_n))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Exogenous Infected  </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (x_min, x_max, avg_x  , avgt2_x  , avg_prop_u_x))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Off                 </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (o_min, o_max, avg_o  , avgt2_o  , avg_prop_u_o))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> All                 </td> <td>  -  </td> <td> -   </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (              avg_a  , avgt2_a  , avg_prop_u_a))
                        the_html.write("          </tr>\n")
                        the_html.write("        </table>\n")
                        the_html.write("        <table>\n")
                        the_html.write("          <tr>\n")
                        the_html.write("            <td> Average of time between susceptible </td> <td> {:.5e} </td>\n".format(time_btw_h))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Average of time between infected    </td> <td> {:.5e} </td>\n".format(time_btw_i))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Rate of infections (unclassified)   </td> <td> {:.5e} </td>\n".format(rate_u_i))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Rate of endogenous infections       </td> <td> {:.5e} </td>\n".format(rate_u_n))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Rate of exogenous infections        </td> <td> {:.5e} </td>\n".format(rate_u_x))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Rate of Heal                        </td> <td> {:.5e} </td>\n".format(rate_u_h))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Attempt to infect endogenous        </td> <td> {:5d}  </td>\n".format(sim.attempt_infected_endogeno))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Attempt to infect exogenous         </td> <td> {:5d}  </td>\n".format(sim.attempt_infected_exogeno))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Tx attempt to infect endogenous     </td> <td> {:.5e} </td>\n".format(float(sim.attempt_infected_endogeno)/(sim.config["maxhid"]*time_last)))
                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Tx attempt to infect exogenous      </td> <td> {:.5e} </td>\n".format(float(sim.attempt_infected_exogeno)/time_last))
                        the_html.write("          </tr>\n")
                        the_html.write("        </table>\n")
                        the_html.write("        <table>\n")
                        the_html.write("          <tr>\n")
                        the_html.write("            <th> ID </th> <th> Suscetible (Times) </th> <th> Endogenous Infected (Times) </th> <th> Exogenous Infected (Times) </th> <th> Off (Times) </th> <th> Total Time </th> \n")

                        for i in range(sim.config['maxhid']+1):
                            the_html.write("          </tr>\n\t<tr>\n")
                            the_html.write("            <td> {:>4d}</td> <td>{:7.2f} ({:d})</td> <td>{:7.2f} ({:d})</td> <td>{:7.2f} ({:d})</td> <td>{:7.2f} ({:d})</td> <td>{:7.2f}</td>\n".format(i,
                                        total_unit_h[i], num_h[i],
                                        total_unit_n[i], num_n[i],
                                        total_unit_x[i], num_x[i],
                                        total_unit_o[i], num_o[i],
                                        total_unit_h[i] + total_unit_n[i] + total_unit_x[i] + total_unit_o[i]))

                        the_html.write("          </tr>\n\t<tr>\n")
                        the_html.write("            <td> Average </td> <td>{:7.2f} ({:<4.1f})</td> <td>{:7.2f} ({:<4.1f})</td> <td>{:7.2f} ({:<4.1f})</td> <td>{:7.2f} ({:<4.1f})</td> <td>{:7.2f}</td>\n".format(
                                        np.mean(tot_unit_host_h), np.mean(num_h_array),
                                        np.mean(tot_unit_host_n), np.mean(num_n_array),
                                        np.mean(tot_unit_host_x), np.mean(num_x_array),
                                        np.mean(tot_unit_host_o), np.mean(num_o_array),
                                        np.mean(tot_unit_host_h + tot_unit_host_n + tot_unit_host_x + tot_unit_host_o) ))
                        the_html.write("          </tr>\n")
                        the_html.write("        </table>\n")
                        the_html.write("            </ul>\n")
                        the_html.write("        </article>\n")
                        the_html.write("      </section>\n")
                        the_html.write("    </div>\n")

                    # Foot HTML Round
                    foot_html_name = 'foot.html'
                    with open(_WEB_LOCAL_+ foot_html_name) as f:
                        with open(_WEB_LOCAL_+ html_round_name, "a") as f1:
                            for line in f:
                                f1.write(line)

                    # Copy to remote HTML Round
                    copy(_WEB_LOCAL_ + html_round_name, _WEB_REMOTE_+ html_round_name ) # shutil



            # Print standard output
            if PRINT_ROUND:
                # standard output
                if rnd == 0:
                    print('\n========================================================')
                    print(str_param)
                else:
                    print('========================================================')
                print("Parâmetro[{}]:{}: {} \t Round:{:>2d}".format(param+1,str_param, elem_param,rnd+1))
                print("\tmin \tmax \taverage \tproportion \tunit")
                print("susce:\t{} \t{} \t{:8.4f} \t{:>1.4f} \t{:>1.4f}".format(h_min, h_max, avg_h,  avgt_h ,avg_prop_u_h))
                print("infec:\t{} \t{} \t{:8.4f} \t{:>1.4f} \t{:>1.4f}".format(i_min, i_max, avg_i, avgt_i,avg_prop_u_i))
                print("end:  \t{} \t{} \t{:8.4f} \t{:>1.4f} \t{:>1.4f}".format(i_min, i_max, avg_i, avgt_n  ,avg_prop_u_n))
                print("exo:  \t{} \t{} \t{:8.4f} \t{:>1.4f} \t{:>1.4f}".format(i_min, i_max, avg_i, avgt_x  ,avg_prop_u_x))
                print("off:  \t{} \t{} \t{:8.4f} \t{:>1.4f} \t{:>1.4f}".format(o_min, o_max, avg_o,   avgt_o  ,avg_prop_u_o))
                print("All : \t-  \t-  \t{:8.4f} \t{:>1.4f} \t{:>1.4f}".format(              avg_a,   avgt_a  ,avg_prop_u_a))
                print("Average of time between heal  : {:10.3f}".format(time_btw_h))
                print("Average of time between infect: {:10.3f}".format(time_btw_i))
                print("Rate of infection.............: {:10.7f}".format(rate_u_i))
                print("Rate of endogenous infection..: {:10.7f}".format(rate_u_n))
                print("Rate of exogenous infection...: {:10.7f}".format(rate_u_x))
                print("Rate of Heal..................: {:10.7f}".format(rate_u_h))
                print("Attempt to infect endogenous..: {:d}".format(sim.attempt_infected_endogeno))
                print("Attempt to infect exogenous...: {:d}".format(sim.attempt_infected_exogeno))
                print("Tx attempt to infect end......: {:10.7f}".format(float(sim.attempt_infected_endogeno)/(sim.config["maxhid"]*time_last)))
                print("Tx attempt to infect exo......: {:10.7f}".format(float(sim.attempt_infected_exogeno)/time_last))

                print("||ID|Sus Time(qtd)|End Time(qtd)|Exo Time(qtd)|Off Time(qtd)|Total||")
                str_uni_average = ''
                for i in range(sim.config['maxhid']+1):
                    str_temp = '||{:>4d}|{:7.2f}/{:<4d}|{:7.2f}/{:<4d}|{:7.2f}/{:<4d}|{:7.2f}/{:<4d}|{:7.2f}||'.format(i,
                                total_unit_h[i], num_h[i],
                                total_unit_n[i], num_n[i],
                                total_unit_x[i], num_x[i],
                                total_unit_o[i], num_o[i],
                                total_unit_h[i] + total_unit_n[i]  + total_unit_x[i] + total_unit_o[i])
                    str_uni_average = str_uni_average + '\t' + str_temp
                    if (((i+1) % 2) == 0):
                        str_uni_average = str_uni_average + '\n'
                print(str_uni_average)
                print("Total:")
                print('||{}|{:7.2f}/{:<4d}|{:7.2f}/{:<4d}|{:7.2f}/{:<4d}|{:7.2f}||'.format('\t',
                            np.mean(tot_unit_host_h), np.sum(num_h_array),
                            np.mean(tot_unit_host_n), np.sum(num_n_array),
                            np.mean(tot_unit_host_x), np.sum(num_x_array),
                            np.mean(tot_unit_host_o), np.sum(num_o_array),
                            np.mean(tot_unit_host_h + tot_unit_host_n + tot_unit_host_x + tot_unit_host_o)))
                #avg_a2  = np.mean(tot_unit_host_h) + np.mean(tot_unit_host_i) + np.mean(tot_unit_host_o)
                #tot_time  = total_unit_h[0] + total_unit_i[0] + total_unit_o[0]
                #avgt_a2 = np.mean(tot_unit_host_h/tot_time) + np.mean(tot_unit_host_i/tot_time) + np.mean(tot_unit_host_o/tot_time)

                # file output
                filename ='mirai_sim_coun{:>03d}_{:04d}_param{:>03d}_{}.txt'.format(counter, evt,param,str_param)
                if rnd == 0:
                    #print('Starting writing in file: \'{}.txt\''.format(filename))
                    with open(_GRAPH_ + filename, 'w') as the_file:
                        the_file.write('Execution number: {:3d}\n'.format(counter))
                        the_file.write('Parameter tested: {}\n'.format(str_param))
                        the_file.write('\n========================================================\n')

                with open(_GRAPH_ + filename, 'a') as the_file:
                    the_file.write('========================================================\n')
                    the_file.write("Parameters[{}]:{}: {} \t Round:{:>2d}\n".format(param+1,str_param, elem_param,rnd+1))
                    the_file.write('Total of hosts...........: {:3d}\n'.format(sim.config['maxhid']))
                    the_file.write('Endogenous infection rate: {:10.7f}\n'.format(sim.config['bot']['params'][0]))
                    the_file.write('Exogenous infection rate.: {:10.7f}\n'.format(sim.config['bot']['master'][0]))
                    the_file.write('Host on time.............: {:10.3f} - {}\n'.format(sim.config['dists']['host_on_time']['params'][0],sim.config['dists']['host_on_time']['dist']))
                    the_file.write('Host off time............: {:10.3f} - {}\n'.format(sim.config['dists']['host_off_time']['params'][0],sim.config['dists']['host_off_time']['dist']))

                    the_file.write("\tmin \tmax \taverage \tproportion\n")
                    the_file.write("susce:\t{} \t{} \t{:8.4f} \t{:>1.4f}\n".format (h_min, h_max, avg_h,  avgt_h))
                    the_file.write("infec:\t{} \t{} \t{:8.4f} \t{:>1.4f}\n".format(i_min, i_max, avg_i, avgt_i))
                    the_file.write("off:\t{} \t{} \t{:8.4f} \t{:>1.4f}\n".format  (o_min, o_max, avg_o,   avgt_o))
                    the_file.write("All :\t- \t- \t{:8.4f}  \t{:>1.4f}\n".format (avg_a, avgt_a))
                    the_file.write("Average of time between heal  : {:10.3f}\n".format(time_btw_h))
                    the_file.write("Average of time between infect: {:10.3f}\n".format(time_btw_i))
                    the_file.write("Tx infect.....................: {:10.7f}\n".format(rate_u_i))
                    the_file.write("Tx Heal.......................: {:10.7f}\n".format(rate_u_h))
                    the_file.write("Attempt to infect endogenous..: {:5d}\n".format(sim.attempt_infected_endogeno))
                    the_file.write("Attempt to infect exogenous...: {:5d}\n".format(sim.attempt_infected_exogeno))
                    the_file.write("Tx attempt to infect end......: {:10.7f}\n".format(float(sim.attempt_infected_endogeno)/(sim.config["maxhid"]*time_last)))
                    the_file.write("Tx attempt to infect exo......: {:10.7f}\n".format(float(sim.attempt_infected_exogeno)/time_last))
                    the_file.write("|ID!Sus Time/Sus qtd!Inf Time/Inf qtd!Off Time/Off qtd!Total|")
                    the_file.write("{}\n".format(str_uni_average))

                if WEB_PARAM:
                    web_temp_name ='exec-{:>03d}_param-{:>02d}_temp.html'.format(counter,param)
                    with open(_WEB_LOCAL_ + web_temp_name, 'a') as web_temp_file:
                        web_temp_file.write("<BR>")
                        web_temp_file.write("        <BR>")
                        web_temp_file.write("        Parameters[{}]:{}: {} \t Round:{:>2d}\n".format(param+1,str_param, elem_param,rnd+1))
                        web_temp_file.write("        <table>\n")
                        web_temp_file.write("          <tr>\n")
                        web_temp_file.write("            <th>                     </th> <th> min </th> <th> max </th> <th> average </th> <th> proportion</th> <th> without master </th> \n")
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Susceptible         </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (h_min, h_max, avg_h , avgt_h , avg_prop_u_h))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Infected            </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (i_min, i_max, avg_i, avgt_i, avg_prop_u_i))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Endogenous Infected </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (n_min, n_max, avg_n  , avgt_n  , avg_prop_u_n))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Exogenous Infected  </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (x_min, x_max, avg_x  , avgt_x  , avg_prop_u_x))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Off                 </td> <td> {}  </td> <td> {}  </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (o_min, o_max, avg_o  , avgt_o  , avg_prop_u_o))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> All                 </td> <td>  -  </td> <td> -   </td> <td> {:8.4f} </td> <td>  {:>1.4f} </td> <td>  {:>1.4f} </td>\n".format (              avg_a  , avgt_a  , avg_prop_u_a))
                        web_temp_file.write("          </tr>\n")
                        web_temp_file.write("        </table>\n")
                        web_temp_file.write("        <table>\n")
                        web_temp_file.write("          <tr>\n")
                        web_temp_file.write("            <td> Average of time between heal  </td> <td> {:.5e}</td>\n".format(time_btw_h))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Average of time between infect</td> <td> {:.5e}</td>\n".format(time_btw_i))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Tx infect                     </td> <td> {:.5e}</td>\n".format(1/time_btw_h))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Tx Heal                       </td> <td> {:.5e}</td>\n".format(1/time_btw_i))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Attempt to infect endogenous  </td> <td> {:5d} </td>\n".format(sim.attempt_infected_endogeno))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Attempt to infect exogenous   </td> <td> {:5d} </td>\n".format(sim.attempt_infected_exogeno))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Tx attempt to infect endogenous      </td> <td> {:.5e}</td>\n".format(float(sim.attempt_infected_endogeno)/(sim.config["maxhid"]*time_last)))
                        web_temp_file.write("          </tr>\n\t<tr>\n")
                        web_temp_file.write("            <td> Tx attempt to infect exogenous      </td> <td> {:.5e}</td>\n".format(float(sim.attempt_infected_exogeno)/time_last))
                        web_temp_file.write("          </tr>\n")
                        web_temp_file.write("        </table>\n")

            # Reset the simulator parameters to next round
            sim.count_history = list()
            sim.heal_hosts = 0
            sim.infected_hosts = 0
            sim.infected_end_hosts = 0
            sim.infected_exo_hosts = 0
            sim.off_hosts = 0
            sim.hist_infect = list()
            sim.attempt_infected_endogeno = 0
            sim.attempt_infected_exogeno = 0
            sim.now = 0
            sim.evqueue = list()
            sim.evseq = 0
        # }}} end of round


        if PLOT_PARAM:
            # info_average_proportional => (rnd, elem_param, avgt_h, avgt_i, avgt_n, avgt_x, avgt_o, avgt_a)
            # round_info_avg_u = (rnd, elem_param, avg_u_h, avg_u_i, avg_u_n, avg_u_x, avg_u_o)
            # round_info_time_btw = (rnd, elem_param, time_btw_h, time_btw_i, time_btw_off, time_btw_on)

            info_array = np.array(info_average_proportional)
            #h_p_hst = np.array(h_p_lst)
            #i_p_hst = np.array(i_p_lst)
            #o_p_hst = np.array(o_p_lst)
            #a_p_hst = np.array(a_p_lst)
            plt.plot(info_array[:,1], info_array[:,2], label='susceptible'    , color='b')
            plt.plot(info_array[:,1], info_array[:,4] + info_array[:,5], label='infected'       , color='r')
            plt.plot(info_array[:,1], info_array[:,4], label='end infected'   , color='#ee0000', linestyle = ':')
            plt.plot(info_array[:,1], info_array[:,5], label='exo infected'   , color='#ee0055', linestyle = '--')
            plt.plot(info_array[:,1], info_array[:,6], label='off'            , color='g')
            plt.plot(info_array[:,1], info_array[:,7], label='all'            , color='y')

            plt.xlabel(str_param)
            plt.ylabel('proportion of')
            #plt.ylim((0.0,1.7))
            plt.legend(loc='right')
            filename_pdf ='exec_counter-{:>03d}_{:02d}_param-{:>03d}.pdf'.format(counter,evt,param)
            plt.savefig(_GRAPH_ + filename_pdf)
            #plt.show()
            plt.clf()


        if WEB_PARAM:
            # ============================================
            #Figure

            plt.plot(info_array[:,1], info_array[:,2], label='susceptible'    , color='b')
            plt.plot(info_array[:,1], info_array[:,4]+info_array[:,5], label='infected'       , color='r')
            plt.plot(info_array[:,1], info_array[:,4], label='end infected'   , color='#ee0000', linestyle = ':')
            plt.plot(info_array[:,1], info_array[:,5], label='exo infected'   , color='#ee0055', linestyle = '--')
            plt.plot(info_array[:,1], info_array[:,6], label='off'            , color='g')
            plt.plot(info_array[:,1], info_array[:,7], label='all'            , color='y')

            plt.xlabel(str_param)
            plt.ylabel('proportion of')
            plt.ylim((0.0,1.7))
            plt.legend(loc='upper right')
            fig_name ='img/fig_exec-{:>03d}_{:02d}_param-{:>02d}.png'.format(counter, evt,param)
            fig_name_pdf ='img/fig_exec-{:>03d}_{:02d}_param-{:>02d}.pdf'.format(counter, evt,param)
            plt.savefig(_WEB_LOCAL_+ fig_name, dpi=my_dpi)
            plt.savefig(_WEB_LOCAL_+ fig_name_pdf,  bbox_inches='tight')
            #plt.show()
            plt.clf()
            copy(_WEB_LOCAL_ + fig_name, _WEB_REMOTE_+ fig_name ) # shutil

            # =============================================
            html0_name ='exec-{:>03d}_param-00.html'.format(counter)
            html1_name ='exec-{:>03d}_param-01.html'.format(counter)
            html2_name ='exec-{:>03d}_param-02.html'.format(counter)
            html3_name ='exec-{:>03d}_param-03.html'.format(counter)
            html4_name ='exec-{:>03d}_param-04.html'.format(counter)
            fig0_name ='img/fig_exec-{:>03d}_{:>02d}_param-00.png'.format(counter,evt)
            fig1_name ='img/fig_exec-{:>03d}_{:>02d}_param-01.png'.format(counter,evt)
            fig2_name ='img/fig_exec-{:>03d}_{:>02d}_param-02.png'.format(counter,evt)
            fig3_name ='img/fig_exec-{:>03d}_{:>02d}_param-03.png'.format(counter,evt)
            fig4_name ='img/fig_exec-{:>03d}_{:>02d}_param-04.png'.format(counter,evt)
            # File for this Figure
            # head
            head_html_name = 'head.html'
            html_name ='exec-{:>03d}_param-{:>02d}.html'.format(counter,param)
            with open(_WEB_LOCAL_+ head_html_name) as f:
                with open(_WEB_LOCAL_+ html_name, "w") as f1:
                    for line in f:
                        f1.write(line)

            # Body with graphs
            with open(_WEB_LOCAL_+ html_name,"a") as the_html:
                the_html.write("      <figure><img src=\"{}\" alt=\"{}\">\n".format(fig_name,str_param))
                the_html.write("        <figcaption>\n")
                the_html.write("          <h2> Simulation {:03d}</h2>\n".format(counter))
                the_html.write("          <ul>\n")
                if param == 0:
                    the_html.write("                <li> {} </li>\n".format(str_param))
                    j = -1
                    for val in str_values:
                        j += 1
                        the_html.write("                <li>")
                        if j != 0:
                            the_html.write(";")
                        the_html.write("<a href=\"exec-{:03d}_param-{:02d}_round-{:02d}.html\"> {} </a></li>\n".format(counter, param, j,val))
                else:
                    the_html.write("                <li>Number of elements:</li>\n")
                    the_html.write("                <li>{:d}</li>\n".format(sim.config['maxhid']))

                the_html.write("          </ul>\n          <ul>\n")

                if param == 1:
                    the_html.write("                <li> {} </li>\n".format(str_param))
                    j = -1
                    for val in str_values:
                        j += 1
                        the_html.write("                <li>")
                        if j != 0:
                            the_html.write(";")
                        the_html.write("<a href=\"exec-{:03d}_param-{:02d}_round-{:02d}.html\"> {} </a></li>\n".format(counter, param, j,val))
                else:
                    the_html.write("                <li>Infection rate (bot):</li>\n")
                    the_html.write("                <li>{:.5e}</li>\n".format(sim.config['bot']['params'][0]))

                the_html.write("          </ul>\n          <ul>\n")

                if param == 2:
                    the_html.write("                <li> {} </li>\n".format(str_param))
                    j = -1
                    for val in str_values:
                        j += 1
                        the_html.write("                <li>")
                        if j != 0:
                            the_html.write(";")
                        the_html.write("<a href=\"exec-{:03d}_param-{:02d}_round-{:02d}.html\"> {} </a></li>\n".format(counter, param, j,val))
                else:
                    the_html.write("                <li>Infection rate (master):</li>\n")
                    the_html.write("                <li>{:.5e}</li>\n".format(sim.config['bot']['master'][0]))

                the_html.write("          </ul>\n          <ul>\n")

                if param == 3:
                    the_html.write("                <li> {} </li>\n".format(str_param))
                    j = -1
                    for val in str_values:
                        j += 1
                        the_html.write("                <li>")
                        if j != 0:
                            the_html.write(";")
                        the_html.write("<a href=\"exec-{:03d}_param-{:02d}_round-{:02d}.html\"> {} </a></li>\n".format(counter, param, j,val))
                else:
                    the_html.write("                <li>Average on time:</li>\n")
                    the_html.write("                <li>{}</li>\n".format(sim.config['dists']['host_on_time']['dist']))
                    for val in sim.config['dists']['host_on_time']['params']:
                        the_html.write("                <li>;{:.5e}</li>\n".format(val))

                the_html.write("          </ul>\n          <ul>\n")

                if param == 4:
                    the_html.write("                <li> {} </li>\n".format(str_param))
                    j = -1
                    for val in str_values:
                        j += 1
                        the_html.write("                <li>")
                        if j != 0:
                            the_html.write(";")
                        the_html.write("<a href=\"exec-{:03d}_param-{:02d}_round-{:02d}.html\"> {} </a></li>\n".format(counter, param, j,val))
                else:
                    the_html.write("                <li>Average off time:</li>\n")
                    the_html.write("                <li>{}</li>\n".format(sim.config['dists']['host_off_time']['dist']))
                    for val in sim.config['dists']['host_off_time']['params']:
                        the_html.write("                <li>;{:.5e}</li>\n".format(val))

                the_html.write("          </ul>\n")
                the_html.write("          <ul>\n")
                the_html.write("                <li><footer class=\"more\"><a href=\"#\">Read More &raquo;</a></footer></li>\n")
                the_html.write("          </ul>\n")
                the_html.write("        </figcaption>\n")
                the_html.write("      </figure>\n")
                the_html.write("    </section>\n")
                the_html.write("    <!-- main content -->\n")
                the_html.write("    <div id=\"intro\">\n")
                the_html.write("      <section class=\"clear\">\n")
                the_html.write("        <!-- Other parameter -->\n")
                the_html.write("        <article class=\"four_quarter lastbox\">\n")
                the_html.write("          <figure>\n")
                the_html.write("            <ul class=\"clear\">\n")

                if param != 0:
                    the_html.write("              <li>             <a href=\"{}\"><img src=\"{}\" width=\"220\" height=\"165\" alt=\"\"></a>\n".format(html0_name, fig0_name))
                    the_html.write("                               <a href=\"{}\">Number of elements</a>\n".format(html0_name))
                    the_html.write("              </li>\n")

                if param != 1:
                    the_html.write("              <li>             <a href=\"{}\"><img src=\"{}\" width=\"220\" height=\"165\" alt=\"\"></a>\n".format(html1_name, fig1_name))
                    the_html.write("                               <a href=\"{}\">Endogenous infection rate</a>\n".format(html1_name))
                    the_html.write("              </li>\n")

                if param != 2:
                    the_html.write("              <li>             <a href=\"{}\"><img src=\"{}\" width=\"220\" height=\"165\" alt=\"\"></a>\n".format(html2_name, fig2_name))
                    the_html.write("                               <a href=\"{}\">Exogenous infection rate</a>\n".format(html2_name))
                    the_html.write("              </li>\n")

                if param != 3:
                    if param == 4:
                        cl = " class=\"last>\""
                    else:
                        cl = ">            "
                    the_html.write("              <li{}<a href=\"{}\"><img src=\"{}\" width=\"220\" height=\"165\" alt=\"\"></a>\n".format(cl, html3_name, fig3_name))
                    the_html.write("                               <a href=\"{}\">Average on time</a>\n".format(html3_name))
                    the_html.write("              </li>\n")

                if param != 4:
                    the_html.write("              <li class=\"last\"><a href=\"{}\"><img src=\"{}\" width=\"220\" height=\"165\" alt=\"\"></a>\n".format(html4_name, fig4_name))
                    the_html.write("                               <a href=\"{}\">Average off time</a>\n".format(html4_name))
                    the_html.write("              </li>\n")


                the_html.write("            </ul>\n")
                the_html.write("            <figcaption><a href=\"index.html\">Return to home &raquo;</a></figcaption>\n")
                the_html.write("          </figure>\n")
                the_html.write("        </article>\n")
                the_html.write("      </section>\n")
                the_html.write("    </div>\n")
                the_html.write("    <!-- all simulations -->\n")
                the_html.write("    <!-- simulation 1 -->\n")

            # Mount index file:
            if param == 0:
                index_name = 'index.html'
                copy(_WEB_LOCAL_+ html_name, _WEB_LOCAL_+  index_name) # shutil

            # Body with graphs again
            with open(_WEB_LOCAL_+ html_name,"a") as the_html:
                the_html.write("    <div id=\"line_one\" >\n")
                the_html.write("      <section class=\"clear\">\n")
                the_html.write("        <!-- article 1 -->\n")
                the_html.write("        <article class=\"six_sixth\">\n")

            if param == 0:
                index_temp_name = 'index_temp.html'
                # Body with graphs again
                with open(_WEB_LOCAL_+ index_temp_name,"w") as the_index_html:
                    if (counter % 2) == 1 :
                        the_index_html.write("    <div id=\"line_one\">\n")
                    else:
                        the_index_html.write("    <div id=\"line_two\">\n")
                    the_index_html.write("      <section class=\"clear\">\n")
                    the_index_html.write("        <!-- article 1 -->\n")
                    the_index_html.write("        <article class=\"one_sixth\">\n")
                    the_index_html.write("          <h2> Simulation {:03d}</h2>\n".format(counter))
                    the_index_html.write("        </article>\n")
                    the_index_html.write("        <!-- Other parameter -->\n")
                    the_index_html.write("        <article class=\"five_sixth lastbox\">\n")
                    the_index_html.write("          <figure>\n")
                    the_index_html.write("            <ul class=\"clear\">\n")
                    the_index_html.write("              <li>             <a href=\"{}\"><img src=\"{}\" width=\"140\" height=\"105\" alt=\"Number of elements\"></a>\n".format(html0_name,fig0_name))
                    the_index_html.write("                               <a href=\"{}\">Number of elements</a>\n".format(html0_name))
                    the_index_html.write("              </li>\n")
                    the_index_html.write("              <li>             <a href=\"{}\"><img src=\"{}\" width=\"140\" height=\"105\" alt=\"Endogenous infection rate\"></a>\n".format(html1_name,fig1_name))
                    the_index_html.write("                               <a href=\"{}\">Endogenous infection rate</a>\n".format(html1_name))
                    the_index_html.write("              </li>\n")
                    the_index_html.write("              <li>             <a href=\"{}\"><img src=\"{}\" width=\"140\" height=\"105\" alt=\"Exogenous infection rate\"></a>\n".format(html2_name,fig2_name))
                    the_index_html.write("                               <a href=\"{}\">Exogenous infection rate</a>\n".format(html2_name))
                    the_index_html.write("              </li>\n")
                    the_index_html.write("              <li>             <a href=\"{}\"><img src=\"{}\" width=\"140\" height=\"105\" alt=\"Average on time\"></a>\n".format(html3_name,fig3_name))
                    the_index_html.write("                               <a href=\"{}\">Average on time</a>\n".format(html3_name))
                    the_index_html.write("              </li>\n")
                    the_index_html.write("              <li class=\"last\"><a href=\"{}\"><img src=\"{}\" width=\"140\" height=\"105\" alt=\"Average off time\"></a>\n".format(html4_name,fig4_name))
                    the_index_html.write("                               <a href=\"{}\">Average off time</a>\n".format(html4_name))
                    the_index_html.write("              </li>\n")
                    the_index_html.write("            </ul>\n")
                    the_index_html.write("          </figure>\n")
                    the_index_html.write("        </article>\n")
                    the_index_html.write("      </section>\n")
                    the_index_html.write("    </div>\n")

                # Insert index_temp in index_history
                index_history_name = 'index_history.html'
                with open(_WEB_LOCAL_+  index_history_name) as f:
                    with open(_WEB_LOCAL_+  index_temp_name, "a") as f1:
                        for line in f:
                            f1.write(line)
                # Save all History
                copy(_WEB_LOCAL_+  index_temp_name, _WEB_LOCAL_+  index_history_name) # shutil
                # Make index file html
                with open(_WEB_LOCAL_+  index_temp_name) as f:
                    with open(_WEB_LOCAL_+  index_name, "a") as f1:
                        for line in f:
                            f1.write(line)

            # Detail of execution
            with open(_WEB_LOCAL_+ web_temp_name) as f:
                with open(_WEB_LOCAL_+ html_name, "a") as f1:
                    for line in f:
                        f1.write(line)
                    f1.write("        </article>\n")
                    f1.write("      </section>\n")
                    f1.write("    </div>\n")

            # Foot HTML
            foot_html_name = 'foot.html'
            with open(_WEB_LOCAL_+ foot_html_name) as f:
                with open(_WEB_LOCAL_+ html_name, "a") as f1:
                    for line in f:
                        f1.write(line)
            if param == 0:
                with open(_WEB_LOCAL_+ foot_html_name) as f:
                    with open(_WEB_LOCAL_+  index_name, "a") as f1:
                        for line in f:
                            f1.write(line)

            copy(_WEB_LOCAL_+ html_name, _WEB_REMOTE_) # shutil
            if param == 0:
                copy(_WEB_LOCAL_+ index_name, _WEB_REMOTE_) # shutil

            ## Try to delete the temp file ##
            try:
                os.remove(_WEB_LOCAL_+ web_temp_name)
            except OSError as e:  ## if failed, report it back to the user ##
                print ("Error: %s - %s." % (e.filename, e.strerror))

if __name__ == '__main__':
    #start = time.time()
    start_time = datetime.now()
    results = main()
    #end = time.time()
    time_elapsed = datetime.now() - start_time
    print("Time elapsed: {0}".format(time_elapsed))
    sys.exit(results)
