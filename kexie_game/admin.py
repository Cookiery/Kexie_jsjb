from __future__ import unicode_literals
from .models import User
import xadmin


# Register your models here.


class UserAdmin(object):
    list_display = ['openid', 'level', 'nickname', 'history_items', 'sign_count']  # 自定义后台显示内容
    search_fields = ['openid', 'level', 'nickname', 'isBan', 'history_items', 'sign_count']  # 搜索功能
    list_filter = ['openid', 'level', 'nickname', 'isBan', 'history_items', 'sign_count']  # 过滤器


xadmin.site.register(User, UserAdmin)  # 要显示什么导入什么
