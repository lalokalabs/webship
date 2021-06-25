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

import os

from invoke import task
from fabric2 import Connection
from fabric2 import SerialGroup

def confirm(prompt="Proceed?", answer="Y", cancel="n"):
    if input(f"{prompt} [{answer}/{cancel}] ") == answer:
        return True

    return False

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
        name = c.webship["main"]["name"]
        if "command" in c.webship["fetch"]:
            with c.cd(f"{name}"):
                c.run(c.webship["fetch"]["command"])

@task
def build(c, project_name, version, docker_image="python:3.8"):
    repo_path = "$PWD"
    build_opts = ""
    command = c.webship["build"]["command"]
    deploy_path = f"/app/{project_name}/releases/{project_name}-{version}"
    docker_cmd = (f"podman run --rm -i -t -v {repo_path}:{deploy_path} {docker_image} "
                  f"/bin/bash -c 'cd {deploy_path} && rm -rf .venv && "
                  f"{command}'")
    print(docker_cmd)
    c.run(c.webship["build"]["pre_command"])
    with c.cd(f"build/{project_name}"):
        ret = c.run(docker_cmd)

    excludes = "--exclude=.git"
    tarball_name = f"{project_name}-{version}.tar.gz"
    with c.cd("build"):
        c.run(f"tar czf {tarball_name} {excludes} {project_name}")

@task
def run(c, tarball, cmd, env_file=None, docker_image="python:3.8"):
    project_name, version = tarball.split("/")[-1].split("-")
    version = version.strip(".tar.gz")
    if env_file is not None:
        fp = open(env_file)
        env_file = os.path.realpath(fp.name)

    tarball_name = f"{project_name}-{version}.tar.gz"
    deploy_path = f"/app/{project_name}/releases"
    cmd_prefix = ""
    if not cmd.startswith("/"):
        cmd_prefix = f"{deploy_path}/{project_name}-{version}"
    docker_cmd = (f"podman run --rm -i -t -v $PWD:/build "
                  f"-e tarball_name={tarball_name} -e deploy_path={deploy_path} --env-file={env_file} "
                  f"-e project_name={project_name} -e version={version} "
                  f"-p 8000:8000 "
                  f"{docker_image} "
                  f"/bin/bash -c 'cd /build && ls && tar xzf {tarball_name} && mkdir -p {deploy_path} && "
                  f"mv {project_name} {project_name}-{version} && "
                  f"mv {project_name}-{version} {deploy_path} && "
                  f"{cmd_prefix}/{cmd}'")
    with c.cd("build"):
        print(docker_cmd)
        ret = c.run(docker_cmd, pty=True)
        print(ret)

@task
def deploy(c, tarball):
    tarball_path = os.path.realpath(open(tarball).name)
    print(tarball_path)
    hosts = ",".join(c.webship["deploy"]["hosts"].split())
    project_name, version = tarball_path.split("/")[-1].split("-")
    deploy_path = f"/app/{project_name}/releases"
    filename = tarball_path.split("/")[-1]
    version = version.strip(".tar.gz")
    print(tarball_path, deploy_path, project_name, version, filename)

    def upload_and_unpack(c):
        #if c.run('test -f /opt/mydata/myfile', warn=True).failed:
        print(f"Copying {tarball_path} to {c.host} ...")
        c.put(tarball_path)
        target_dir = f"{deploy_path}/{project_name}-{version}"
        print(f"Checking {target_dir} exists...")
        if not c.run(f"test -d {target_dir}", warn=True).failed:
            print(f"{target_dir} exists")
            if not confirm():
                return
        print(f"Extracting tarball to {target_dir}")
        c.sudo(f"tar -C {deploy_path} -xzvf {filename}", hide=True)
        print(f"Deleting existing {target_dir}")
        c.sudo(f"rm -r {target_dir}")
        c.sudo(f"mv {deploy_path}/{project_name} {deploy_path}/{project_name}-{version}")
        print("copying env file")
        c.put("env", f"{target_dir}/.env")

    for connection in SerialGroup(hosts):
        upload_and_unpack(connection)
