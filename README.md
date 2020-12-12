Tools to deploy python web application. The build process is run in container
using podman so make sure you have podman properly setup on the build machine.

## Install

    pipx install webship

## Usage

Create directory to hold the deploy project:-

    mkdir -p myapp_deploy

Create `webship.ini` to hold configuration about the deploy:-

```
[fetch]
repo = git@github.com:xoxzoeu/myapp.git
clone_args = recursive

[deploy]
path = /app/myapp
hosts =
    127.0.0.1
    127.0.0.2
```

To build the app:-

    webship fetch
    webship build myapp 1.0.1 --docker_image=myapp

That will generate the release tarball in `build/myapp-1.0.1.tar.gz`. Before
deploying the release tarball, we can test it first to make sure everything
is working as expected:-

    webship run build/myapp-1.0.1.tar.gz ".venv/bin/myapp manage runserver 0.0.0.0:8000" --env-file=/home/kamal/python/myapp_deploy/env 

To deploy:-

    webship deploy build/myapp-1.0.1.tar.gz

Deploy directory structure is like below:-

```
    deploy_path (default to /app/<project_name>)
        releases/
        current --> releases/<project_name>-0.0.1
```

Active release will be `/app/<project_name>/current` which is a symlink to active version. This
structure will allow multiple apps to be deployed on the same server.
