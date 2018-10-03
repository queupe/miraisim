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

AMOUNT = 15
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

    lst_prop_infec = list()
    lst_prop_infec_min = list()
    lst_prop_infec_max = list()
    #prop_heal = list()
    lst_avg = list()

    # Testing parameters
    parameters_end = True
    param_index = -1
    amount_index = -1
    bkp_value = 0
    str_title = ''
    str_xlabel = ''
    run = True

    while parameters_end:

        param_index += 1
        amount_index += 1
        # Testing parameters
        #---------------------------------------------------------------------
        # Endtime
        if(param_index == 0):
            if (sim.config['endtime'] != sim.config['max']['endtime']):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['endtime'],sim.config['max']['endtime'], AMOUNT)
                    bkp_value = sim.config['endtime']
                    str_title = "Exploring the end time"
                    str_xlabel = "End Time"
                sim.config['endtime'] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['endtime']
                print('Endtime is equal')
        #---------------------------------------------------------------------
        # maxid
        elif(param_index == 2):
            sim.config['endtime'] = bkp_value
            if (sim.config['maxhid'] != sim.config['max']['maxhid']):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['maxhid'],sim.config['max']['maxhid'], AMOUNT)
                    bkp_value = sim.config['maxhid']
                    str_title = "Exploring the number of susceptibles"
                    str_xlabel = "susceptibles"
                sim.config['maxhid'] = e_amount[amount_index]
                print('Max id:{}'.format(sim.config['maxhid']))
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['maxhid']
                print('Number of user is equal')
        #---------------------------------------------------------------------
        # frac_vulnerable
        elif(param_index == 3):
            sim.config['maxhid'] = bkp_value
            if (sim.config['frac_vulnerable'] != sim.config['max']['frac_vulnerable']):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['frac_vulnerable'],sim.config['max']['frac_vulnerable'], AMOUNT)
                    bkp_value = sim.config['frac_vulnerable']
                    str_title = "Exploring the proportion of vulnerable"
                    str_xlabel = "Vulnerable proportion"
                sim.config['frac_vulnerable'] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['frac_vulnerable']
                print('Fraction of vulnerable is equal')
        #---------------------------------------------------------------------
        # number of rtt auth
        elif(param_index == 4):
            sim.config['frac_vulnerable'] = bkp_value
            if (sim.config['nrtts_auth'] != sim.config['max']['nrtts_auth']):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['nrtts_auth'],sim.config['max']['nrtts_auth'], AMOUNT)
                    bkp_value = sim.config['nrtts_auth']
                    str_title = "Exploring the number of RTT to authentication"
                    str_xlabel = "Number of RTT"
                sim.config['nrtts_auth'] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['nrtts_auth']
        #---------------------------------------------------------------------
        # number of rtt infect
        elif(param_index == 5):
            sim.config['nrtts_auth'] = bkp_value
            if (sim.config['nrtts_infect'] != sim.config['max']['nrtts_infect']):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['nrtts_infect'],sim.config['max']['nrtts_infect'], AMOUNT)
                    bkp_value = sim.config['nrtts_infect']
                    str_title = "Exploring the number of RTT to authentication"
                    str_xlabel = "Number of RTT"
                sim.config['nrtts_auth'] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['nrtts_infect']
        #---------------------------------------------------------------------
        # Endogenous infection rate
        elif(param_index == 6):
            sim.config['nrtts_infect'] = bkp_value
            if (sim.config['bot']['params'][0] != sim.config['max']['bot']['params'][0]):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['bot']['params'][0],sim.config['max']['bot']['params'][0], AMOUNT)
                    bkp_value = sim.config['bot']['params']
                    str_title = "Exploring the endogenous infection rate"
                    str_xlabel = "Endogenous infection rate"
                sim.config['bot']['params'][0] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['bot']['params']
        #---------------------------------------------------------------------
        # Exogenous infection rate
        elif(param_index == 7):
            sim.config['bot']['params'] = bkp_value
            if (sim.config['bot']['master'][0] != sim.config['max']['bot']['master'][0]):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['bot']['master'][0],sim.config['max']['bot']['master'][0], AMOUNT)
                    bkp_value = sim.config['bot']['master']
                    str_title = "Exploring the exogenous infection rate"
                    str_xlabel = "Exogenous infection rate"
                sim.config['bot']['master'][0] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['bot']['master']
        #---------------------------------------------------------------------
        # Host on time
        elif(param_index == 8):
            sim.config['bot']['params'] = bkp_value
            if (sim.config['dists']['host_on_time']['params'][0] != sim.config['dists']['host_on_time']['params'][0]):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['dists']['host_on_time']['params'][0],sim.config['dists']['host_on_time']['params'][0], AMOUNT)
                    bkp_value = sim.config['dists']['host_on_time']['params'][0]
                    str_title = "Exploring the exogenous infection rate"
                    str_xlabel = "Exogenous infection rate"
                sim.config['dists']['host_on_time']['params'][0] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['dists']['host_on_time']['params'][0]
        #---------------------------------------------------------------------
        # Host off time
        elif(param_index == 9):
            sim.config['dists']['host_on_time']['params'][0] = bkp_value
            if (sim.config['dists']['host_off_time']['params'][0] != sim.config['dists']['host_off_time']['params'][0]):
                if(amount_index == 0):
                    e_amount = np.logspace(sim.config['dists']['host_off_time']['params'][0],sim.config['dists']['host_off_time']['params'][0], AMOUNT)
                    bkp_value = sim.config['dists']['host_off_time']['params'][0]
                    str_title = "Exploring the exogenous infection rate"
                    str_xlabel = "Exogenous infection rate"
                sim.config['dists']['host_off_time']['params'][0] = e_amount[amount_index]
                if(amount_index == AMOUNT):
                    amount_index = -1
                    param_index += 1
                else:
                    amount_index += 1
            else:
                run = False
                amount_index = -1
                param_index += 1
                bkp_value = sim.config['dists']['host_off_time']['params'][0]
        #---------------------------------------------------------------------
        # End cicle
        elif(param_index > 9):
            parameters_end = False

        # Starting
        if (parameters_end and run):
            logging.info('Starting round: {0:>2d}'.format(amount_index))
            if param_index != 7:
                sim.dist_host_on_time = parse_dist(sim.config['dists']['host_on_time'],'on-time')
            if param_index != 8:
                sim.dist_host_off_time = parse_dist(sim.config['dists']['host_off_time'], 'off-time')

            logging.info('initialized on/off time distributions')

            print('--------------------------')
            print('Round {0:>3d}'.format(amount_index))
            print(str_title)

            sim.targeting_factory = targeting.create_factory(sim.config)
            logging.info('%s', sim.targeting_factory)
            print('sim.targeting_factory')
            print(sim.targeting_factory)

            sim.bot_factory = bots.create_factory(sim.config)
            logging.info('%s', sim.bot_factory)
            print('sim.bot_factory')
            print(sim.bot_factory)

            sim.host_tracker = hosts.HostTracker(sim.config)
            logging.info('%s', sim.host_tracker)
            print('sim.host_tracker')
            print(sim.host_tracker)

            sim.e2e_latency = hosts.E2ELatency(sim.config)
            logging.info('%s', sim.e2e_latency)
            print('sim.e2e_latency')
            print(sim.e2e_latency)

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
                (qtd, hour, hid, status) = hist
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
                (qtd, hour, hid, status) = hist
                if (hour > sim.config['endtime']/2):
                    hour_tot += hour - hour_ant
                    dev_std += ((qtd - avg_local)**2)*(hour - hour_ant)

            var_local = np.sqrt(dev_std / hour_tot)

            #for hist in sim.count_heal

            if amount_index == 0:
                lst_prop_infec = list()
                lst_prop_infec_min = list()
                lst_prop_infec_max = list()
                #prop_heal = list()
                lst_avg = list()

            lst_prop_infec.append(avg_local/sim.config['maxhid'])
            lst_prop_infec_min.append(float(min)/sim.config['maxhid'])
            lst_prop_infec_max.append(float(max)/sim.config['maxhid'])
            #lst_prop_heal.append()
            lst_avg.append(avg_local)
            print("Infect min: {0:>2.4f} \tmax   : {1:>2.4f}".format(float(min)/sim.config['maxhid'], float(max)/sim.config['maxhid']))
            print("Prob infec: {0:>2.4f} \tTotal : {1:>4d}".format(avg_local/sim.config['maxhid'], sim.config['maxhid']))
            print("Proportion infec: {0:>2.4f} \theal  : {1:>2.4f}".format(avg_weight, avg_weight))
            print("Average   : {0:>2.4f} \tStd dv: {1:>4.2f}\n".format(avg_local, var_local))

            if amount_index == -1:
                plt.plot(range(len(lst_prop_infec)),np.array(lst_prop_infec), label='infec')
                plt.plot(range(len(lst_prop_infec_min)),np.array(lst_prop_infec), label='infec min')
                plt.plot(range(len(lst_prop_infec_max)),np.array(lst_prop_infec), label='infec max')
                plt.savefig('graph/mirai_sim_{:>03}.pdf'.format(param_index))

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
        elif(not run):
            run = True
# }}}


if __name__ == '__main__':
    start = time.time()
    results = main()
    end = time.time()
    print("Time elapsed: {0:>4.3f}".format(end - start))
    sys.exit(results)
