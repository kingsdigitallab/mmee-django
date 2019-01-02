import csv
import logging
import re

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from photos.models import (Photo, Photographer, PhotoCategory,
                           PhotoSubcategory)
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

        parser.add_argument(
            '--append',
            action='store_true',
            dest='append',
            help='append photos, even if records already exist.'
            ' For testing purpose.',
        )

        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            help='CLEAR all photo records before importing',
        )

    def handle(self, *args, **options):
        self.append_only = options.get('append', False)

        if options.get('reset', False):
            self.erase_all_data()

        self.image_path = options.get('image_path', None)

        with open(options['spreadsheet_path'][0]) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.import_row(row)

    def erase_all_data(self):
        '''Remove all image, photo, photographers, subcat and cat from DB'''
        for m in [Photo, Image, PhotoSubcategory, PhotoCategory, Photographer]:
            print('Erasing all {} records'.format(m))
            m.objects.all().delete()

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
        if photo is None:
            return photo

        terms = row.get('thesaurus_term', '')
        # Artefact; commemorative; mural
        terms = [t.strip() for t in terms.split(';')]

        if len(terms) > 1:
            term = terms.pop(0)
            # TODO: improve the parsing for more advanced cases
            cat, created = PhotoCategory.objects.get_or_create(label=term)

            _print_operation(cat, created)

            subcats = []
            while terms:
                term = terms.pop(0)
                subcat, created = PhotoSubcategory.objects.get_or_create(
                    category=cat, label=term
                )
                subcats.append(subcat)
                _print_operation(subcat, created)
            photo.subcategories.set(subcats)

        return photo

    def import_photo(self, row, photographer):
        '''
        Add or update a Photograph record from the given CSV row.
        '''
        ret = None

        image = self.get_or_create_image(row)
        if not image:
            print('WARNING: image file not found {}'.format(
                row['filename']
            ))
            return ret

        created = False
        if not self.append_only:
            ret = Photo.objects.filter(image=image).first()

        if not ret:
            ret = Photo()
            created = True

        date_parts = _parse_date(row['date'])
        photo = {
            'taken_year': date_parts.year,
            'taken_month': date_parts.month,
            'taken_day': date_parts.day,
            'photographer': photographer,
            'description': (row['description'] or ''),
            'comments': row['comments'],
            'image': image,
        }
        coords = row['dd_co_ordinates']
        if coords:
            coords = coords.split()
            photo['location'] = Point(float(coords[1]), float(coords[0]))

        for field in photo:
            if photo[field]:
                setattr(ret, field, photo[field])

        ret.save()

        _print_operation(ret, created, 'title')

        # Update or Create image file as Wagtail Image
        # .image_title = ~slugify(FILENAME)
        # .file = hash(FILE).jpg

        return ret

    def get_or_create_image(self, row):
        image = None

        if self.image_path and row['filename']:
            path = os.path.join(self.image_path, row['filename'])
            if os.path.exists(path):
                image_title = re.sub(
                    r'[^\w\.]', '-', row['filename'].strip()
                ).lower()
                hash = get_hash_from_file(path)

                image = Image.objects.filter(
                    file__contains=hash
                ).first()

                if not image:
                    new_name = re.sub(r'.*\.', hash + '.', row['filename'])
                    image = Image(
                        file=ImageFile(File(open(path, 'rb')), name=new_name),
                        title=image_title
                    )
                    image.save()

                    _print_operation(image, True, 'title')

        return image

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
            'age_range': Photographer.get_age_range_from_age(row['age_range']),
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

        _print_operation(ret, created)

        return ret


def _print_operation(record, created, display_field=None):
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

    phone_match = re.match(r'.*?(\d{11}).*?', text)

    if phone_match:
        return phone_match.group(1)

    return None


def get_hash_from_file(path):
    chunk_size = 1024 * 1024 * 10
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
