# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Level(models.Model):
    level = models.CharField(max_length=3, verbose_name=u"等级")
    token = models.CharField(max_length=32)
    items = models.TextField()  # JSON: {item_id:count}, 获得的物品

    def __str__(self):
        return self.token

    class Meta:
        verbose_name = u"战斗等级"
        verbose_name_plural = verbose_name
