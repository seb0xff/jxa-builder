from jxa_builder.utils.click_importer import click
from jxa_builder.commands.build import build
from jxa_builder.commands.install import install
from jxa_builder.commands.uninstall import uninstall
from jxa_builder.commands.freeze_nodejs_deps import freeze_nodejs_deps


@click.group(
    context_settings=dict(help_option_names=["-h", "--help"]),
    help=
    'A build system for Javascript for Automation.\n\nTo turn on classic display mode set JXA_BUILDER_CLASSIC_DISPLAY_MODE env variable to true.'
)
def cli():
  pass


cli.add_command(build)
cli.add_command(install)
cli.add_command(uninstall)
cli.add_command(freeze_nodejs_deps)

if __name__ == "__main__":
  cli()
