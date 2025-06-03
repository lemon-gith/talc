from option import Result, Ok, Err
from subprocess import CompletedProcess
import subprocess


class IPRoute:
    """A wrapper for the ip toolset (i.e. you need it installed on your system)

    literally just runs the ip command given...\n
    Warning: cannot run any sudo commands,
    unless you have python installed under root

    i.e. never ever expose this API to anyone that you wouldn't 100%
    trust to enter arbitrary commands on your device :D

    But I think it's a nice wrapper, that:
    - is simple to use
    - flexible, to a fault
    - doesn't introduce new proprietary syntax
    - handles errors gracefully

    Warning: This only runs on linux systems
    that already have the iproute toolset installed... (very portable, ik)

    Note: currently only supports more readable `.addr` and `.link`,
    use `.ip` for all other commands (or those, too, if you want...)
    """
    def __init__(self):
        out = self._run_cmd("ip -V")

        if out.is_err:
            raise RuntimeError(
                f"""err (ipr): I think ip utility isn't installed,
                here's the error:\n{out.unwrap_err()}"""
            )

        # all good to go :)

    def _sanitiser(self, *args: str) -> Result[None, str]:
        """
        Very unsophisticated command sanitiser, before being passed to bash

        For more secure use, I recommend implementing whitelisting
        """
        blacklist = (';', '|', '&&')
        for arg in args:
            for taboo in blacklist:
                if taboo in arg:
                    return Err(taboo)

        return Ok(None)


    def _run_cmd(self, cmd: str) -> Result[CompletedProcess[str], str]:
        """literally just runs the command given...

        But also raises error on failed command, etc.

        i.e. never ever expose this API to anyone that you wouldn't 100%
        trust to enter arbitrary commands on your device :D
        """
        out = subprocess.run(
            cmd.strip(), shell=True,
            capture_output=True, text=True, encoding='utf-8'
        )

        if out.returncode == 0:
            return Ok(out)
        else:
            return Err(
                f"""err (ipr): command '{cmd}' failed:
stdout: {out.stdout}\nstderr: {out.stderr}\nfull log: {out}
                """  # have to do it like this for the formatting...
            )

    def addr(
        self, *cmds: str, as_root: bool = False
    ) -> Result[CompletedProcess[str], str]:
        """ Usage (taken directly from ip addr help):

        ip address {add|change|replace} IFADDR dev IFNAME [ LIFETIME ]
        [ CONFFLAG-LIST ]

        ip address del IFADDR dev IFNAME [mngtmpaddr]

        ip address {save|flush} [ dev IFNAME ] [ scope SCOPE-ID ]
        [ to PREFIX ] [ FLAG-LIST ] [ label LABEL ] [up]

        ip address [ show [ dev IFNAME ] [ scope SCOPE-ID ] [ master DEVICE ] [ nomaster ] [ type TYPE ] [ to PREFIX ] [ FLAG-LIST ] [ label LABEL ] [up] [ vrf NAME ] ]

        ip address {showdump|restore}

        IFADDR := PREFIX | ADDR peer PREFIX [ broadcast ADDR ] [ anycast ADDR ]
        [ label IFNAME ] [ scope SCOPE-ID ] [ metric METRIC ]

        SCOPE-ID := [ host | link | global | NUMBER ]

        FLAG-LIST := [ FLAG-LIST ] FLAG

        FLAG  := [ permanent | dynamic | secondary | primary | [-]tentative |
        [-]deprecated | [-]dadfailed | temporary | CONFFLAG-LIST ]

        CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG

        CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]

        LIFETIME := [ valid_lft LFT ] [ preferred_lft LFT ]

        LFT := forever | SECONDS

        TYPE := { amt | bareudp | bond | bond_slave | bridge | bridge_slave |
        dsa | dummy | erspan | geneve | gre | gretap | gtp | ifb | ip6erspan |
        ip6gre | ip6gretap | ip6tnl | ipip | ipoib | ipvlan | ipvtap | macsec |
        macvlan | macvtap | netdevsim | nlmon | rmnet | sit | team |
        team_slave | vcan | veth | vlan | vrf | vti | vxcan | vxlan | wwan |
        xfrm | virt_wifi }
        """
        out = self._sanitiser(*cmds)
        if out.is_err:
            return Err(
                f"err (ipr): disallowed string, '{out.unwrap()}', in command"
            )

        return self._run_cmd(
            ("sudo" if as_root else "")+ f"ip addr {' '.join(cmds)}"
        )

    def link(
        self, *cmds: str, as_root: bool = False
    ) -> Result[CompletedProcess[str], str]:
        """ Usage (taken directly from ip link help):

        ip link add [link DEV | parentdev NAME] [ name ] **NAME**
        [ txqueuelen PACKETS ] [ address LLADDR ] [ broadcast LLADDR ]
        [ mtu MTU ] [index IDX ] [ numtxqueues QUEUE_COUNT ]
        [ numrxqueues QUEUE_COUNT ] [ netns { PID | NAME } ]
        **type TYPE** [ ARGS ]

        ip link delete **{ DEVICE | dev DEVICE | group DEVGROUP }**
        **type TYPE** [ ARGS ]

        ip link set **{ DEVICE | dev DEVICE | group DEVGROUP }**
        [ { up | down } ] [ type TYPE ARGS ] [ arp { on | off } ]
        [ dynamic { on | off } ] [ multicast { on | off } ]
        [ allmulticast { on | off } ] [ promisc { on | off } ]
        [ trailers { on | off } ] [ carrier { on | off } ]
        [ txqueuelen PACKETS ] [ name NEWNAME ] [ address LLADDR ]
        [ broadcast LLADDR ] [ mtu MTU ] [ netns { PID | NAME } ]
        [ link-netns NAME | link-netnsid ID ] [ alias NAME ]
        [ vf NUM [ mac LLADDR ]
        [ vlan VLANID [ qos VLAN-QOS ] [ proto VLAN-PROTO ] ]\
        [ rate TXRATE ] [ max_tx_rate TXRATE ]
        [ min_tx_rate TXRATE ] [ spoofchk { on | off} ]
        [ query_rss { on | off} ] [ state { auto | enable | disable} ]
        [ trust { on | off} ] [ node_guid EUI64 ] [ port_guid EUI64 ] ]\
        [ { xdp | xdpgeneric | xdpdrv | xdpoffload }
        { off | object FILE [ { section | program } NAME ]
        [ verbose ] | pinned FILE } ] [ master DEVICE ] [ vrf NAME ]
        [ nomaster ] [ addrgenmode { eui64 | none | stable_secret | random } ]
        [ protodown { on | off } ] [ protodown_reason PREASON { on | off } ]
        [ gso_max_size BYTES ] | [ gso_max_segs PACKETS ] [ gro_max_size BYTES ]

        ip link show [ DEVICE | group GROUP ] [up] [master DEV] [vrf NAME]
        [type TYPE] [nomaster]

        ip link xstats type TYPE [ ARGS ]

        ip link afstats [ dev DEVICE ]

        ip link property add dev DEVICE [ altname NAME .. ]

        ip link property del dev DEVICE [ altname NAME .. ]

        ip link help [ TYPE ]

        TYPE := { amt | bareudp | bond | bond_slave | bridge | bridge_slave |
        dsa | dummy | erspan | geneve | gre | gretap | gtp | ifb | ip6erspan |
        ip6gre | ip6gretap | ip6tnl | ipip | ipoib | ipvlan | ipvtap | macsec |
        macvlan | macvtap | netdevsim | nlmon | rmnet | sit | team |
        team_slave | vcan | veth | vlan | vrf | vti | vxcan | vxlan | wwan |
        xfrm | virt_wifi }
        """
        out = self._sanitiser(*cmds)
        if out.is_err:
            return Err(
                f"err (ipr): disallowed string, '{out.unwrap()}', in command"
            )

        return self._run_cmd(
            ("sudo" if as_root else "")+ f"ip link {' '.join(cmds)}"
        )

    def ip(
        self, *cmds: str, as_root: bool = False
    ) -> Result[CompletedProcess[str], str]:
        """Usage (taken from ip help):

        ip [ OPTIONS ] OBJECT { COMMAND | help }

        ip [ -force ] -batch filename

        OBJECT := { address | addrlabel | amt | fou | help | ila | ioam |
        l2tp | link | macsec | maddress | monitor | mptcp | mroute | mrule |
        neighbor | neighbour | netconf | netns | nexthop | ntable | ntbl |
        route | rule | sr | tap | tcpmetrics | token | tunnel | tuntap | vrf |
        xfrm }

        OPTIONS := { -V[ersion] | -s[tatistics] | -d[etails] | -r[esolve] |
        -h[uman-readable] | -iec | -j[son] | -p[retty] | -f[amily] { inet |
        inet6 | mpls | bridge | link } | -4 | -6 | -M | -B | -0 |
        -l[oops] { maximum-addr-flush-attempts } | -br[ief] | -o[neline] |
        -t[imestamp] | -ts[hort] | -b[atch] [filename] | -rc[vbuf] [size] |
        -n[etns] name | -N[umeric] | -a[ll] | -c[olor]}
        """
        out = self._sanitiser(*cmds)
        if out.is_err:
            return Err(
                f"err (ipr): disallowed string, '{out.unwrap()}', in command"
            )

        return self._run_cmd(
            ("sudo" if as_root else "")+ f"ip {' '.join(cmds)}"
        )
