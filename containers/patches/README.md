# Container Patches

Various patches, to be applied onto the git submodule files, by the container build process.

## CorunSim

These patches are those provided by the SimBricks devs. More information can be found in the [`corunsim/` directory](../../nics/corunsim/README.md).

## Corundum

These are my own patches for the Corundum system.

### Latest

This consists of some patches I was writing to get the system to compile under Verilator, and not just under Icarus Verilog. Ultimately this was abandoned, especially since [Corundum](https://groups.google.com/g/corundum-nic/c/9oAPMKfncxY) isn't tested under Verilator, in pursuit of a system that worked with the existing infrastructure, instead of chasing a ton of patches and fixes.

