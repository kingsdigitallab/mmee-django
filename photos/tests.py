from django.test import TestCase

from .management.commands.import_data import _get_email, _get_phone


class ImportDataTest(TestCase):
    def setUp(self):
        self.contacts = [
            {'contact': '02077028705 hildalanes@btinternet.com',
                'email': 'hildalanes@btinternet.com', 'phone': '02077028705'},
            {'contact': 'hildalanes@btinternet.com 02077028705',
                'email': 'hildalanes@btinternet.com', 'phone': '02077028705'},
            {'contact': 'hildalanes@btinternet.com',
                'email': 'hildalanes@btinternet.com', 'phone': None},
            {'contact': '02077028705', 'email': None, 'phone': '02077028705'},
            {'contact': '', 'email': None, 'phone': None},
            {'contact': None, 'email': None, 'phone': None},
        ]

    def test_get_email(self):
        for contact in self.contacts:
            self.assertEqual(_get_email(contact['contact']), contact['email'])

    def test_get_phone(self):
        for contact in self.contacts:
            self.assertEqual(_get_phone(contact['contact']), contact['phone'])
