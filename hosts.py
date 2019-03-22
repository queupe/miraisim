import logging
import sys

import sim

STATUS_SHUTDOWN = 'host_status_shutdown'
STATUS_SECURE = 'host_status_secure'
STATUS_VULNERABLE = 'host_status_vulnerable'
STATUS_INFECTED = 'host_status_infected'
STATUS_INFECTED_END = 'host_status_endogenous_infected'
STATUS_INFECTED_EXO = 'host_status_exogenous_infected'

# Testing 2 new branch
# We only create hosts for vulnerable and infected (online) devices.
# Secure and shut-down devices are handled without in-memory objects.
class Host(object):  # {{{
    @staticmethod
    def bootup(hid):
        host = Host(hid, STATUS_VULNERABLE)
        logging.info('hid %d on_time %f', hid, host.on_time)
        sim.host_tracker.add(host)
        ev = (sim.now + host.on_time, host.shutdown, None)
        sim.enqueue(ev)
        sim.add_on_host(hid)

    def __init__(self, hid, status):
        self.hid = hid
        self.status = status
        self.on_time = sim.dist_host_on_time()  # pylint: disable=not-callable
        self.infection_time = None
        self.bot = None

    def infect(self, from_hid = -1):
        logging.debug('hid %d', self.hid)
        assert self.status != STATUS_SECURE
        assert self.status != STATUS_SHUTDOWN
        if self.status == STATUS_INFECTED or self.status == STATUS_INFECTED_END or self.status == STATUS_INFECTED_EXO:
            return False
        else:
            self.status = STATUS_INFECTED
            if from_hid == 0:
                self.status = STATUS_INFECTED_EXO
            if from_hid > 0:
                self.status = STATUS_INFECTED_END

            self.infection_time = sim.now
            self.bot = sim.bot_factory(self.hid)  # pylint: disable=not-callable
            self.bot.start()
            sim.add_infected_host(self.hid, from_hid)
            return True

    def master_infect (self, from_hid = -1):
        self.status = STATUS_INFECTED_EXO
        self.infection_time = sim.now
        self.bot = sim.master_bot_factory(self.hid)  # pylint: disable=not-callable
        self.bot.master_start()
        sim.add_infected_host(self.hid, from_hid)
        return True

    def shutdown(self, _none):
        infection = sim.now
        if self.status == STATUS_INFECTED or self.status == STATUS_INFECTED_END or self.status == STATUS_INFECTED_EXO:
            self.bot.teardown()
            infection = self.infection_time
        logging.info('hid %d on_time %f infected %f', self.hid, self.on_time,
                     (sim.now - infection)/self.on_time)
        #Add by Vilc - August, 09, 2018
        # Modified Jan 17, 2019
        status_infected = sim._SUSCETIBLE_
        if self.status == STATUS_INFECTED:
            status_infected = sim._INFECTED_
        elif self.status == STATUS_INFECTED_END:
            status_infected = sim._INFECTED_END_
        elif self.status == STATUS_INFECTED_EXO:
            status_infected = sim._INFECTED_EXO_

        sim.add_off_host(self.hid, status_infected, self.on_time, sim.now - infection)

        off_time = sim.dist_host_off_time()  # pylint: disable=not-callable
        ev = (sim.now + off_time, Host.bootup, self.hid)
        sim.enqueue(ev)
        sim.host_tracker.delete(self)
# }}}


class HostTracker(object):  # {{{
    def __init__(self, config):
        frac_vulnerable = float(config['frac_vulnerable'])
        self.vulnerable_period = int(1.0/frac_vulnerable)
        self.hid2host = dict()

    def get(self, hid):
        if (hid % self.vulnerable_period) != 0:
            return None, STATUS_SECURE
        if hid not in self.hid2host:
            return None, STATUS_SHUTDOWN
        else:
            host = self.hid2host[hid]
            return host, host.status

    def add(self, host):
        assert (host.hid % self.vulnerable_period) == 0
        assert host.hid not in self.hid2host
        self.hid2host[host.hid] = host
        #print('HostTracker {:d}\n'.format(host.hid))

    def delete(self, host):
        assert host.hid in self.hid2host
        del self.hid2host[host.hid]

    def __str__(self):
        return 'HostTracker: period %d online %d' % (self.vulnerable_period,
                                                     len(self.hid2host))
# }}}


class E2ELatency(object):  # {{{
    def __init__(self, config):
        self.min = float(config['e2e_latency']['min'])
        self.max = float(config['e2e_latency']['max'])
        assert self.max >= self.min
        self.timeout = float(config['e2e_latency']['timeout'])

    def get(self, srchid, dsthid):
        if srchid == dsthid:
            return self.min
        h = abs(hash('%d.%d' % (srchid, dsthid)))
        scale = h/sys.maxsize
        latency = scale*(self.max - self.min) + self.min
        logging.debug('E2ELatency src %d dst %d scale %f lat %f',
                      srchid, dsthid, scale, latency)
        return latency

    def get_timeout(self):
        return self.timeout

    def get_auth_delay(self, srchid, dsthid):
        #print(srchid, dsthid, sim.config['nrtts_auth'])
        return self.get(srchid, dsthid) * sim.config['nrtts_auth']

    def get_infect_delay(self, srchid, dsthid):
        return self.get(srchid, dsthid) * sim.config['nrtts_infect']

    def __str__(self):
        return 'E2ELatency min %f max %f timeout %f' % (self.min, self.max,
                                                        self.timeout)
# }}}
