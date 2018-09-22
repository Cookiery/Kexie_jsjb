# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Portal(models.Model):
    latitude = models.FloatField(verbose_name=u"纬度")
    longitude = models.FloatField(verbose_name=u"经度")
    type = models.BooleanField(default=False)
    question = models.CharField(default="", max_length=512)
    name = models.CharField(max_length=32)
    item_type = models.CharField(max_length=32)
    item_base_count = models.IntegerField()

    def __str__(self):
        return self.name

