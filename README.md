# Automatic build of linux containers

The aim of this project is to utilize [mulled](https://github.com/mulled/mulled) and with this [involucro](https://github.com/involucro/involucro) in an automatic way. Every new package in
bioconda is build and packaged into a Linux Container (Docker, rkt) and available from [quay.io](https://quay.io/organization/biocontainers).

We have developed small utilities around this technology stack which is currently included in [`galaxy-lib`](https://github.com/galaxyproject/galaxy-lib). Here is a short introduction:

## Search for containers

```sh
mulled-search -s vsearch -o biocontainers
```

## Build all packages from bioconda from the last 24h

```sh
mulled-build-channel --channel bioconda --namespace biocontainers \
    --involucro-path ./involucro --recipes-dir ./bioconda-recipes --diff-hours 25 build
```

## Test all packages from bioconda from the last 24h

> tests will be extracted from the `recipes-dir` - we need to improve it, if you have time get in touch with me :)

```sh
mulled-build-channel --channel bioconda --namespace biocontainers \
    --involucro-path ./involucro --recipes-dir ./bioconda-recipes --diff-hours 25 build
```

## Building Docker containers for local Conda packages

> we modified the samtools package to version 3.0 to make clear we are using a local version

1. build your recipe

  ```sh
  conda build recipes/samtools
  ```

2. index your local builds

  ```sh
  conda index /home/bag/miniconda2/conda-bld/linux-64/
  ```

3. build a container for your local package

  ```sh
  mulled-build build-and-test 'samtools=3.0' \
    --extra-channel file://home/bag/miniconda2/conda-bld/ --test 'samtools --help'
  ```


ToDo:
-----

 * all bioconda precompiled conda-packages are mirrored to the Galaxy depot
 * extend this concept for conda-forge
