from django.contrib.admin.tests import AdminSeleniumWebDriverTestCase
from django.contrib.staticfiles.testing import StaticLiveServerCase
from django.contrib.auth.models import User

from daguerre.tests import models
from daguerre.tests import admin
from daguerre.tests.base import BaseTestCase

from selenium import webdriver

class AreaWidgetTestCase(BaseTestCase, StaticLiveServerCase):

    # Borrow some methods from Django's `AdminSeleniumWebDriverTestCase`
    admin_login = AdminSeleniumWebDriverTestCase.admin_login.__func__
    wait_page_loaded = AdminSeleniumWebDriverTestCase.wait_page_loaded.__func__
    wait_loaded_tag = AdminSeleniumWebDriverTestCase.wait_loaded_tag.__func__
    wait_for = AdminSeleniumWebDriverTestCase.wait_for.__func__
    wait_until = AdminSeleniumWebDriverTestCase.wait_until.__func__

    @classmethod
    def setUpClass(cls):
        cls.selenium = webdriver.Firefox()
        super(AreaWidgetTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(AreaWidgetTestCase, cls).tearDownClass()

    def open(self, path):
        self.selenium.get("{}{}".format(self.live_server_url, path))

    def test_image_loads(self):

        # Create a user
        user = User.objects.create(username="super", is_staff=True,
            is_superuser=True)
        user.set_password("secret")
        user.save()

        # Upload an image and create a BasicImageModel
        image = self.create_image("100x100.png")
        models.BasicImageModel.objects.create(image=image)

        self.admin_login(username="super", password="secret",
            login_url="/admin/")

        self.open("/admin/daguerre/basicimagemodel/1/")

        # TODO: Finish this test.