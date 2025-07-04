# Container Global Scripts

These are scripts that should be globally available within the container.\
If they're not accessible to you, please check the [debugging section](#debugging).

## activenv

A little script ported over from my personal desktop that just activates python `venv`s.

>![NOTE]
>The find command for auto-detection of `venv/` directory only checks at depth level 2 from root (`/`)\
>This shouldn't be a problem in any of my containers, because that's how they're set up, but should that underlying assumption change, you can update `-mindepth` or `-maxdepth`, accordingly.

## privesc

A small utility that acts as a getter/setter for net capabilities.

It's not as dangerous as it sounds, I just couldn't think of another name.

## cory

A helpful CLI tool that just helps manage and run various commonly used commands.

Please feel free to update `cory` with new capabilities and commands you would find useful.\
If you do, remember to update his version number, too...

## Debugging

These scripts should be copied into `/usr/local/bin/`, which should be on your `PATH` by default.

1. Run `ls /usr/local/bin/` to see if the scripts are there or not
  - if they're not, there must've been a mistake while building or something (sth to check out)
  - for now, you can manually copy them in: `docker cp ./ <container name>:/usr/local/bin/`
2. Run `echo $PATH` to check if `/usr/local/bin` is on `PATH`
  - if it isn't then sth has been very misconfigured :/
  - open a new terminal in the container to check if this is a persistent issue
  - if it persists, run this to add this path to `PATH`
    - `echo -e "\nexport PATH=\${PATH:+\${PATH}:}/usr/local/bin/" >> ~/.bashrc`
