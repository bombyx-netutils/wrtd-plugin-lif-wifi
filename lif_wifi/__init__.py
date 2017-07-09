#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import logging
import subprocess


def get_plugin_list():
    return [
        "wifi",
    ]


def get_plugin(name):
    if name == "wifi":
        return _PluginObject()
    else:
        assert False


class _PluginObject:

    def init2(self, instanceName, cfg, tmpDir, varDir):
        assert instanceName == ""
        self.cfg = cfg
        self.tmpDir = tmpDir
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self.wifiNetworks = []
        for o in self.cfg:
            t = _WrtConfigWifiNetwork()
            t.ssid = o["ssid"]
            if "password" in o:
                t.password = o["password"]
            else:
                t.password = ""
            self.wifiNetworks.append(t)

        self.hostapdProcDict = dict()

    def start(self):
        self.logger.info("Started.")

    def stop(self):
        for ifname in list(self.hostapdProcDict.keys()):        # self.hostapdProcDict changed in loop
            self._stopHostapd(ifname)
            self.logger.info("Interface \"%s\" unmanaged." % (ifname))
        self.logger.info("Stopped.")

    def interface_appear(self, bridge, ifname):
        if ifname.startswith("wl"):
            self._runHostapd(bridge.get_name(), ifname)
            self.logger.info("Interface \"%s\" managed." % (ifname))
            return True
        else:
            return False

    def interface_disappear(self, ifname):
        if ifname in self.hostapdProcDict:
            self._stopHostapd(ifname)
            self.logger.info("Interface \"%s\" unmanaged." % (ifname))

    def _runHostapd(self, brname, wlanIntf):
        if len(self.wifiNetworks) == 0:
            return

        cfgFile = os.path.join(self.tmpDir, "hostapd-%s.conf" % (wlanIntf))
        pidFile = os.path.join(self.tmpDir, "hostapd-%s.pid" % (wlanIntf))

        # generate hostapd configuration file
        buf = ""
        buf += "interface=%s\n" % (wlanIntf)
        buf += "bridge=%s\n" % (brname)
        buf += "\n"
        buf += "# hardware related configuration\n"
        buf += self._genWlanAdapterHwCfg(wlanIntf, True)
        buf += "\n"
        for j in range(0, len(self.wifiNetworks)):
            wifiNet = self.wifiNetworks[j]
            buf += "# AP %d\n" % (j + 1)
            if j > 0:
                buf += "bss=%s.%d" % (wlanIntf, j + 1)      # new interface that hostapd will create for this AP
            buf += "ssid=%s\n" % (wifiNet.ssid)
            if wifiNet.password != "":
                buf += "auth_algs=1\n"                      # WPA only, WEP disallowed
                buf += "wpa=2\n"                            # WPA2 only
                buf += "wpa_key_mgmt=WPA-PSK\n"
                buf += "rsn_pairwise=CCMP\n"
                buf += "wpa_passphrase=%s\n" % (wifiNet.password)
        buf += "\n"
        buf += "eap_server=0\n"

        try:
            # write to hostapd configuration file
            with open(cfgFile, "w") as f:
                f.write(buf)

            # run hostapd process
            cmd = "/usr/sbin/hostapd"
            cmd += " -P %s" % (pidFile)
            cmd += " %s" % (cfgFile)
            self.hostapdProcDict[wlanIntf] = subprocess.Popen(cmd, shell=True, universal_newlines=True)
        except:
            if os.path.exists(cfgFile):
                os.unlink(cfgFile)
            if os.path.exists(pidFile):
                os.unlink(pidFile)
            raise

    def _stopHostapd(self, ifname):
        cfgFile = os.path.join(self.tmpDir, "hostapd-%s.conf" % (ifname))
        pidFile = os.path.join(self.tmpDir, "hostapd-%s.pid" % (ifname))

        self.hostapdProcDict[ifname].terminate()
        self.hostapdProcDict[ifname].wait()
        del self.hostapdProcDict[ifname]

        if os.path.exists(cfgFile):
            os.unlink(cfgFile)
        if os.path.exists(pidFile):
            os.unlink(pidFile)

    def _genWlanAdapterHwCfg(self, wlanIntf, highOrLow):
        buf = ""
        buf += "driver=nl80211\n"
        # if highOrLow:
        #     buf += "hw_mode=a\n"                        # 5GHz
        # else:
        #     buf += "hw_mode=g\n"                        # 2.4GHz
        if True:
            buf += "hw_mode=g\n"                        # 2.4GHz
            buf += "channel=1\n"                        # it sucks that channel=0 (ACS) has bug
        buf += "ieee80211n=1\n"
        buf += "ieee80211ac=1\n"
        buf += "wmm_enabled=1\n"
        return buf


class _WrtConfigWifiNetwork:

    def __init__(self):
        self.ssid = None
        self.password = None
