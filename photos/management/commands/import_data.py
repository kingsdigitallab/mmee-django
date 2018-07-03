import csv
import logging
import re

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from photos.models import MonumentType, Photo, Photographer


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

            cur_email = None
            cur_phone = None
            cur_name = None
            cur_age = None

            for d in data:
                # skips empty rows
                if not d['photo number']:
                    continue

                # Photographer
                email = _get_email(d['contact details'])
                if email:
                    cur_email = email
                else:
                    email = cur_email

                photographer, _ = Photographer.objects.get_or_create(
                    email=email)

                phone = _get_phone(d['contact details'])
                if phone:
                    cur_phone = phone
                else:
                    phone = cur_phone

                photographer.phone_number = phone

                name = d['Name of photographer']
                if name:
                    cur_name = name
                else:
                    name = cur_name

                photographer.name = name

                age = d['Age range']
                if age:
                    age = age[0]
                    cur_age = age
                else:
                    age = cur_age

                photographer.age_range = age

                photographer.save()

                # Photo
                number = d['photo number']
                date = parse_date(d['date'])

                photo, _ = Photo.objects.get_or_create(
                    photographer=photographer, number=number, date=date)
                photo.title = d['description provided by photographer']
                photo.comments = d['additional comments by photographer']

                coords = d['DD co ordinates']
                if coords:
                    coords = coords.split()
                    photo.location = Point(float(coords[1]), float(coords[0]))

                # Terms
                terms = d['Thesaurus term']
                if terms:
                    terms = terms.split(';')
                    for term in terms:
                        monument_type, _ = MonumentType.objects.get_or_create(
                            title=term.strip().lower())
                        photo.monument_type.add(monument_type)

                photo.save()


def _get_email(text):
    if not text:
        return None

    if '@' not in text:
        return None

    items = text.split()
    if '@' in items[0]:
        return items[0]

    return items[1]


def _get_phone(text):
    if not text:
        return None

    phone_match = re.match('.*?(\d{11}).*?', text)

    if phone_match:
        return phone_match.group(1)

    return None
