```bash
./corundum_verilator {self.basic_args(env, self.clock_freq)}

./corundum_verilator {env.dev_pci_path(self)} {env.nic_eth_path(self)}\
  {env.dev_shm_path(self)} {self.sync_mode} {self.start_tick}\
  {self.sync_period} {self.pci_latency} {self.eth_latency} {self.clock_freq}
```

`env` variables come from the `env` parameter that `run_cmd` takes:
```py
fred = CorundumVerilatorNIC()
fred.run_cmd(env)
```

It looks like `run_cmd` is only ever called by `runners.py` in `ExperimentBaseRunner`'s async `start_sim` function:

```py
# self.env refers to the env passed into the EBR object on instantiation
run_cmd = sim.run_cmd(self.env)

# executor isn't necessarily important here, I think?
executor = self.sim_executor(sim)
sc = executor.create_component(
    name, shlex.split(run_cmd), verbose=self.verbose, canfail=True
)
await sc.start()
self.running.append((sim, sc))
```

Ok, for some reason `ExperimentBaseRunner` seems to be the end of the road, I'm not quite sure why. So, this is just a guess, but I reckon an indirect call is made to `runners.py` via `run.py`. I have absolutely no clue where the `runtime` from here comes from (run.py: L39):
```py
from simbricks.orchestration import runtime
```

but I reckon that this is the line that pulls that in.

Since the way to call experiments is:

```bash
/path/to/run.py /path/to/exp.py
```

and `/exp.py` is just a script that instantiates, configures, and loads experiment instances into an `experiments: List[Experiment]` variable, which is then used in the line (run.py: L327):

```py
# the `exp.py` paths that can be passed into the `run.py` script
for path in args.experiments:
    ...
    experiments += ...

# after accumulating all the defined experiments, for each of those
for e in experiments:
    no_simbricks = e.no_simbricks
    # first do a dry run to collect config values, if checkpoint=true
    # this step is explained in SimBricks documentation
    if e.checkpoint:
        prereq = add_exp(
            e, rt, 0, None, True, False, no_simbricks, args
        )
    else:
        prereq = None

    # these are the important lines
    for run in range(args.firstrun, args.firstrun + args.runs):
        add_exp(
            e, rt, run, prereq, False, e.checkpoint, no_simbricks, args
        )
```

- `e` is the experiment itself, this is an important part of the call
  - defined in `simbricks/orchestration/experiments.py`
- `rt` is a `runtime.Runtime` object
  - idrk what else to add here, yet
- `run` is just a counter
- `prereq` is a `runtime.Run` that may or may not exist, dependent on `checkpoint`
- the following 3 bools are just passed into the `env` variable
- `args` contains all the CLI args parsed
  - `args.repo` is used to instantiate the `repo_path` variable for `ExpEnv`

Importantly, ExpEnv is imported into the `run.py` module via the

```py
from simbricks.orchestration.experiment import experiment_environment
```

call. This pulls it in from the file in which the class `ExpEnv` is defined, i.e. as `experiment_environment.ExpEnv`.\
This line in `add_exp()` is what instantiates the ExpEnv object.

```py
env = experiment_environment.ExpEnv(args.repo, workdir, cpdir)
```

Following that, this object is passed into a runtime:

```py
run = runtime.Run(e, run, env, outpath, prereq)
rt.add_run(run)
return run
```

Return value of `add_exp()` is only useful for `prereq`, it's otherwise ignored.

`runtime` from this import line:

```py
from simbricks.orchestration import runtime
```

is a directory within `simbricks/orchestration`. It defines multiple files within it that can be imported into `run.py`. This particular one, `Run` is defined in `common.py` and my assumption is that from here, nothing super interesting happens, and values are just passed down until they reach the final call. So, back up to `ExpEnv` and where it gets its values from.

---

From `run.py`, it seems like `workdir` just refers to the directory that the simulation should output its files to? (that was just `workspaces/simbricks/out` for SimBricks)

And `sim.name` is the value of the name variable assigned to that particular simulator class. For `CorundumVerilatorNIC`, neither of its parents, `NICSim` nor `PCIDevSim` seem to overwrite `self.name`.

Which means that it's a case of an attribute being used as a publicly-modifiable attribute despite a lack of labelling or get-/set-ters. Gah, I hate python :/

Best part is, after spending another little while hunting it down, it turns out that the name is slowly built, piece-by-piece, by the various classes it's passed into, e.g.:

```py
# from HostSim, from Gem5Host, from experiments/gt_tcp_single.py
def add_nic(self, dev: NICSim) -> None:
    """Add a NIC to this host."""
    self.add_pcidev(dev)

def add_pcidev(self, dev: PCIDevSim) -> None:
    """Add a PCIe device to this host."""
    dev.name = self.name + '.' + dev.name
    self.pcidevs.append(dev)
```

At the very beginning, the base `Simulator` class just gets the name `''`, which is great. That means that the name is slowly constructed by the system.

Quite frankly, I'm not quite sure how to get the name, but having taken a little poke around at the output files and various other components, I'm not sure the name here is really that important anymore :/

To conclude, the values passed to the `corundum_verilator` call must have been:

- env.dev_pci_path(self)
  - ??? - `/corundum/out/dev.pci.{fred}`
- env.nic_eth_path(self)
  - ??? - `/corundum/out/nic.eth.{fred}`
- env.dev_shm_path(self)
  - ??? - `/corundum/out/dev.shm.{fred}`
- self.sync_mode
  - = 0
- self.start_tick
  - = 0
- self.sync_period
  - = 500
- self.pci_latency
  - = 500
- self.eth_latency
  - = 500
- self.clock_freq
  - = 250  # MHz

I reckon the name is mostly irrelevant, and just gives the other components a specific file to hook onto.

My guess is that those three path-strings indicate possible inter-communication paths, like named pipes or sth., idk :p

---

I would have loved to have just pulled this info out of the run files generated by SimBricks, but it was specifically the experiments that used `CorundunmVerilatorNIC` that proceeded to fry my laptop...

So, I couldn't run them locally, and don't have access to the log files when they're run remotely (by their new runners).

Once I was able to figure out the calling syntax, I was finally able to get it to run without receiving a `Segmentation fault (core dumped)`. I reckon it's finally up and running, now I need to figure out how to talk to it...

idk how long that'll take, or whether the communication will go smoothly, but yh
