# python-project-starter

This repository is a define practices for AIT Brainlab to follow.
All `python` project should look like this and follow the standard.

- [python-project-starter](#python-project-starter)
  - [Implemented standard](#implemented-standard)
  - [TODO](#todo)
  - [Project structure](#project-structure)
  - [How to use this](#how-to-use-this)
    - [Change project name](#change-project-name)
    - [Setup development](#setup-development)
    - [Command Script](#command-script)
    - [Install command script completion](#install-command-script-completion)
  - [Django Setup](#django-setup)
    - [Start a new app module](#start-a-new-app-module)
  - [License](#license)

## Implemented standard

1. Project structure
2. logging system
3. command line (with `Typer`)
4. basic web server and REST API (`with FastAPI and Jinja`)
5. processor module with celery support (options for those who may not need `pub-sub/queue`)
6. Define how Django should be implemented.

## TODO

- [ ] Distribution standard (containerize for distribution)
- [ ] Chat/LLM standard (interface, prompt, mcp)
- [ ] tools/framework (some other github repo)

## Project structure

```
.
|-- .devcontainer/               # Where the development containers are defined
|-- .vscode/                     # Where the vscode related configuration are kept
|-- data                         # ! Where data is kept. All the data are ignored by default.
|   `-- example.csv
|-- docs/                        # ! Where document (design, paper, any for reference) is kept. 
|-- logs/                        # Where logs are kept.
|-- models/                      # ! Where models (weight) should be stored.
|-- notebooks/                   # ! Where jupyter notebook should be stored.
|   `-- 0-starter.ipynb
|-- src/                         # ! Where development modules should be.
|   |-- django_core              # |
|   |   |-- __init__.py          # | 
|   |   |-- asgi.py              # | 
|   |   |-- settings.py          # | 
|   |   |-- urls.py              # | 
|   |   `-- wsgi.py              # | 
|   |-- django_module            # | 
|   |   |-- __init__.py          # |--- These are `Django` related structure
|   |   |-- admin.py             # | 
|   |   |-- apps.py              # | 
|   |   |-- migrations           # | 
|   |   |   `-- __init__.py      # | 
|   |   |-- models.py            # | 
|   |   |-- tests.py             # | 
|   |   `-- views.py             # | 
|-- django_manage.py             # | 
|   |-- project                  # Example modules with Brainlab practice.
|       |-- __init__.py
|       |-- cli.py
|       |-- logger.py
|       |-- processor
|       |   |-- __init__.py
|       |   |-- works.py
|       |   `-- works_test.py
|       |-- processor_celery
|       |   |-- __init__.py
|       |   |-- cli.py
|       |   |-- works.py
|       |   `-- works_test.py
|       `-- web
|           |-- __init__.py
|           |-- py.typed
|           |-- router.py
|           `-- templates
|               |-- base.html
|               |-- example.html
|               `-- index.html
|-- .gitignore
|-- .python-version
|-- dev-setup.sh                 # ! run this one when you cloned
|-- LICENSE
|-- local.env.example            # ! copy and create `local.env`
|-- pyproject.toml               # python configuration. You have to change this.
|-- README.md
|-- supervisord.conf             # ! if you want to run multiple processes at the same time, learn this one
`-- uv.lock
```

## How to use this

There are three main tools we use to manage the project.

1. `uv`: python project manager
2. devcontainer: where we spin development environment
3. `mypy`: a complier-ish that will check if your code meet certain standard

### Change project name

We intend that this repository will be used as a template for `python` development.
There are a lot of places where we have to add a `python-project-start` string to make this run properly.
You should change this name to follow your project/module name.

To change the name, you start from your project/repository name.

```sh
/some/path/to/your/repository/<project_name>
```

Let's say we will create another project based on this template with name `myproject`

```sh
/some/path/path/to/your/repository/myproject
```

The place where you need to change the name are

1. `/.devcontainer/dev/.env`: parameter `PROJECT_NAME`
2. `pyproject.toml`: parameter `project.name`
3. `local.env.example`: parameter `PROJECT_NAME`

This should be enough for you to start developing.

### Setup development

1. (optional) spin up devcontainer in vscode (<kbd>cmd/ctrl</kbd> + <kbd>shift</kbd> + <kbd>P</kbd> and choose `Dev Containers: Rebuild and reopen in Container`)
2. Set up the development environment in one go using `bash dev-setup.sh`

### Command Script

The project has a command script.
By default it uses `python-project-starter`.

```sh
uv run python-project-starter --help
```

If you want to change this command name, you have to configure the following

1. `pyproject.toml`: under section `project.scripts`, change the command name
2. `supervisord.conf`: This use your command name to spawn processes

### Install command script completion

Command line solution uses `Typer` library which has completion capabitily.
After you write the command name, you can use <kbd>tab</kbd> to get suggestion/completion.

This functionality is automatically set for if you use `.devcontainer`.
For local user, you will need to run this manually (because I don't know if you want this install in your computer).

```sh
uv run <command_name> --install-completion
```

To remove this, get the intallation path from the command and delete the file manually.

## Django Setup

Let's agree that we should develop a `Django app module` not an entire Django website.
In this AIT Brainlab best practice, the folders that are related to the Django are

```sh
...
|-- src/                         
|   |-- django_core              # |
|   |   |-- __init__.py          # | 
|   |   |-- asgi.py              # | 
|   |   |-- settings.py          # | 
|   |   |-- urls.py              # | 
|   |   `-- wsgi.py              # | 
|   |-- django_module            # | 
|   |   |-- __init__.py          # |--- These are `Django` related structure
|   |   |-- admin.py             # | 
|   |   |-- apps.py              # | 
|   |   |-- migrations           # | 
|   |   |   `-- __init__.py      # | 
|   |   |-- models.py            # | 
|   |   |-- tests.py             # | 
|   |   `-- views.py             # | 
|-- django_manage.py             # | 
...
```

The provided `django_core` is configuration for the development purposes.
The production may have different configuration.
Thus, your main development should be a modular module that is compatible with any django project.

To access typical django operation, you use

```sh
uv run django_manage.py
```

For example, if you want to start the development server, you use

```sh
uv run django_manage.py runserver 0.0.0.0:8000
```

### Start a new app module

Generate a django app boilerplate

```sh
#                       startapp <app_name> <app_folder>
uv run django_manage.py startapp myapp src/myapp
```

Then, add the module to the development project settings (`/src/django_core/settings.py`)

```py
...
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp'  # <---- Add here
]
...
```

Finally, add the routing in `/src/django_core/urls.py`

```py
...
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path("myapp/", include("myapp.urls")),  #<---- Add here
]
...
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
