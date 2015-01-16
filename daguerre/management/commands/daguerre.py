import os
import sys

try:
    from django.apps import apps
except ImportError:
    apps = None
    from django.core.management import find_management_module
from django.core.management import load_command_class
from django.core.management.base import BaseCommand
from django.utils.encoding import smart_str


NO_ARGS = """The daguerre management command requires a subcommand.

"""


class Command(BaseCommand):
    def _find_commands(self):
        if apps:
            parts = (apps.get_app_config('daguerre').path,
                     'management', 'commands')
        else:
            parts = (find_management_module('daguerre'),
                     'commands')
        command_dir = os.path.join(*parts)
        try:
            return dict((f[10:-3], f[:-3]) for f in os.listdir(command_dir)
                        if f.startswith('_daguerre_') and f.endswith('.py'))
        except OSError:
            return {}

    def _error(self, msg):
        sys.stderr.write(smart_str(self.style.ERROR(msg)))
        sys.exit(1)

    def _valid_commands(self):
        commands = self._find_commands()
        return "Valid daguerre subcommands are:\n\n{0}".format(
            "\n".join(commands)) + "\n\n"

    def _get_command(self, command, *args, **options):
        commands = self._find_commands()
        if command not in commands:
            self._error("Unknown command: {0}\n\n".format(command) +
                        self._valid_commands())
        return load_command_class('daguerre', commands[command])

    def run_from_argv(self, argv):
        if len(argv) < 3:
            self._error(NO_ARGS + self._valid_commands())
        command = self._get_command(argv[2])
        new_argv = [argv[0], "{0} {1}".format(*argv[1:3])] + argv[3:]
        command.run_from_argv(new_argv)

    def execute(self, *args, **options):
        if not args:
            self.stderr.write()
            self._error(NO_ARGS + self._valid_commands())
        command = self._get_command(args[0])
        command.execute(*args[1:], **options)
