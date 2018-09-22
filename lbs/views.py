# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from kexie_game.views import change_count
from lbs.models import Portal
import hashlib
import random
import redis
import time
import json

TOKEN = "laoganbunvzhuang"
r_expire = redis.Redis(db=2)  # PortalID-LastMinerTime


def redis_lock(uid, temp_id):
    wait = 0
    while r_expire.set("lock" + uid, temp_id, nx=True, ex=10) is None:
        time.sleep(0.001)
        wait += 1
        if wait > 10000:
            return False
    return True


def redis_unlock(uid, temp_id):
    wait = 0
    while r_expire.set("unlock" + uid, temp_id, nx=True, ex=10) is None:
        time.sleep(0.001)
        wait += 1
        if wait > 10000:
            return False
    if r_expire.get("lock" + uid) == temp_id:
        r_expire.delete("lock" + uid, "unlock" + uid)
    else:
        r_expire.delete("unlock" + uid)
        return False
    return True


def normal_random(center, delta):
    """
    产生伪正态分布随机数
    :param int center: 期望
    :param int delta: 变化最大值
    :return: 伪正态分布随机数[center - delta, center + delta]
    :rtype: float
    """
    l = list()
    l.append(random.random())
    time.sleep(0.001)
    l.append(random.random())
    time.sleep(0.001)
    l.append(random.random())
    random_rate = sum(l) / 3.0
    return center + delta * (2 * random_rate - 1)


def portal_map(request):
    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    # 列出当前所有节点
    portals = Portal.objects.all()
    portal_list = []
    for p in portals:
        expire_time = r_expire.ttl(p.id)
        expire_time = int(expire_time) if expire_time is not None else 0
        portal_list.append({
            "id": p.id,
            "position": {"latitude": p.latitude, "longitude": p.longitude},
            "type": p.type,
            "question": p.question,
            "name": p.name,
            "distance": pow(sum(pow((p.latitude - latitude), 2), pow((p.longitude - longitude), 2)), 0.5),
            "expire": expire_time,
            # "rich_type": int((300 - expire_time) / 60),
            "item_type": p.item_type
        })
    sort_portal_list = sorted(portal_list, key=lambda i: i["distance"])
    return JsonResponse({"status": "Success", "portal": sort_portal_list})


@csrf_exempt
def miner(request):
    # 用户验证
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    openid = data.get("openid")
    sign = data.get("sign")
    nonce = data.get("nonce")
    if sign != hashlib.md5(openid + TOKEN + nonce).hexdigest():
        return HttpResponseForbidden()

    # 挖矿逻辑
    portal = data.get("portal")
    p = Portal.objects.get(id=portal)
    expire_time = r_expire.ttl(p.id)
    expire_time = int(expire_time) if expire_time is not None else 0
    rich_type = int((300 - expire_time) / 60)
    if rich_type == 0:
        return JsonResponse({"status": "Error", "Error": "TooHot"})
    item_count = int(normal_random(4, 2)) * rich_type * p.item_base_count
    change_count(item_count, p.item_type, openid)
    r_expire.set(p.id, time.time(), ex=expire_time + 60)
    return JsonResponse({"status": "Success", "rich_type": rich_type, "count": item_count, "item_type": p.item_type})


def portal_info(request):
    portal = request.GET.get("portal")
    p = Portal.objects.get(id=portal)
    expire_time = r_expire.ttl(p.id)
    expire_time = int(expire_time) if expire_time is not None else 0
    rich_type = int((300 - expire_time) / 60)
    return JsonResponse(
        {"status": "Success", "rich_type": rich_type, "base_count": p.item_base_count, "item_type": p.item_type})
