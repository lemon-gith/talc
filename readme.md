# Talc

Talc is a Verilator Testbench harness designed to test hardware implementations of networking-related logic, implemented on the [Corundum NIC](https://github.com/corundum/corundum).

## Codespaces Version

>[!NOTE]
>This repo has been slightly modified to run in GitHub Codespaces. The changes are not substantial and consist of changes only to the devcontainer file, removing unavailable options and automating things that would otherwise be expected from the user, to allow it to be built by a runner.

## Usage

>[!WARNING]
>I cannot guarantee that any containers but that for Talc will run in this environment. Moreover, it must be within a DevContainer, because that is what a GitHub Codespace uses to configure itself.

### Talc

This is the primary testbench container that I have developed for my FYP.

#### GitHub Codespaces

1. Create a GitHub Codespace on this branch
2. Start Testing

>[!WARNING]
>Please note that due to the remote nature of the Codespace and the restructuring present in the repo, there is currently no simple way to commit any work done within the codespace. For development, please use the main branch and clone a local copy. This branch is only good for quick and portable testing of the existing system.

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
