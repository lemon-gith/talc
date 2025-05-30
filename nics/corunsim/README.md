# CorunSim (Corundum x SimBricks)

This is an extraction of the SimBricks implementation of Corundum with its various patches and whatnot. All the SimBricks content resides in the `interface/`.

>Read more about the [`interface/` folder](./interface/README.md).

The same version of Corundum used in the old version of SimBricks is included here as a submodule, so that if you want to run the SimBricks-extracted Corundum implementation, you can:

Commit `d0c9a83752cde7715787aa31a5bb951fc808e0cc` from https://github.com/corundum/corundum.

I can confirm that this is not plug-and-play with the latest version of Corundum, I have a lot of patches for this exact endeavour, that'll likely be deprecated, in the [`patches/`](../../containers/patches/) directory.

## Development Environment

I designed all of these systems to work in [Docker containers](https://www.docker.com/resources/what-container/) for maximum portability. As such, the docker container for the CorunSim mini project is defined in [`corunsim.Dockerfile`](../../containers/corunsim.Dockerfile), with a couple of comments describing how to run the container.

### Patches

You'll notice in that Dockerfile that there are some patches that are applied to the system as it builds the container. The CorunSim patches can all be found in [`patches/corunsim/`](../../containers/patches/corunsim/), with the majority of these patches being provided by the SimBricks devs, though there was no nice list, I had to chase them down by analysing Verilator bugs and their commit history.

You can read more about the patches, including the ones that I wrote in the [corresponding README](../../containers/patches/README.md).
