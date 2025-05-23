# How to Use Sockets

I imagine a lot of the interfacing code comes from the `lib/simbricks/` folder, which contains a lot of this helper code that's pulled in by their various C files.

## PCI Socket

The socket that enables PCI communication between the NIC and the host device, appears to be passed into the Host (e.g. Gem5Host), using the following argument defined in `simulators.py`, `run_cmd` in the host class:

```py
f'--simbricks-pci=connect:{env.dev_pci_path(dev)}'
```

For Gem5, this is a CLI argument that's passed into the gem5 simulator instance that's run for the host device. I imagine it makes use of a custom interface that the SimBricks devs must've baked in (obvs, I don't imagine `--simbricks-pci` being a gem5 original arg).

Might need to take a look into how they've modified the simulator, but I imagine it's just some C++ code that sends messages via the PCI interface? I hope :pensive:

```py
def gem5_path(self, variant: str) -> str:
    return f'{self.repodir}/sims/external/gem5/build/X86/gem5.{variant}'
```

Conveniently, this gem5 submodule uses SCons to construct itself, not a Makefile :D\
(I have never seen one of these before...)\
Under the hood, still `gcc`/`clang`, though.

### Interface Search

Ok, after digging through all of their [custom commits](https://github.com/simbricks/gem5/commits/main/) it looks like the `src/simbricks/` (and `configs/simbricks/`, but that's not as important), directory in `/sims/external/gem5/` is the only one with substantial changes. All the changes made to other areas of the codebase are just small adjustments to various existing components to release limiters, downgrade errors to warnings, and generally loosen restrictions so that the system doesn't crash as much.

TODO: dig through the PCI code, and see if you can find the hooks

探そうよ :D

### 使い方

> TODO: When I figure out what the interface looks like, this will be me trying to use it

## Eth Socket

Ok, so, symmetrically, these are used by their respective network simulator, where presumably the network simulator sets this socket as some kind of networking interface. The following fn from `simulators.py`'s base `NetSim` defines the point at which this is abstracted into a list of sockets to connect to:

```py
def connect_sockets(self, env: ExpEnv) -> tp.List[tp.Tuple[Simulator, str]]:
    sockets = []
    for n in self.nics:
        sockets.append((n, env.nic_eth_path(n)))
```

As you can see, the nics are iterated over, with the socket file being extracted from each NIC. Once these paths are extracted, they are once again passed as arguments into their respective simulators (`sims/net/*`).

Interestingly, `WireNet` only connects 2 devices, so presumably a new `WireNet` instance must be instantiated per connection one desires. The others tend to have a `-s` option to add these devices to.

### Interface Search

どこに？見付かれないよ :(

TODO: maybe do this first, since this interface may be more immediately useful?

Unrelated, but apparently the interface file in the latest version of Corundum has been removed :D

### 使い方

> TODO: When I figure out what the interface looks like, this will be me trying to use it


# Latest Corundum Test

```sv
indir_tbl_index_reg[INDIR_TBL_ADDR_WIDTH-1:0] <= (
    req_dest & app_mask_reg[req_id]) + (req_hash & hash_mask_reg[req_id]
);
if (PORTS > 1) begin
    indir_tbl_index_reg[INDIR_TBL_ADDR_WIDTH +: CL_PORTS] <= req_id;
    // This line is the problem, the problem is the width of this ^
end
req_dest_d1_reg <= req_dest;
req_dest_d1_reg[DEST_WIDTH-1] <= req_dest[DEST_WIDTH-1] & app_direct_en_reg[req_id];
req_tag_d1_reg <= req_tag;
req_valid_d1_reg <= req_valid;
```

