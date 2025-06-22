# Talc

Talc is a Verilator Testbench harness designed to test hardware implementations of networking-related logic, implemented on the [Corundum NIC](https://github.com/corundum/corundum).

There are a few systems in this repo, the primary system being Talc.

## Usage

>[!WARNING]
>Generally, I cannot guarantee that any of these will run outside of the provided containers due to the dependencies of the the simulation tools and environment.

Talc and CorunTB have both Docker Containers _and_ accompanying [DevContainer](https://code.visualstudio.com/docs/devcontainers/containers) configuration files for use with VSCode. I provide pure docker instructions for _all_ the containers, to not force any particular system on anyone, though, using a DevContainer is my preferred development environment.\
As such, prerequisites are:

- [Docker](https://www.docker.com/) (obviously)

If using VSCode and DevContainers:
- [VSCode](https://code.visualstudio.com/)
- [DevContainers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Talc

This is the primary testbench container that I have developed for my FYP.

#### VSCode

1. Clone repo
2. Initialise and Update git [submodule](./nics/corundum/)
   - `git submodule update --init --recursive` would pull in _all_ submodules
3. Open in VSCode
4. If you don't have GPUs or haven't set them up to work with docker, comment out `--gpus=all` in [`devcontainer.json`](./.devcontainer/devcontainer.json)
5. `> Reopen in Container` (selecting the `talc` option)
6. Begin development

#### Docker

1. Clone repo
2. Initialise and Update git [submodule](./nics/corundum/)
   - `git submodule update --init --recursive` would pull in _all_ submodules
3. Execute docker instructions laid out at the bottom of the [Dockerfile](./containers/talc.Dockerfile):
   - Run from repository root
   - `docker build -t talc -f containers/talc.Dockerfile .`
   - `docker run -d --name tlc --gpus=all --cap-add=NET_RAW --cap-add=NET_ADMIN --device /dev/net/tun:/dev/net/tun --mount type=bind,src=./src/tb,dst=/talc/tb/testbench/ --mount type=bind,src=./src/utils/py,dst=/talc/pyutils --mount type=bind,src=./nics/corundum/fpga/app/talc/rtl,dst=/talc/rtl talc`
     - If you don't have GPUs or haven't set them up to work with docker, remove the `--gpus=all` option (`argv[5]`)
   - `docker exec -it tlc bash`
4. Begin Development

### CorunSim

[CorunSim](./containers/corunsim.Dockerfile) is an alternative, isolated DUT, based on SimBricks' adaptation of Corundum. It features an extracted version of the [older Corundum](https://github.com/corundum/corundum/tree/d0c9a83752cde7715787aa31a5bb951fc808e0cc) implementation that was tweaked for use with the version of [SimBricks](https://github.com/simbricks/simbricks/tree/57eeed65e91a467ce745b3880347f978c57e3beb), that I started with.

This container just contains an extracted version of the old SimBricks implementation of the Corundum NIC, which exposes two sockets to connect to for PCIe and MAC communication.

#### Docker

1. Clone repo
2. Initialise and Update git [submodule](./nics/corunsim/corundum/)
   - `git submodule update --init --recursive` would pull in _all_ submodules
3. Execute docker instructions laid out at the bottom of the [Dockerfile](./containers/corunsim.Dockerfile):
   - Run from repository root
   - `docker build -t corunsim_test -f containers/corunsim.Dockerfile .`
   - `docker run -d --name corunsim_tb corunsim_test`
   - `docker exec -it corunsim_tb bash`
4. Begin Work

### CorunTB

[`CorunTB`](./containers/coruntb.Dockerfile) is an outdated version of the Talc system that doesn't contain a lot of the newer additions to the environment, but I kept it here in case one wishes to use a very simple version of this testbench, without the full development toolset, and large codebase refactoring.

#### VSCode

1. Clone repo
2. Initialise and Update git [submodule](./nics/corundum/)
   - `git submodule update --init --recursive` would pull in _all_ submodules
3. Open in VSCode
4. If you don't have GPUs or haven't set them up to work with docker, comment out `--gpus=all` in [`devcontainer.json`](./.devcontainer/devcontainer.json)
5. `> Reopen in Container` (selecting the `coruntb` option)
6. Begin development

#### Docker

1. Clone repo
2. Initialise and Update git [submodule](./nics/corundum/)
   - `git submodule update --init --recursive` would pull in _all_ submodules
3. Execute docker instructions laid out at the bottom of the [Dockerfile](./containers/coruntb.Dockerfile):
   - Run from repository root
   - `docker build -t coruntb -f containers/coruntb.Dockerfile .`
   - `docker run -d --name cortb --gpus=all --cap-add=NET_RAW --cap-add=NET_ADMIN --device /dev/net/tun:/dev/net/tun --mount type=bind,src=./src/tb,dst=/corundum/fpga/app/template/tb/coruntb --mount type=bind,src=./src/tap/py/,dst=/tapaz/ coruntb`
     - If you don't have GPUs or haven't set them up to work with docker, remove the `--gpus=all` option (`argv[5]`)
   - `docker exec -it cortb bash`
4. Begin Development

### Tunic

[`Tunic`](./containers/tunic.Dockerfile) is based off of [this fork](https://github.com/lemon-gith/tunic), of the [Tonic](https://github.com/minmit/tonic) system. This was intended to be fixed up and merged into the Corundum App Logic block, to provide a further template for hardware implementation.

> [!WARNING]
> There really is not much use in opening this container, since it's unfinished and still has a lot of the bugs present in the original repo.

#### Docker

1. Clone repo
2. Initialise and Update git [submodule](./nics/tunic/)
   - `git submodule update --init --recursive` would pull in _all_ submodules
3. Execute docker instructions laid out at the bottom of the [Dockerfile](./containers/talc.Dockerfile):
   - Run from repository root
   - `docker build -t tunic_test -f containers/tunic.Dockerfile .`
   - `docker run -d --name tunic_tb tunic_test`
   - `docker exec -it tunic_tb bash`
4. `source /tunic/venv/bin/activate`
5. Begin Work
   - `./tools/runtest --type sim --config tonic/tonic_reno.yaml`

## Repository Structure

### [`.devcontainer/`](./.devcontainer/)

VSCode's special devcontainer directory.

- `devcontainer.json`
  - contains the devcontainer configs for Talc
- `coruntb/devcontainer.json`
  - contains the devcontainer configs for `coruntb`

### [`containers/`](./containers/)

A directory to hold container Dockerfiles and various other helper files.

- `configs/`
  - contains VSCode configuration files for talc and coruntb, as well as a `requirements.txt` for those containers
- `patches/` ([README](./containers/patches/README.md))
- `Dockerfiles`
  - the 4 Dockerfiles for each of the available containers

### [`nics/`](./nics/)

A directory to hold nic submodules, as well as some helper files relating to the NICs.

- `corundum` ([README](./nics/corundum/README.md))
- `CorunSim` ([README](./nics/corunsim/README.md))
- `Tunic` ([README](./nics/tunic/README.md))

### [`scripts/`](./scripts/)

A directory to hold the bash scripts that I make use of.

- `basic_net/`
  - the scripts that I wrote to spin up the infrastructure for namespaced mock devices that could be used to test the NIC
- `global/` ([README](./scripts/global/README.md))
  - these are pulled into the Talc and CorunTB containers for use there

### [`src/`](./src/)

- `c_tap/`
  - contains the file written by my supervisor (using GPT-4o), to create a TAP device in C++
- `tb`
  - this is the main testbench codebase that's mounted into the Talc and CorunTB containers for development
- `utils/py/`
  - contains the python utility libraries used (and globally available) within the Talc container

## Moving to On-Board Development

When moving onto testing for specific boards, the base assumption is that none of Corundum's source files have been modified: only the top-level files in [`talc/rtl/`](./nics/corundum/fpga/app/talc/rtl/) that modify the `App` block, i.e. none of the files in [`talc/rtl/common/`](./nics/corundum/fpga/app/talc/rtl/common/), only the files like `mqnic_app_block.v`. If any of these are changed, it's alright, but they will need to be copied over, too.

All other directories, as a result of all the Corundum symlinks, should be pulled in everywhere needed, so, as long as you remember to port your specific app logic over to where it's needed, too, you should be all set to use the Corundum system, using their [README](https://github.com/corundum/corundum/blob/1ca0151b97af85aa5dd306d74b6bcec65904d2ce/README.md).
