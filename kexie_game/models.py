# -*- coding: utf-8 -*-
from django.db import models


class User(models.Model):
    openid = models.CharField(max_length=30)
    level = models.IntegerField(default=0, verbose_name=u"等级")
    nickname = models.CharField(max_length=64, verbose_name=u"匿名")
    isBan = models.BooleanField(default=False, verbose_name=u"封禁")
    history_items = models.TextField()  # JSON:[1, 2, 3, 5]
    img = models.CharField(max_length=128, verbose_name=u"头像")
    daily_sign = models.BooleanField(default=False, verbose_name=u"日签到")
    weekly_sign = models.IntegerField(default=0, verbose_name=u"周签到")
    sign_count = models.IntegerField(default=0, verbose_name=u"签到次数")

    def __str__(self):
        return self.nickname

    class Meta:
        verbose_name = u"用户"
        verbose_name_plural = verbose_name
