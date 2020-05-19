# testing.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


"""Support for no database testing."""

from django.test.runner import DiscoverRunner


class DatabaseLessTestRunner(DiscoverRunner):
    """A test suite runner that does not set up and tear down a database."""
    
    
    def setup_databases(self, *args, **kwargs):
        """Overrides DjangoTestSuiteRunner"""
    
    
    def teardown_databases(self, *args, **kwargs):
        """Overrides DjangoTestSuiteRunner"""
