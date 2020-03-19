#!/usr/bin/env python3

from migen import *

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.clock import *

from liteeth.common import convert_ip
from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII
from liteeth.core import LiteEthUDPIPCore
from liteeth.frontend.etherbone import LiteEthEtherbone

from litex_boards.platforms import colorlight_5a_75b

# CRG ----------------------------------------------------------------------------------------------

class RGMIITestCRG(Module):
    '''A class to define the clock and reset Generator'''
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()

        # # #

        clk25 = platform.request("clk25")
        platform.add_period_constraint(clk25, 1e9/25e6)

        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk25, 25e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)

# RGMIITest ----------------------------------------------------------------------------------------

class RGMIITestSoC(SoCMini):
    '''Implement the SoC side of the test'''
    def __init__(self, platform, eth_phy=0, mac_address=0x10e2d5000000, ip_address="192.168.88.50"):
        sys_clk_freq = int(133e6)

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, sys_clk_freq)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = crg = RGMIITestCRG(platform, sys_clk_freq)

        # 1 Gbps Ethernet --------------------------------------------------------------------------
        # phy
        ethphy = LiteEthPHYRGMII(
            clock_pads = platform.request("eth_clocks", eth_phy),
            pads       = platform.request("eth", eth_phy))
        # core
        ethcore = LiteEthUDPIPCore(
            phy         = ethphy,
            mac_address = mac_address,
            ip_address  = convert_ip(ip_address),
            clk_freq    = sys_clk_freq,
            with_icmp   = True)
        self.submodules += ethphy, ethcore
        # timing constraints
        ethphy.crg.cd_eth_rx.clk.attr.add("keep")
        ethphy.crg.cd_eth_tx.clk.attr.add("keep")
        platform.add_period_constraint(ethphy.crg.cd_eth_rx.clk, 1e9/125e6)
        platform.add_period_constraint(ethphy.crg.cd_eth_tx.clk, 1e9/125e6)

        # Led --------------------------------------------------------------------------------------
        counter = Signal(32)
        self.sync += counter.eq(counter + 1)
        self.comb += platform.request("user_led_n").eq(counter[26])

# Build --------------------------------------------------------------------------------------------

def main():
    platform = colorlight_5a_75b.Platform(revision="7.0")
    soc     = RGMIITestSoC(platform)
    builder = Builder(soc, output_dir="build")
    builder.build()

if __name__ == "__main__":
    main()
