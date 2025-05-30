# Container Patches

Various patches, to be applied onto the git submodule files, by the container build process.

## [CorunSim](./corunsim/)

These patches are those provided by the SimBricks devs. More information can be found in the [`corunsim/` directory](../../nics/corunsim/README.md).

## [Corundum](./corundum/)

These are patches I've written for the original Corundum repo, not integrated with any other systems.

### [Latest](./corundum/latest/)

This consists of patches I was wrote to get the [latest](https://github.com/corundum/corundum/tree/1ca0151b97af85aa5dd306d74b6bcec65904d2ce)[^1] Corundum testbenches to compile under Verilator (v5.020), and not just under Icarus Verilog.\
Ultimately this was abandoned, especially since [Corundum](https://groups.google.com/g/corundum-nic/c/9oAPMKfncxY) isn't tested under Verilator, in pursuit of a system that worked with the existing infrastructure, instead of chasing a ton of patches and fixes.

- [mqnic_rx_queue_map.v](../../containers/patches/corunsim/mqnic_rx_queue_map.v#L109-l114)
  - Verilator 5.020 refused to acknowledge `CL_PORTS` as a constant value, despite being defined literally the same way as `ID_WIDTH`, so I reused the latter

[^1]: At the time of writing (2025-05-30)

## [Deprecated](./deprecated/)

These are patches that were necessary at some point, but are no longer needed in any of the building systems:

- [axis_async_fifo.v](./deprecated/axis_async_fifo.v#L698-L699)
  - This is less of a fix, and more of a bucket-kick...
  - I was unable to diagnose the exact reason Verilator was unhappy, but I knew that it was throwing [`ASCRANGE`](https://verilator.org/guide/latest/warnings.html#cmdoption-arg-ASCRANGE) errors at this point
  - In my head, this was fine, as it's clearly non-negative, because the exact same expression is found a [few lines above](./deprecated/axis_async_fifo.v#688), and doesn't cause an error
    - therefore the worst case is `RAM_PIPELINE = 0`, which still results in a valid, single-bit wire
  - but admittedly, I'm not sure if the original logic here still checks out, so this might just cause a problem down-the-road, which is why it was deprecated