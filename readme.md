# Verilator Testbench

The Verilator Testbench and testing setup for the [SVIRD](https://gitlab.com/accaueh/svird) implementation.

## Usage

### Corundum

> [!NOTE]
> The way I've set up the Makefiles, without modification, this will only run in the [docker container](./containers/corundum.Dockerfile)

## Design

Currently, I'm attempting to use 2 different NIC implementations: [Corundum](https://github.com/corundum/corundum), [Tonic](https://github.com/minmit/tonic)

The former is now entrenched in python and iverilog code, so I'm using an older commit, the same one used by the SimBricks developers.\
In fact, I'm also using a bunch of their interface scripts in order to compile a friendlier Verilog binary.

The latter seems to have been abandoned, but would still be the base of choice for this project (if we needed a more easily modifiable base).\
The python code isn't great and is out-of-date, as a result, is I've created a fork ([Tunic](https://github.com/lemon-gith/tunic)), and will be working on repairing that and attempting to modify it for use with Verilator, in parallel with building out the rest of this testbench.

## TODOs

> TODO: Once you've sorted out this repo, rewrite this README, to be more helpful and to describe exactly what's used for what purpose

## On-Board Development

When moving onto testing for specific boards, as a result of all the Corundum symlinks, the `app/` directory that we're using for these testbenches is pulled in everywhere needed, so, as long as you remember to port your `mqnic_app_block.v` over to where it's needed, too, you should be all set.
