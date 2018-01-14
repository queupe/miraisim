import logging
import sys

import sim

STATUS_SHUTDOWN = 'host_status_shutdown'
STATUS_SECURE = 'host_status_secure'
STATUS_VULNERABLE = 'host_status_vulnerable'
STATUS_INFECTED = 'host_status_infected'


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

    def __init__(self, hid, status):
        self.hid = hid
        self.status = status
        self.on_time = sim.dist_host_on_time()  # pylint: disable=not-callable
        self.infection_time = None
        self.bot = None

    def infect(self):
        logging.debug('hid %d', self.hid)
        assert self.status != STATUS_SECURE
        assert self.status != STATUS_SHUTDOWN
        if self.status == STATUS_INFECTED:
            return False
        else:
            self.status = STATUS_INFECTED
            self.infection_time = sim.now
            self.bot = sim.bot_factory(self.hid)  # pylint: disable=not-callable
            self.bot.start()
            return True

    def shutdown(self, _none):
        infection = sim.now
        if self.status == STATUS_INFECTED:
            self.bot.teardown()
            infection = self.infection_time
        logging.info('hid %d infected %f', self.hid,
                     (sim.now - infection)/self.on_time)
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
        return self.get(srchid, dsthid) * sim.config['nrtts_auth']

    def get_infect_delay(self, srchid, dsthid):
        return self.get(srchid, dsthid) * sim.config['nrtts_infect']

    def __str__(self):
        return 'E2ELatency min %f max %f timeout %f' % (self.min, self.max,
                                                        self.timeout)
# }}}
