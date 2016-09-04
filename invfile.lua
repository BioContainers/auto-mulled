
local repo = 'quay.io/' .. ENV.NAMESPACE .. '/' .. VAR.PACKAGE .. ':' .. VAR.TAG

inv.task('build')
    .using('continuumio/miniconda:latest')
        .withHostConfig({binds = {"build:/data"}})
        .run('rm', '-rf', '/data/dist')
    .using('continuumio/miniconda:latest')
        .withHostConfig({binds = {"build/dist:/usr/local/"}})
        .run('/bin/sh', '-c', 'conda install --channel bioconda --channel r '
            .. VAR.PACKAGE .. '=' .. VAR.VERSION .. '=' .. VAR.BUILD
            .. ' -p /usr/local --copy --yes')
    .wrap('build/dist')
        .at('/usr/local')
        .inImage('bgruening/busybox-bash:0.1')
        .as(repo)

inv.task('test')
    .using(repo)
    .withConfig({entrypoint = {'/bin/sh', '-c'}})
    .run(VAR.TEST)

inv.task('push')
    .push(repo)

inv.task('all')
    .runTask('build')
    .runTask('test')
    .runTask('push')
