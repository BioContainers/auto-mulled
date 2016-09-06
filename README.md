Automatic build of linux containers
-----------------------------------

The aim of this project is to utilize [mulled](https://github.com/mulled/mulled) and with this [involucro](https://github.com/involucro/involucro) in an automatic way. Every new package in
bioconda is build and packaged into a Linux Container (Docker, rkt) and available from [quay.io](https://quay.io/organization/mulled).



ToDo:
-----

 * all bioconda precompiled conda-packages are mirrored to the Galaxy depot
 * extend this concept for conda-forge
 * create a small command line utility to query the mulled repo, find packages and versions ...
