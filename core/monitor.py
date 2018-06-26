import sys
import os
import radix
import traceback
# from taps.bgpmon import BGPmon
from subprocess import Popen


class Monitor():

    def __init__(self, confparser):
        self.prefix_tree = radix.Radix()
        self.process_ids = list()
        self.flag = False
        self.confparser = confparser

    def start(self):
        if not self.flag:
            configs = self.confparser.get_obj()
            for config in configs:
                try:
                    for prefix in configs[config]['prefixes']:
                        node = self.prefix_tree.add(prefix.with_prefixlen)
                        node.data['origin_asns'] = configs[
                            config]['origin_asns']
                        node.data['neighbors'] = configs[config]['neighbors']
                        node.data['mitigation'] = configs[
                            config]['mitigation']
                except Exception as e:
                    traceback.print_exc()
            prefixes = self.prefix_tree.prefixes()
            # Code here later to implement filter of monitors
            self.init_ris_instances(prefixes)
            # self.init_bgpmon_instance(prefixes)
            self.init_exabgp_instance(prefixes)
            self.init_bgpstreamhist_instance(prefixes)
            self.init_bgpstreamlive_instance(prefixes)
            self.flag = True
            print('Monitors Started...')

    def stop(self):
        if self.flag:
            for proc_id in self.process_ids:
                proc_id[1].terminate()
            self.flag = False
            print('Monitors Stopped...')

    def init_ris_instances(self, prefixes):
        try:
            monitors = self.confparser.get_monitors()
            if 'riperis' in monitors:
                for prefix in prefixes:
                    for ris_monitor in monitors['riperis']:
                        p = Popen(['nodejs', 'taps/ripe_ris.js',
                                   '--prefix', prefix, '--host', ris_monitor])
                        self.process_ids.append(('RIPEris', p))
        except Exception as e:
            traceback.print_exc()

    # def init_bgpmon_instance(self, prefixes):
    #   try:
    #       if(len(self.confparser.get_monitors()['bgpmon']) == 1):
    #           p = Process(target=BGPmon, args=(self.prefix_tree, self.raw_log_queue, self.confparser.get_monitors()['bgpmon'][0]))
    #           p.start()
    #           self.process_ids.append(('BGPmon', p))
    #   except:
    #       print('Error on initializing of BGPmon.')

    def init_exabgp_instance(self, prefixes):
        try:
            monitors = self.confparser.get_monitors()
            if 'exabgp' in monitors and len(monitors['exabgp']) > 0:
                for exabgp_monitor in monitors['exabgp']:
                    prefixes = self.prefix_tree.prefixes()
                    exabgp_monitor_str = exabgp_monitor[0] + ':' +  str(exabgp_monitor[1])
                    p = Popen(['python3', 'taps/exabgp_client.py',
                        '--prefix', ','.join(prefixes), '--host', exabgp_monitor_str])
                    self.process_ids.append(('ExaBGP', p))
        except Exception as e:
            traceback.print_exc()

    def init_bgpstreamhist_instance(self, prefixes):
        try:
            monitors = self.confparser.get_monitors()
            if 'bgpstreamhist' in monitors:
                prefixes = self.prefix_tree.prefixes()
                bgpstreamhist_dir = monitors['bgpstreamhist']
                p = Popen(['python3', 'taps/bgpstreamhist.py',
                        '--prefix', ','.join(prefixes), '--dir', bgpstreamhist_dir])
                self.process_ids.append(('BGPStreamHist', p))
        except Exception as e:
            traceback.print_exc()

    def init_bgpstreamlive_instance(self, prefixes):
        try:
            monitors = self.confparser.get_monitors()
            if 'bgpstreamlive' in monitors:
                prefixes = self.prefix_tree.prefixes()
                bgpstream_projects = ','.join(monitors['bgpstreamlive'])
                p = Popen(['python3', 'taps/bgpstreamlive.py',
                        '--prefix', ','.join(prefixes), '--mon_projects', bgpstream_projects])
                self.process_ids.append(('BGPStreamLive', p))
        except Exception as e:
            traceback.print_exc()
