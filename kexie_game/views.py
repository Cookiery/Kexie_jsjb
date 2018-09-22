# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from kexie_game.models import User
import requests
import hashlib
import redis
import time
import json
import uuid

APPID = "wx6b9e0961249fab65"
SECRET = "ab8fd7aa013524e798de9d200532f8c4"
TOKEN = "laoganbunvzhuang"
r_belonging = redis.Redis(db=0)  # OpenID-{item_id: count}
r_ranking = redis.Redis(db=1)


class LockError(Exception):
    pass


class UnlockError(Exception):
    pass


def redis_lock(uid, temp_id):
    wait = 0
    while r_belonging.set("lock" + uid, temp_id, nx=True, ex=10) is None:
        time.sleep(0.001)
        wait += 1
        if wait > 10000:
            return False
    return True


def redis_unlock(uid, temp_id):
    wait = 0
    while r_belonging.set("unlock" + uid, temp_id, nx=True, ex=10) is None:
        time.sleep(0.001)
        wait += 1
        if wait > 10000:
            return False
    if r_belonging.get("lock" + uid) == temp_id:
        r_belonging.delete("lock" + uid, "unlock" + uid)
    else:
        r_belonging.delete("unlock" + uid)
        return False
    return True


@csrf_exempt
def login(request):
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    code = data.get("code")
    r = requests.get("https://api.weixin.qq.com/sns/jscode2session?",
                     params={"appid": APPID, "secret": SECRET, "js_code": code, "grant_type": "authorization_code"})
    openid = r.json().get("openid", None)
    if openid is None:
        return JsonResponse({"status": "Error", "Error": "UnableGetOpenID"})
    # 获取到OpenID
    u = User.objects.filter(openid=openid)
    is_first = not len(u)
    if not len(u):
        u = User.objects.create(openid=openid)
    else:
        u = u[0]
    if r_belonging.exists(openid):
        items = [{"id": key, "count": value} for key, value in r_belonging.hgetall(openid).items()]
    else:
        items = []
    return JsonResponse(
        {"nickname": u.nickname, "img": u.img, "isBan": u.isBan, "items": items, "level": u.level,
         "history_items": json.loads(u.history_items), "openid": openid, "sign": u.daily_sign, "isFirst": is_first})


@csrf_exempt
def belongings_get(request):
    # 用户验证
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    openid = data.get("openid")
    sign = data.get("sign")
    nonce = data.get("nonce")
    if sign != hashlib.md5(openid + TOKEN + nonce).hexdigest():
        return HttpResponseForbidden()
    # 获取信息
    if r_belonging.exists(openid):
        items = [{"id": key, "count": value} for key, value in r_belonging.hgetall(openid).items()]
    else:
        items = []
    u = User.objects.get(openid=openid)
    return JsonResponse({"items": items, "Craftable": json.loads(u.history_items)})


@csrf_exempt
def sign_in(request):
    # 用户验证
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    openid = data.get("openid")
    sign = data.get("sign")
    nonce = data.get("nonce")
    if sign != hashlib.md5(openid + TOKEN + nonce).hexdigest():
        return HttpResponseForbidden()
    # 获取信息
    u = User.objects.get(openid=openid)
    u.weekly_sign += 10 ** (6 - time.localtime(time.time()).tm_wday)
    u.daily_sign = True
    u.sign_count += 1
    u.save()
    return JsonResponse({"weekly": "%07d" % u.weekly_sign, "sign_count": u.sign_count, "daily_sign": u.daily_sign})


@csrf_exempt
def ranking(request):
    key_list = r_ranking.keys()
    ranked_list = sorted([{"score": float(r_ranking.get(key)), "nickname": User.objects.get(openid=key).nickname}
                          for key in key_list], key=lambda rank_item: -rank_item["score"])
    return JsonResponse({"users": ranked_list})


@csrf_exempt
def info(request):
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    openid = data.get("openid")
    # 获取到OpenID后获取信息
    u = User.objects.get(openid=openid)
    if r_belonging.exists(openid):
        items = [{"id": key, "count": value} for key, value in r_belonging.hgetall(openid).items()]
    else:
        items = []
    return JsonResponse(
        {"nickname": u.nickname, "img": u.img, "isBan": u.isBan, "items": items, "level": u.level,
         "history_items": json.loads(u.history_items), "openid": openid, "sign": u.daily_sign})


def change_count(delta, item_id, openid, focus=False):
    """
    改变用户仓库内物品数量，种类
    :param int delta:
    :param str item_id:
    :param str openid:
    :param bool focus:
    :return:是否成功改变
    :rtype: bool
    :raises LockError:if redis is unable to lock, and waiting for more than 10 second.
    """
    focus = True if delta > 0 and not focus else False
    temp_uuid = uuid.uuid4().__str__()
    if not redis_lock(str(openid), temp_uuid):
        raise LockError
    item_count = r_belonging.hget(openid, item_id)
    if item_count is None:
        item_count = 0
    else:
        item_count = int(float(item_count))
    if item_count + delta < 0 and not focus:
        if not redis_unlock(str(openid), temp_uuid):
            raise UnlockError
        return False
    total_count = 20000000 if item_count + delta > 20000000 else item_count + delta
    r_belonging.hset(openid, item_id, total_count)
    if not redis_unlock(str(openid), temp_uuid):
        raise UnlockError
    return True


def get_count(openid, item_id):
    # type: (int, str) -> int
    """
    获取UID用户仓库指定item_id物品内容个数
    :param int openid: 用户UID
    :param str item_id: 物品识别号ItemID
    :rtype: int
    :return: 数量
    """
    item_count = r_belonging.hget(openid, item_id)
    if item_count is None:
        item_count = 0
    else:
        item_count = int(float(item_count))
    return item_count
