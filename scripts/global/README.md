# Container Global Scripts

These are scripts that should be globally available within the container.\
If they're not accessible to you, please check the [debugging section](#debugging).

## activenv

A little script ported over from my personal desktop that just activates python `venv`s.

>![NOTE]
>The reason there are two, is just so that the default can be set differently between the corundum and talc containers\
> They're manually handled within the build process, which isn't ideal, but I didn't want to add complexity to the activenv script

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
