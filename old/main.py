import typer
import os
# from typing_extensions import Annotated, Optional
from os import path as p
from enum import Enum
from typing import Literal, TypeVar, Generic, Iterable, Optional, Union, cast, Annotated, get_type_hints, Protocol, runtime_checkable, List, Dict, Sequence
from dataclasses import dataclass
import click
import click
import os
from enum import Enum
from typing import Optional
import test2

print(test2.E)

exit()

app = typer.Typer(no_args_is_help=True)

# def main(name: str = typer.Argument(...)):
#   print(f"Hello {name}")


class CompilationMode(Enum):
  app = 'app'
  script = 'script'
  bundle = 'bundle'


class DependenciesCompilationMode(Enum):
  script = 'script'
  bundle = 'bundle'


class DependenciesInstallationMode(Enum):
  app = 'app'
  user = 'user'
  system = 'system'


# @app.callback(invoke_without_command=True)
@app.command()
def compile(
    project_dir: Annotated[
        Optional[str],
        typer.Argument(
            help=
            'Working directory. Place where the project is located. Defaults to the current directory'
        )] = os.getcwd(),
    comp_mode: Annotated[
        CompilationMode,
        typer.Option(
            help=
            'Whether to compile the main source to a standalone app (e.g. applet/droplet) or a script'
        )] = 'app',
    deps_comp_mode: Annotated[
        DependenciesCompilationMode,
        typer.Option(
            help=
            'Dependencies compilation mode. Whether dependencies should be compiled as scripts or bundles'
        )] = 'script',
    deps_install_mode: Annotated[
        DependenciesInstallationMode,
        typer.Option(
            help=
            'Where to install dependencies. If the main file is compiled to a standalone app one can embed them inside. Otherwise they can be installed for a current user, or system wide'
        )] = 'app',
    version: Annotated[str,
                       typer.Option(help='Version of the project')] = '1.0.0',
    main_file: Annotated[str,
                         typer.Option(help='Main source file')] = 'index.js',
    app_name: Annotated[
        str,
        typer.Option(
            help='App name, (has effect only when compiling to a standalone app)'
        )] = 'out',
    app_icon: Annotated[
        str,
        typer.Option(
            help=
            'By default the builder searches for "icon.icns" or "<app-name>.icns" in the working directory. If both icons are not found and this option is left empty, the default icon is used (has effect only when compiling to a standalone app)'
        )] = '',
    debug_info: Annotated[
        bool,
        typer.Option(
            '--debug-info',
            help=
            'Whether to add some useful information. (mainly used for testing purposes)'
        )] = False,
    install_after: Annotated[
        bool,
        typer.Option('--install-after',
                     help='Whether to run "install" command after building'
                     )] = False,
    deps_only: Annotated[
        bool,
        typer.Option(
            '--deps-only',
            help=
            'Whether to install the app and it\'s dependencies or only the dependencies'
        )] = False,
    package_name: Annotated[Optional[str],
                            typer.Option(help='Package name')] = None,
):
  typer.echo(f"{project_dir}")


@app.command()
def install(locations_file: Annotated[str,
                                      typer.Argument(
                                          show_default='./build/locations.json'
                                      )] = p.join(os.getcwd(), 'build',
                                                  'locations.json'),
            dependencies_only: Annotated[bool, typer.Option()] = False):
  typer.echo(f"{locations_file}, {dependencies_only}")


@app.command()
def uninstall(locations_file: Annotated[
    Optional[str],
    typer.Argument(show_default='./build/locations.json')] = p.join(
        os.getcwd(), 'build', 'locations.json')):
  typer.echo(f"{locations_file}")


if __name__ == "__main__":
  app()
