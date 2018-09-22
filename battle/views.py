# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from kexie_game.views import change_count
from kexie_game.models import User
from battle.models import Level
import hashlib
import redis
import json

TOKEN = "laoganbunvzhuang"
r_belonging = redis.Redis(db=0)  # OpenID-{item_id: count}
r_expire = redis.Redis(db=2)  # PortalID-LastMinerTime


@csrf_exempt
def join(request):
    # 用户验证
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    openid = data.get("openid")
    sign = data.get("sign")
    nonce = data.get("nonce")
    if sign != hashlib.md5(openid + TOKEN + nonce).hexdigest():
        return HttpResponseForbidden()

    # 进入战斗
    level = int(data.get("level"))
    if r_belonging.exists(openid):
        items = [{"id": key, "count": value} for key, value in r_belonging.hgetall(openid).items()]
    else:
        items = []
    u = User.objects.get(openid=openid)
    if level > u.level + 1:
        return JsonResponse({"status": "Error", "Error": "LevelWrong"})
    return JsonResponse({"status": "Success", "items": items})


def end(request):
    # 用户验证
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    openid = data.get("openid")
    sign = data.get("sign")
    nonce = data.get("nonce")
    if sign != hashlib.md5(openid + TOKEN + nonce).hexdigest():
        return HttpResponseForbidden()

    # 战斗结算
    level = data.get("level")
    l = Level.objects.get(level=level)
    level_token = data.get("token")
    if level_token != l.token:
        return JsonResponse({"status": "Error", "Error": "LevelWrong"})
    items = json.loads(l.items)
    for item_id, count in items.items():
        change_count(int(count), item_id, openid)
    return JsonResponse({"status": "Success", "items": [{"id": key, "count": value} for key, value in items.items()]})
