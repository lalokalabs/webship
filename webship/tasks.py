# -*- coding: utf-8 -*-

"""
Copyright (c) 2020-present Xoxzo Inc.

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

from invoke import task

@task
def fetch(c, repo=None, clone_args=""):
    repo = repo or c.webship.fetch.repo
    if clone_args:
        clone_args = f"--{clone_args}"
    else:
        if "clone_args" in c.webship["fetch"]:
            clone_args = f"--{c.webship.fetch.clone_args}"

    c.run("mkdir -p build")
    with c.cd("build"):
        c.run(f"git clone {clone_args} {repo}")

@task
def build(c, project_name, version, docker_image="python:3.8"):
    repo_path = "$PWD"
    build_opts = ""
    deploy_path = f"/app/releases/{project_name}-{version}"
    docker_cmd = (f"podman run --rm -i -t -v {repo_path}:{deploy_path} {docker_image} "
                  f"/bin/bash -c 'cd {deploy_path} && rm -rf .venv && "
                  f"poetry install'")
    print(docker_cmd)
    with c.cd(f"build/{project_name}"):
        ret = c.run(docker_cmd)

    excludes = "--exclude=.git"
    tarball_name = f"{project_name}-{version}.tar.gz"
    with c.cd("build"):
        c.run(f"tar czf {tarball_name} {excludes} {project_name}")

@task
def run(c, project_name, version, cmd, env_file=None, docker_image="python:3.8"):
    tarball_name = f"{project_name}-{version}.tar.gz"
    deploy_path = f"/app/releases"
    docker_cmd = (f"podman run --rm -i -t -v $PWD:/build "
                  f"-e tarball_name={tarball_name} -e deploy_path={deploy_path} --env-file={env_file} "
                  f"-e project_name={project_name} -e version={version} {docker_image} "
                  f"/bin/bash -c 'cd /build && ls && tar xzf {tarball_name} && mkdir -p {deploy_path} && "
                  f"mv {project_name} {project_name}-{version} && "
                  f"mv {project_name}-{version} {deploy_path} && "
                  #f"/bin/bash'")
                  f"{deploy_path}/{project_name}-{version}/{cmd}'")
    with c.cd("build"):
        print(docker_cmd)
        ret = c.run(docker_cmd, pty=True)
        print(ret)

@task
def deploy(c):
    breakpoint()
    print("Running integration tests!")
