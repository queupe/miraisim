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

ROUNDS = 10
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
    X_pos = 0

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
                    #values[-1] = 50000
                    str_param =  'number of elements'
                #sim.config['maxhid'] += rnd * tam
                sim.config['maxhid'] = values[rnd]
                elem_param = sim.config['maxhid']


            # Endogenous infection rate
            elif param == 1:
                if rnd == 0:
                    str_param = 'Endogenous infection rate'
                    values = np.logspace(np.log10(sim.config['min']['bot']['params'][0]),np.log10(sim.config['max']['bot']['params'][0]),ROUNDS, dtype=float)
                sim.config['bot']['params'][0] = values[rnd]
                elem_param = sim.config['bot']['params'][0]

            # Exogenous infection rate
            elif param == 2:
                if rnd == 0:
                    str_param = 'Exogenous infection rate'
                    values = np.logspace(np.log10(sim.config['min']['bot']['master'][0]),np.log10(sim.config['max']['bot']['master'][0]),ROUNDS,dtype=float)
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
            sim.dist_host_on_time  = parse_dist(sim.config['dists']['host_on_time'] , 'on-time')
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


            # Keep max and min
            h_max = 0
            i_max = 0
            o_max = 0

            h_min = sim.config['maxhid']
            i_min = sim.config['maxhid']
            o_min = sim.config['maxhid']

            # Count index
            i = 0
            h_i = 0
            i_i = 0
            o_i = 0

            # Average of all data
            avg_heal  = 0
            avg_infec = 0
            avg_off   = 0
            avg_all   = 0

            # Proportion of data (Average)
            avgt_heal  = 0
            avgt_infec = 0
            avgt_off   = 0

            # Past time in
            time_heal  = 0
            time_infec = 0
            time_off   = 0
            time_t     = 0

            time_b_heal  = 0
            time_b_infec = 0
            time_b_off   = 0
            time_b       = 0

            # Detachment history
            h_lst = list()
            i_lst = list()
            o_lst = list()

            ant_total = 0

            # History of each node (bots)
            hist_bots = list()
            for j in range(sim.config['maxhid']+1):
                hist_bots.append(list())


            for hist in sim.count_history:
                (qtd_heal, qtd_inf, qtd_off, hour, hid, status, status_before) = hist
                i += 1
                now_total = qtd_heal + qtd_inf + qtd_off

                hist_bots[hid].append((hour, status))

                # Protection to division by zero (0)
                if now_total > 0:
                    avg_heal   += (qtd_heal) * (hour - time_b)
                    avg_infec  += (qtd_inf ) * (hour - time_b)
                    avg_off    += (qtd_off ) * (hour - time_b)
                    avg_all    += (now_total)* (hour - time_b)
                    avgt_heal  += (qtd_heal / now_total) * (hour - time_b)
                    avgt_infec += (qtd_inf  / now_total) * (hour - time_b)
                    avgt_off   += (qtd_off  / now_total) * (hour - time_b)
                else:
                    avgt_heal  += 0
                    avgt_infec += 0
                    avgt_off   += 0

                time_t += (hour - time_b)
                time_b = hour

                # Debuging the code
                #if(now_total != sim.config['maxhid'] and now_total != ant_total):
                #    ant_total = now_total
                #    print('Total: {} \tMax: {} \tRound: {} \tCompleted time:{}%'.format(qtd_heal + qtd_inf + qtd_off, sim.config['maxhid'], i, hour*100.0 / sim.config['endtime']))

                # Get max and min
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



            # Average conclude
            #avg_all   = (avg_heal + avg_infec + avg_off) / (time_heal + time_infec + time_off)
            '''
            if time_heal > 0:
                avg_heal  = avg_heal  / time_heal
            else:
                avg_heal  = 0
            if time_infec > 0:
                avg_infec = avg_infec / time_infec
            else:
                avg_infec = 0
            if time_off > 0:
                avg_off   = avg_off   / time_off
            else:
                avg_off   = 0
            avg_all   = avg_heal + avg_infec + avg_off
            '''
            if time_t > 0:
                avg_heal   = avg_heal   / time_t
                avg_infec  = avg_infec  / time_t
                avg_off    = avg_off    / time_t
                avg_all    = avg_all    / time_t

                avgt_heal  = avgt_heal  / time_t
                avgt_infec = avgt_infec / time_t
                avgt_off   = avgt_off   / time_t
            else:
                avgt_heal  = 0
                avgt_infec = 0
                avgt_off   = 0

            avgt_all   = avgt_heal + avgt_infec + avgt_off

            # Average for each bot
            avg_unit_h = [0] * (sim.config['maxhid'] + 1)
            avg_unit_i = [0] * (sim.config['maxhid'] + 1)
            avg_unit_o = [0] * (sim.config['maxhid'] + 1)
            avg_btwn_h = [0] * (sim.config['maxhid'] + 1)
            avg_btwn_i = [0] * (sim.config['maxhid'] + 1)
            avg_btwn_o = [0] * (sim.config['maxhid'] + 1)
            avg_btwn_a_h = 0
            avg_btwn_a_i = 0
            num_h =      [0] * (sim.config['maxhid'] + 1)
            num_i =      [0] * (sim.config['maxhid'] + 1)
            num_o =      [0] * (sim.config['maxhid'] + 1)

            for k in range(sim.config['maxhid'] + 1):
                hist_uni = hist_bots[k]

                # insert the last event to close history
                # The time_b is the last time before
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

                # Ajust because the last event inserted doesn't change the status
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
                    avg_unit_h[k] = float(tmp_unit_h)
                    num_h[k] = ih
                if ii > 0:
                    avg_unit_i[k] = float(tmp_unit_i)
                    num_i[k] = ii
                if io > 0:
                    avg_unit_o[k] = float(tmp_unit_o)
                    num_o[k] = io

            # Average between events
            avg_unit_array_h = np.array(avg_unit_h[1:])
            num_h_array = np.array(num_h[1:])
            avg_unit_array_i = np.array(avg_unit_i[1:])
            num_i_array = np.array(num_i[1:])
            avg_unit_array_o = np.array(avg_unit_o[1:])
            num_o_array = np.array(num_o[1:])

            time_btw_h= (( np.sum(avg_unit_array_i)) /
                        ( np.sum(num_i_array)))
            time_btw_i= (( np.sum(avg_unit_array_h) + np.sum(avg_unit_array_o)) /
                        ( np.sum(num_h_array)      + np.sum(num_o_array)))

            # Print individuals average


            '''
            print('Average:    |{:7.2f}/{:4.2f}|{:7.2f}/{:4.2f}|{:7.2f}/{:4.2f}|{:7.2f}'.format(
                            np.sum(avg_unit_array_h)/np.sum(np.array(num_h)), np.mean(np.array(num_h)),
                            np.sum(avg_unit_array_i)/np.sum(np.array(num_i)), np.mean(np.array(num_i)),
                            np.sum(avg_unit_array_o)/np.sum(np.array(num_o)), np.mean(np.array(num_o)),
                            np.sum(avg_unit_array_h)/np.sum(np.array(num_h))+
                            np.sum(avg_unit_array_i)/np.sum(np.array(num_i))+
                            np.sum(avg_unit_array_o)/np.sum(np.array(num_o))
            ))

            print('Probab:     |{:7.2f}/{:4.2f}|{:7.2f}/{:4.2f}|{:7.2f}/{:4.2f}'.format(
                            np.sum(avg_unit_array_h)/np.sum(np.array(num_h))/avg_unit_array_i[0], np.mean(np.array(num_h)),
                            np.sum(avg_unit_array_i)/np.sum(np.array(num_i))/avg_unit_array_i[0], np.mean(np.array(num_i)),
                            np.sum(avg_unit_array_o)/np.sum(np.array(num_o))/avg_unit_array_i[0], np.mean(np.array(num_o))
            ))
            '''


            #Save parameters of round
            h_p_lst.append((rnd, elem_param, avgt_heal))
            i_p_lst.append((rnd, elem_param, avgt_infec))
            o_p_lst.append((rnd, elem_param, avgt_off))
            a_p_lst.append((rnd, elem_param, avgt_all))

            # Show the informations
            if PRINT_ROUND:
                # standard output
                if rnd == 0:
                    print('\n========================================================')
                    print(str_param)
                else:
                    print('========================================================')
                print("Parâmetro[{}]:{}: {} \t Round:{:>2d}".format(param+1,str_param, elem_param,rnd+1))
                print("\tmin \tmax \taverage \tproportion")
                print("heal:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format (h_min, h_max, avg_heal,  avgt_heal))
                print("infec:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format(i_min, i_max, avg_infec, avgt_infec))
                print("off:\t{} \t{} \t{:8.4f} \t{:>1.4f}".format  (o_min, o_max, avg_off,   avgt_off))
                print("All :\t- \t- \t{:8.4f}  \t{:>1.4f}".format (avg_all, avgt_all))
                print("Average of time between heal  : {:10.3f}".format(time_btw_h))
                print("Average of time between infect: {:10.3f}".format(time_btw_i))
                print("Tx infect.....................: {:10.7f}".format(1/time_btw_h))
                print("Tx Heal.......................: {:10.7f}".format(1/time_btw_i))
                print("Attempt to infect endogenous..: {:d}".format(sim.attempt_infected_endogeno))
                print("Attempt to infect exogenous...: {:d}".format(sim.attempt_infected_exogeno))
                print("Tx attempt to infect end......: {:10.7f}".format(float(sim.attempt_infected_endogeno)/(sim.config["maxhid"]*time_befo)))
                print("Tx attempt to infect exo......: {:10.7f}".format(float(sim.attempt_infected_exogeno)/time_befo))

                print("|ID!Sus Time/Sus qtd!Inf Time/Inf qtd!Off Time/Off qtd!Total|")
                str_uni_average = ''
                for i in range(sim.config['maxhid']):
                    str_temp = '|{:>4d}!{:7.2f}/{:4d}!{:7.2f}/{:4d}!{:7.2f}/{:4d}!{:7.2f}|'.format(i+1,
                                avg_unit_array_h[i], num_h[i],
                                avg_unit_array_i[i], num_i[i],
                                avg_unit_array_o[i], num_o[i],
                                avg_unit_array_h[i] + avg_unit_array_i[i] + avg_unit_array_o[i])
                    str_uni_average = str_uni_average + '\t' + str_temp
                    if (((i+1) % 2) == 0):
                        str_uni_average = str_uni_average + '\n'
                print(str_uni_average)

                # file output
                filename ='graph/mirai_sim_coun{:>03d}_param{:>03d}_{}'.format(counter,param,str_param)
                if rnd == 0:
                    #print('Starting writing in file: \'{}.txt\''.format(filename))
                    with open(filename + '.txt', 'w') as the_file:
                        the_file.write('Execution number: {:3d}\n'.format(counter))
                        the_file.write('Parameter tested: {}\n'.format(str_param))
                        the_file.write('\n========================================================\n')

                with open(filename + '.txt', 'a') as the_file:
                    the_file.write('========================================================\n')
                    the_file.write("Parameters[{}]:{}: {} \t Round:{:>2d}\n".format(param+1,str_param, elem_param,rnd+1))
                    the_file.write('Total of hosts...........: {:3d}\n'.format(sim.config['maxhid']))
                    the_file.write('Endogenous infection rate: {:10.7f}\n'.format(sim.config['bot']['params'][0]))
                    the_file.write('Exogenous infection rate.: {:10.7f}\n'.format(sim.config['bot']['master'][0]))
                    the_file.write('Host on time.............: {:10.3f} - {}\n'.format(sim.config['dists']['host_on_time']['params'][0],sim.config['dists']['host_on_time']['dist']))
                    the_file.write('Host off time............: {:10.3f} - {}\n'.format(sim.config['dists']['host_off_time']['params'][0],sim.config['dists']['host_off_time']['dist']))

                    the_file.write("\tmin \tmax \taverage \tproportion\n")
                    the_file.write("heal:\t{} \t{} \t{:8.4f} \t{:>1.4f}\n".format (h_min, h_max, avg_heal,  avgt_heal))
                    the_file.write("infec:\t{} \t{} \t{:8.4f} \t{:>1.4f}\n".format(i_min, i_max, avg_infec, avgt_infec))
                    the_file.write("off:\t{} \t{} \t{:8.4f} \t{:>1.4f}\n".format  (o_min, o_max, avg_off,   avgt_off))
                    the_file.write("All :\t- \t- \t{:8.4f}  \t{:>1.4f}\n".format (avg_all, avgt_all))
                    the_file.write("Average of time between heal  : {:10.3f}\n".format(time_btw_h))
                    the_file.write("Average of time between infect: {:10.3f}\n".format(time_btw_i))
                    the_file.write("Tx infect.....................: {:10.7f}\n".format(1/time_btw_h))
                    the_file.write("Tx Heal.......................: {:10.7f}\n".format(1/time_btw_i))
                    the_file.write("Attempt to infect endogenous..: {:5d}\n".format(sim.attempt_infected_endogeno))
                    the_file.write("Attempt to infect exogenous...: {:5d}\n".format(sim.attempt_infected_exogeno))
                    the_file.write("Tx attempt to infect end......: {:10.7f}\n".format(float(sim.attempt_infected_endogeno)/(sim.config["maxhid"]*time_befo)))
                    the_file.write("Tx attempt to infect exo......: {:10.7f}\n".format(float(sim.attempt_infected_exogeno)/time_befo))
                    the_file.write("|ID!Sus Time/Sus qtd!Inf Time/Inf qtd!Off Time/Off qtd!Total|")
                    the_file.write("{}\n".format(str_uni_average))



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
            #plt.text(values[0],1.45,"Final settings:")
            #plt.text(values[0],1.40,"Hosts: {}".format(sim.config['maxhid']))
            #plt.text(values[0],1.35,"End infection rate: {}".format(sim.config['bot']['params'][0]))
            #plt.text(values[0],1.30,"Exo infection rate: {}".format(sim.config['bot']['master'][0]))
            #plt.text(values[0],1.25,"Host on time: {}".format(sim.config['dists']['host_on_time']['params'][0]))
            plt.legend(loc='upper right')
            filename ='graph/mirai_sim_coun{:>03d}_param{:>03d}_{}'.format(counter,param,str_param)
            plt.savefig(filename + '.png')
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
