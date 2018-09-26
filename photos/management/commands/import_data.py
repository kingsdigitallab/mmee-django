import csv
import logging
import re

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from photos.models import (Photo, Photographer, PhotoCategory,
                           PhotoSubcategory)
from django.utils.dateparse import parse_date
import os
from django.core.files.base import File
import hashlib
from wagtail.images.models import Image
from django.core.files.images import ImageFile

'''
(venv) ➜  /vagrant git:(develop) ✗ ./manage.py import_data
--image-path="research_data/private/images"
research_data/private/memmap-photos-batch-1.csv
'''


class Command(BaseCommand):
    args = '<spreadsheet_path>'
    help = 'Imports data from a spreadsheet'
    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument('spreadsheet_path', nargs=1, type=str)

        parser.add_argument(
            '--image-path',
            action='store',
            dest='image_path',
            help='Path to image folder',
        )

    def handle(self, *args, **options):
        self.image_path = options.get('image_path', None)

        with open(options['spreadsheet_path'][0]) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.import_row(row)

    def import_row(self, row):
        # normalise the keys and values
        row = {
            (str(k).lower().strip().replace(' ', '_')): str(v).strip()
            for k, v
            in row.items()
        }

        photographer = self.import_photographer(row)

        if not photographer:
            print('WARNING: skip row, no photographer data')
        else:
            photo = self.import_photo(row, photographer)

            self.import_subcategories(row, photo)

        return photo

    def import_subcategories(self, row, photo):
        terms = row.get('thesaurus_term', '')
        # Artefact; commemorative; mural
        terms = [t.strip() for t in terms.split(';')]

        if len(terms) > 1:
            term = terms.pop(0)
            # TODO: improve the parsing for more advanced cases
            cat, created = PhotoCategory.objects.get_or_create(label=term)

            self._print_operation(cat, created)

            subcats = []
            while terms:
                term = terms.pop(0)
                subcat, created = PhotoSubcategory.objects.get_or_create(
                    category=cat, label=term
                )
                subcats.append(subcat)
                self._print_operation(subcat, created)
            photo.subcategories.set(subcats)

        return photo

    def import_photo(self, row, photographer):
        '''
        Add or update a Photograph record from the given CSV row.
        Uses the Photographer and the .
        '''
        photo = {
            'number': row['photo_number'],
            'date': _parse_date(row['date']),
            'photographer': photographer,
        }

        ret, created = Photo.objects.get_or_create(**photo)

        photo.update({
            'description': (row['description'] or ''),
            'comments': row['comments'],
        })

        for field in photo:
            if photo[field]:
                setattr(ret, field, photo[field])

        coords = row['dd_co_ordinates']
        if coords:
            coords = coords.split()
            ret.location = Point(float(coords[1]), float(coords[0]))

        ret.save()

        self._print_operation(ret, created, 'title')

        # Update or Create image file as Wagtail Image
        # .title = slugify(FILENAME)
        # .file = hash(FILE).jpg
        if self.image_path and row['filename']:
            path = os.path.join(self.image_path, row['filename'])
            if os.path.exists(path):
                title = re.sub(
                    '[^\w\.]', '-', row['filename']).lower().strip()

                hash = get_has_from_file(path)

                image = Image.objects.filter(
                    file__contains=hash
                ).first()

                if not image:
                    new_name = re.sub(r'.*\.', hash + '.', row['filename'])
                    image = Image(
                        file=ImageFile(File(open(path, 'rb')), name=new_name),
                        title=title
                    )
                    image.save()

                    self._print_operation(image, True, 'title')
                    ret.image = image
                    ret.save()

        return ret

    def _print_operation(self, record, created, display_field=None):
        operation = 'UP'
        if created:
            operation = 'CR'

        if display_field is None:
            display_name = str(record)
        else:
            display_name = getattr(record, display_field)[:20]

        print('{} {} #{} "{}"'.format(
            operation,
            record.__class__.__name__,
            record.pk,
            display_name
        ))

    def import_photographer(self, row):
        '''
        Add or update a Photographer record from the given CSV row.
        Returns None if no photographer data.
        Uses email as ID or first name + last name if email is missing.
        '''
        photographer = {
            'first_name': row['firstname'],
            'last_name': row['surname'],
            'email': _get_masked_email(row['email']),
            'phone_number': _get_masked_phone(row['phone']),
            'age_range': Photographer.get_age_range_from_str(row['age_range']),
        }

        email = photographer['email']
        if not ''.join([
            (photographer[k] or '')
            for k
            in ['first_name', 'last_name', 'email']
        ]):
            return None

        ret = None
        created = False
        if email:
            ret = Photographer.objects.filter(
                email=photographer['email']).first()
        if not ret and not email:
            ret = Photographer.objects.filter(
                first_name=photographer['first_name'],
                last_name=photographer['last_name'],
            ).first()
        if not ret:
            created = True
            ret = Photographer(**photographer)
        else:
            for field in photographer:
                if photographer[field]:
                    setattr(ret, field, photographer[field])
        ret.save()

        self._print_operation(ret, created)

#         print(photographer)
#         print(ret.first_name, ret.last_name, ret.email)

        return ret

    def handle_old(self, *args, **options):
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
                email = _get_masked_email(d['contact details'])
                if email:
                    cur_email = email
                else:
                    email = cur_email

                photographer, _ = Photographer.objects.get_or_create(
                    email=email)

                phone = _get_masked_phone(d['contact details'])
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
                        pass
#                        monument_type, _ = MonumentType.objects.get_or_create(
#                             title=term.strip().lower())
#                         photo.monument_type.add(monument_type)

                photo.save()


def _parse_date(date_str):
    # YYYY-MM-DD
    # Apr-18
    # 13-Apr-18
    from dateparser import parse

    # Apr-18 => 1-Apr-18
    # otherwise dateparse convert into 18-04-CURRENT_YEAR
    date_str = re.sub(r'(\w+-\d+)', r'01-\1', date_str)
    ret = parse(date_str)

    return ret


# mask parts of the emails and phone numbers


def _get_masked_email(text):
    if not text:
        return None

    if '@' not in text:
        return None

    items = text.split()
    if '@' in items[0]:
        return items[0]

    return items[1]


def _get_masked_phone(text):
    if not text:
        return None

    phone_match = re.match('.*?(\d{11}).*?', text)

    if phone_match:
        return phone_match.group(1)

    return None


def get_has_from_file(path):
    chunk_size = 1024 * 1024 * 10
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
