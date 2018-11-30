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

import bots
import hosts
import targeting
import sim

from os import path
from datetime import datetime
from graph_results import show_results

DIST_EXPONENTIAL = 'Exponential'
DIST_UNIFORM = 'Uniform'

ROUNDS = 5
PARAMS = 5

PRINT_ROUND = True
PLOT_ROUND = False
PLOT_PARAM = True

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

    str_param = ''
    elem_param = 0
    tam = 0
    values = [0]

    for param in range(PARAMS):
        with open(opts.configfn, 'r') as fd:
            sim.config = json.load(fd)

        h_p_lst = list()
        i_p_lst = list()
        o_p_lst = list()
        a_p_lst = list()

        for rnd in range(ROUNDS):
            # change the parameters
            # Number of elements
            if param == 0:
                if rnd == 0:
                    tam = sim.config['maxhid']
                    values = np.linspace(sim.config['min']['maxhid'],sim.config['max']['maxhid'],ROUNDS,dtype=int)
                    str_param =  'number of elements'
                #sim.config['maxhid'] += rnd * tam
                sim.config['maxhid'] = values[rnd]
                elem_param = sim.config['maxhid']

            # Endogenous infection rate
            elif param == 1:
                if rnd == 0:
                    str_param = 'Endogenous infection rate'
                    values = np.linspace(sim.config['min']['bot']['params'][0],sim.config['max']['bot']['params'][0],ROUNDS,dtype=float)
                sim.config['bot']['params'][0] = values[rnd]
                elem_param = sim.config['bot']['params'][0]

            # Exogenous infection rate
            elif param == 2:
                if rnd == 0:
                    str_param = 'Exogenous infection rate'
                    values = np.linspace(sim.config['min']['bot']['master'][0],sim.config['max']['bot']['master'][0],ROUNDS,dtype=float)
                sim.config['bot']['master'][0] = values[rnd]
                elem_param = sim.config['bot']['master'][0]

            # Average host on time
            elif param == 3:
                if rnd == 0:
                    str_param = 'Average host on time'
                    values = np.linspace(   sim.config['min']['dists']['host_on_time']['params'][0],
                                            sim.config['max']['dists']['host_on_time']['params'][0],
                                            ROUNDS,
                                            dtype=float)
                sim.config['dists']['host_on_time']['params'][0] = values[rnd]
                elem_param = sim.config['dists']['host_on_time']['params'][0]

            # Average host off time
            elif param == 4:
                if rnd == 0:
                    str_param = 'Average host off time'
                    values = np.linspace(   sim.config['min']['dists']['host_off_time']['params'][0],
                                            sim.config['max']['dists']['host_off_time']['params'][0],
                                            ROUNDS,
                                            dtype=float)
                sim.config['dists']['host_off_time']['params'][0] = values[rnd]
                elem_param = sim.config['dists']['host_off_time']['params'][0]


            else:
                return -1


            # Normal execution from miraisim.py
            sim.dist_host_on_time = parse_dist(sim.config['dists']['host_on_time'], 'on-time')
            sim.dist_host_off_time = parse_dist(sim.config['dists']['host_off_time'], 'off-time')
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

            avgt_heal  = 0
            avgt_infec = 0
            avgt_off   = 0

            time_heal  = 0
            time_infec = 0
            time_off   = 0
            time_t     = 0

            time_b_heal  = 0
            time_b_infec = 0
            time_b_off   = 0
            time_b       = 0

            h_lst = list()
            i_lst = list()
            o_lst = list()

            ant_total = 0

            hist_bots = list()
            for j in range(sim.config['maxhid']+1):
                hist_bots.append(list())

            for hist in sim.count_history:
                (qtd_heal, qtd_inf, qtd_off, hour, hid, status, status_before) = hist
                i += 1
                now_total = qtd_heal + qtd_inf + qtd_off

                hist_bots[hid].append((hour, status))
                #print(hid)

                avgt_heal  += qtd_heal * (hour - time_b) * now_total
                avgt_infec += qtd_inf  * (hour - time_b) * now_total
                avgt_off   += qtd_off  * (hour - time_b) * now_total
                time_t += (hour - time_b) * now_total
                time_b = hour

                #if(now_total != sim.config['maxhid'] and now_total != ant_total):
                    #ant_total = now_total
                    #print('Total: {} \tMax: {} \tRound: {} \tCompleted time:{}%'.format(qtd_heal + qtd_inf + qtd_off, sim.config['maxhid'], i, hour*100.0 / sim.config['endtime']))

                if (hour > sim.config['endtime']/2):
                    # Extreme points
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
                    # Average calculates
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
                            avg_infec  += (qtd_inf * (hour - time_b_infec))
                            time_infec += (hour - time_b_infec)
                        else:
                            avg_heal  += (qtd_heal * (hour - time_b_heal))
                            time_heal  += (hour - time_b_heal)
                        o_lst.append((hour,qtd_heal, qtd_inf, qtd_off))

                    '''
                    str_evt = "Evt[{0:>3d}]".format(i)
                    str_qtd = "H:{0:>3d}[{1:>2.2f}%]\tI:{2:>3d}[{3:>2.2f}%]\tO:{4:>3d}[{5:>2.2f}%]\tT:{6:>3d}".format(qtd_heal, float(qtd_heal*100)/(sim.config['maxhid']+1) ,
                                                                                                                      qtd_inf , float(qtd_inf*100) /(sim.config['maxhid']+1) ,
                                                                                                                      qtd_off , float(qtd_off*100) /(sim.config['maxhid']+1) ,
                                                                                                                      qtd_heal+qtd_inf+qtd_off )
                    str_tim = "time:{0:>4.3f}".format(hour)
                    str_hid = "ID:{0:>4d}".format(hid)
                    print("{}\t{}\t{}\t{}\t{}".format(str_evt, str_tim, str_qtd, str_hid, str_status))
                    '''
                #hour_ant = hour
                else:
                    if (status == sim._SUSCETIBLE_):
                        time_b_heal   = hour
                        h_lst.append((hour,qtd_heal, qtd_inf, qtd_off))
                    elif(status == sim._INFECTED_):
                        time_b_infec = hour
                        i_lst.append((hour,qtd_heal, qtd_inf, qtd_off))
                    elif(status == sim._SHUTDOWN_):
                        time_b_off   = hour
                        o_lst.append((hour,qtd_heal, qtd_inf, qtd_off))


            # Average conclude
            #avg_all   = (avg_heal + avg_infec + avg_off) / (time_heal + time_infec + time_off)
            avg_heal  = avg_heal  / time_heal
            avg_infec = avg_infec / time_infec
            avg_off   = avg_off   / time_off
            avg_all   = avg_heal + avg_infec + avg_off

            avgt_heal  = avgt_heal  / time_t
            avgt_infec = avgt_infec / time_t
            avgt_off   = avgt_off   / time_t

            # Average unitary
            avg_unit_h = [0] * (sim.config['maxhid'] + 1)
            avg_unit_i = [0] * (sim.config['maxhid'] + 1)
            avg_unit_o = [0] * (sim.config['maxhid'] + 1)
            for k in range(sim.config['maxhid'] + 1):
                hist_uni = hist_bots[k]
                p = len(hist_uni)
                hist_uni.append((time_b,hist_uni[p-1][1]))
                tmp_unit_h = 0
                tmp_unit_i = 0
                tmp_unit_o = 0
                #print(k)
                time_base = hist_uni[0][0]
                time_befo = 0
                time_total = 0
                ih = 0
                ii = 0
                io = 0
                if   hist_uni[p][1] == sim._SUSCETIBLE_:
                    ih -= 1
                elif hist_uni[p][1] == sim._INFECTED_:
                    ii -= 1
                elif hist_uni[p][1] == sim._SHUTDOWN_:
                    io -= 1
                for uni in hist_uni:
                    (tmp_time,tmp_status) = uni
                    if tmp_status == sim._SUSCETIBLE_:
                        tmp_unit_h += tmp_time - time_befo
                        ih += 1
                    elif tmp_status == sim._INFECTED_:
                        tmp_unit_i += tmp_time - time_befo
                        ii += 1
                    elif tmp_status == sim._SHUTDOWN_:
                        tmp_unit_o += tmp_time - time_befo
                        io += 1
                    time_befo = tmp_time
                if ih > 0:
                    avg_unit_h[k] = float(tmp_unit_h) / ih
                if ii > 0:
                    avg_unit_i[k] = float(tmp_unit_i) / ii
                if io > 0:
                    avg_unit_o[k] = float(tmp_unit_o) / io

            # Print individuals average
            str_uni_average = ''
            for i in range(sim.config['maxhid'] + 1):
                str_temp = '{:>4d}|{:7.2f}|{:7.2f}|{:7.2f}|{:7.2f}'.format(i,avg_unit_h[i], avg_unit_i[i],avg_unit_o[i],avg_unit_h[i] + avg_unit_i[i] + avg_unit_o[i])
                str_uni_average = str_uni_average + '\t' + str_temp
                if ((i % 3) == 0):
                    str_uni_average = str_uni_average + '\n'
            print(str_uni_average)


            # Status time evolution
            h_prob = avg_heal  / sim.config['maxhid']
            i_prob = avg_infec / sim.config['maxhid']
            o_prob = avg_off   / sim.config['maxhid']
            a_prob = avg_all   / sim.config['maxhid']

            h_hst = np.array(h_lst)
            i_hst = np.array(i_lst)
            o_hst = np.array(o_lst)
            all_hst = np.array(sim.count_history)

            #Save parameters of round
            h_p_lst.append((rnd, elem_param, h_prob, avg_heal))
            i_p_lst.append((rnd, elem_param, i_prob, avg_infec))
            o_p_lst.append((rnd, elem_param, o_prob, avg_off))
            a_p_lst.append((rnd, elem_param, a_prob, avg_all))

            # Show the informations
            if PRINT_ROUND:
                # standard output
                if rnd == 0:
                    print('\n========================================================')
                    print(str_param)
                else:
                    print('========================================================')
                print("Parâmetro[{}]:{}: {} \t Round:{:>2d}".format(param+1,str_param, elem_param,rnd+1))
                print("\tmin \tmax \taverage \tprobability")
                print("heal:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format(h_min, h_max, avg_heal, h_prob))
                print("infec:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format(i_min, i_max, avg_infec, i_prob))
                print("off:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format(o_min, o_max, avg_off, o_prob))
                print("Total:\t- \t- \t{:8.4f}  \t{:>1.4f}".format(avg_all, a_prob))

                print("--------------------------------------------------------")
                print("\taverageT \tprobabilityT")
                print("heal:\t{:8.4f} \t{:>1.4f}".format( avgt_heal,  avgt_heal  / sim.config['maxhid']))
                print("infec:\t{:8.4f} \t{:>1.4f}".format(avgt_infec, avgt_infec / sim.config['maxhid']))
                print("off:\t{:8.4f} \t{:>1.4f}".format(  avgt_off,   avgt_off   / sim.config['maxhid']))
                print("Total:\t{:8.4f} \t{:>1.4f}".format(avgt_heal + avgt_infec + avgt_off, (avgt_heal  / sim.config['maxhid']) + (avgt_infec / sim.config['maxhid']) +(avgt_off/sim.config['maxhid'])))

            # Plotting
            if PLOT_ROUND:
                plt.plot(h_hst[:,0], h_hst[:,1]/sim.config['maxhid'], label='susceptible', color='b')
                plt.plot(i_hst[:,0], i_hst[:,2]/sim.config['maxhid'], label='infected'   , color='r')
                plt.plot(o_hst[:,0], o_hst[:,3]/sim.config['maxhid'], label='off'        , color='g')
                plt.plot(all_hst[:,3], (all_hst[:,0]+all_hst[:,1]+all_hst[:,2])/sim.config['maxhid'], label='total', color='y')
                plt.xlabel('time')
                plt.ylabel('proportion of')
                plt.ylim((0.0,1.5))
                plt.legend(loc='upper right')
                plt.savefig('graph/mirai_sim_c{:>03d}_ftr{:>03d}_rnd{:>03d}.pdf'.format(counter,param,rnd))
                #plt.show()
                plt.clf()

            sim.count_history = list()
            sim.heal_hosts = 0
            sim.infected_hosts = 0
            sim.off_hosts = 0
            sim.now = 0
            sim.evqueue = list()
            sim.evseq = 0
        # }}}
        h_p_hst = np.array(h_p_lst)
        i_p_hst = np.array(i_p_lst)
        o_p_hst = np.array(o_p_lst)
        a_p_hst = np.array(a_p_lst)


        if PLOT_PARAM:
            plt.plot(h_p_hst[:,1], h_p_hst[:,2], label='susceptible', color='b')
            plt.plot(i_p_hst[:,1], i_p_hst[:,2], label='infected'   , color='r')
            plt.plot(o_p_hst[:,1], o_p_hst[:,2], label='off'        , color='g')
            plt.plot(a_p_hst[:,1], a_p_hst[:,2], label='all'        , color='y')
            plt.xlabel(str_param)
            plt.ylabel('proportion of')
            plt.ylim((0.0,1.5))
            plt.legend(loc='upper right')
            plt.savefig('graph/mirai_sim_c{:>03d}_ftr{:>03d}.pdf'.format(counter,param,rnd))
            #plt.show()
            plt.clf()




if __name__ == '__main__':
    #start = time.time()
    start_time = datetime.now()
    results = main()
    #end = time.time()
    time_elapsed = datetime.now() - start_time
    print("Time elapsed: {0}".format(time_elapsed))
    sys.exit(results)
