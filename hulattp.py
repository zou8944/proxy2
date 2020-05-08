import hashlib
import json
import re
import time
import uuid


def dict2str(dic):
    result = "{"
    for key in sorted(dic.keys(), reverse=True):
        result += "{}:".format(key)
        value = dic[key]
        if type(value) is dict:
            result += dict2str(value)
        elif type(value) is list:
            result += array2str(value)
        else:
            result += json.dumps(value, ensure_ascii=False).replace("\"", "")
        result += ","
    result = result[:-1] + "}"
    return result


def array2str(arr):
    result = "["
    for item in arr:
        if type(item) is dict:
            result += dict2str(item)
        elif type(item) is list:
            result += array2str(item)
        else:
            result += json.dumps(item, ensure_ascii=False).replace("\"", "")
        result += ","
    result = result[:-1] + "]"
    return result


def dict2list(dic):
    l = []
    for key in dic.keys():
        value = dic[key]
        value_type = type(value)
        temp = "{}=".format(key)
        if value_type is dict:
            temp += dict2str(value)
        elif value_type is list:
            temp += array2str(value)
        else:
            temp += json.dumps(value, ensure_ascii=False).replace("\"", "")
        l.append(temp)
    return l


def generate_headers(path, params, body):
    timestamp = str(int(time.time() * 1000))
    requestId = str(uuid.uuid1())
    candidates = ["X-RequestId={}".format(requestId), "X-Timestamp={}".format(timestamp)]
    for key in params:
        candidates.append("{}={}".format(key, params[key]))
    for item in dict2list(body):
        candidates.append(item)
    candidates.sort(reverse=True)
    candidate_str = "{}^".format(path)
    for i in range(len(candidates)):
        if i == len(candidates) - 1:
            candidate_str += candidates[i]
        elif i % 2 == 0:
            candidate_str += "{}|".format(candidates[i])
        else:
            candidate_str += "{}&".format(candidates[i])
    candidate_str += "^"
    print candidate_str
    return {
        "X-RequestId": requestId,
        "X-Timestamp": timestamp,
        "X-Signature": hashlib.sha256(candidate_str.encode("utf-8")).hexdigest()
    }


def pre_request(req, req_body):
    segs = re.sub(r"http[s]?://[\w.]+", "", req.path).split("?")
    path = segs[0]
    params = {}
    if len(segs) > 1:
        param_segs = segs[1].split("&")
        for param_seg in param_segs:
            key_value = param_seg.split("=")
            params[key_value[0]] = key_value[1]
    if "content-type" in req.headers and "application/json" in req.headers["content-type"]:
        try:
            body = json.loads(req_body)
        except Exception as e:
            body = {}
    else:
        body = {}
    for item in generate_headers(path, params, body).items():
        req.headers[item[0]] = item[1]
