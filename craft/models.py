# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Formula(models.Model):
    formula = models.CharField(max_length=30, verbose_name=u"合成公式")
    items = models.TextField()  # JSON: {item_id:delta(消耗品为负，获得物为正)}

    def __str__(self):
        return self.formula

    class Meta:
        verbose_name = u"合成方式"
        verbose_name_plural = verbose_name
