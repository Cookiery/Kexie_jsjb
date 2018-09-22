# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from craft.models import Formula
import hashlib
import redis
import time
import json
import uuid

TOKEN = "laoganbunvzhuang"
r_belonging = redis.Redis(db=0)


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
def f_craft(request):
    # 用户验证
    if request.method == "GET":
        return HttpResponseForbidden()
    data = json.loads(request.body.decode('utf-8'))
    openid = data.get("openid")
    sign = data.get("sign")
    nonce = data.get("nonce")
    if sign != hashlib.md5(openid + TOKEN + nonce).hexdigest():
        return HttpResponseForbidden()
    # 合成逻辑
    items_str = data.get("items")
    formulas = Formula.objects.filter(formula=items_str)
    if len(formulas):
        return JsonResponse({"status": "Error", "Error": "FormulaWrong"})
    items_dic = json.loads(formulas[0].items)
    temp_uuid = uuid.uuid4().__str__()
    if not redis_lock(openid, temp_uuid):
        return JsonResponse({"status": "Error", "Error": "LockError"})
    items_counts = r_belonging.hgetall(openid)
    for item, delta in items_dic.items():
        item_count = items_counts.get(item)
        if item_count is None:
            item_count = 0
        else:
            item_count = int(float(item_count))
        if item_count + int(delta) < 0:
            return JsonResponse({"status": "Error", "Error": "LockError"})
    for item, delta in items_dic.items():
        item_count = items_counts.get(item)
        if item_count is None:
            item_count = int(delta)
        else:
            item_count = int(float(item_count)) + int(delta)
        r_belonging.hset(openid, item, item_count)
    if not redis_unlock(openid, temp_uuid):
        return JsonResponse({"status": "Error", "Error": "UnlockError"})
    return JsonResponse({"status": "Success"})
