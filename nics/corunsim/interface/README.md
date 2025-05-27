# Corundum Interface Files

These are really useful interface files taken from the good people at SimBricks:

[Commit `57eeed65e91a467ce745b3880347f978c57e3beb`](https://github.com/simbricks/simbricks/tree/57eeed65e91a467ce745b3880347f978c57e3beb)

Which itself derives from the Corundum commit:

Commit `d0c9a83752cde7715787aa31a5bb951fc808e0cc` from https://github.com/ucsdsysnet/corundum.

## [`lib/`](./lib/)

This is a library of various tools used by SimBricks for interconnecting simulators and providing them with a consistent API to call on. Which would be incredibly convenient, even without the rest of the SimBricks framework.

Taken from the same commit as above from [`/lib/`](https://github.com/simbricks/simbricks/tree/57eeed65e91a467ce745b3880347f978c57e3beb/lib).

## [`mk/`](./mk/)

These are Makefile utilities that are included in the various sub-rules to better track and provide a consistent environment to each of the sub-`rules.mk` files.

Taken from the same commit as above from [`/mk/`](https://github.com/simbricks/simbricks/tree/57eeed65e91a467ce745b3880347f978c57e3beb/mk).
