import click
from flask.cli import AppGroup

from app.views import app
from app.tools import demo


task_cli = AppGroup("task")
app.cli.add_command(task_cli)


@task_cli.command(
    "print-demo-person", 
    help="Generate a sample person translation in JSON format."
)
@click.argument("title")
@click.option("-k", type=int, default=2)
def print_person(title, k):
    """Generate a person translation.
    
    Args:
        title: The Wikipedia article title to translate
        k: Number of languages to chain in the translation
    """
    demo.print_person(title, k)

@task_cli.command(
    "print-demo-movie", 
    help="Generate a movie translation in JSON format."
)
@click.argument("title")
@click.option("-k", type=int, default=2)
def print_movie(title, k):
    """Generate a movie translation.
    
    Args:
        title: The Wikipedia article title to translate
        k: Number of languages to chain in the translation
    """
    demo.print_movie(title, k)
