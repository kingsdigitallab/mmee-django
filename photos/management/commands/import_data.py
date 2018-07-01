import csv
import logging

from django.core.management.base import BaseCommand
from photos.models import Photographer


class Command(BaseCommand):
    args = '<spreadsheet_path>'
    help = 'Imports data from a spreadsheet'
    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument('spreadsheet_path', nargs=1, type=str)

    def handle(self, *args, **options):
        with open(options['spreadsheet_path'][0]) as f:
            reader = csv.DictReader(f)
            data = [r for r in reader]

            cur_name = None
            # cur_contact = None

            for d in data:
                name = d['Name of photographer']
                if name:
                    cur_name = name
                else:
                    name = cur_name

                # contact = d['contact details']

                photographer, _ = Photographer.object.get_or_create(name=name)
