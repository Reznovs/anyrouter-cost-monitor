#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
import os
import json
import sys
from datetime import datetime


def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    if not os.path.exists(config_path):
        print("错误: 配置文件 config.json 不存在")
        print("请复制 config.example.json 为 config.json 并填写你的账号密码")
        print(f"配置文件路径: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式错误 - {e}")
        sys.exit(1)

    if not config.get("username") or config["username"] == "your_username":
        print("错误: 请在 config.json 中设置你的用户名")
        sys.exit(1)

    if not config.get("password") or config["password"] == "your_password":
        print("错误: 请在 config.json 中设置你的密码")
        sys.exit(1)

    return config


def generate_acw_sc_v2(arg1):
    m = [
        0xF, 0x23, 0x1D, 0x18, 0x21, 0x10, 0x1, 0x26, 0xA, 0x9,
        0x13, 0x1F, 0x28, 0x1B, 0x16, 0x17, 0x19, 0xD, 0x6, 0xB,
        0x27, 0x12, 0x14, 0x8, 0xE, 0x15, 0x20, 0x1A, 0x2, 0x1E,
        0x7, 0x4, 0x11, 0x5, 0x3, 0x1C, 0x22, 0x25, 0xC, 0x24,
    ]
    p = "3000176000856006061501533003690027800375"
    q = [""] * len(m)
    for x in range(len(arg1)):
        for z in range(len(m)):
            if m[z] == x + 1:
                q[z] = arg1[x]
                break
    u = "".join(q)
    v = ""
    for x in range(0, min(len(u), len(p)), 2):
        v += format(int(u[x : x + 2], 16) ^ int(p[x : x + 2], 16), "02x")
    return v


def clear_terminal():
    if os.name == 'nt':
        os.system('cls')
    else:
        print('\033[2J\033[H', end='')


def get_tokens(username, password):
    url = "https://anyrouter.top/api/user/login"
    session = requests.Session()

    try:
        resp1 = session.get(url, timeout=30)
        arg1 = re.search(r"var arg1='([A-F0-9]+)'", resp1.text)
        if not arg1:
            return None, None, None, None

        acw_sc_v2 = generate_acw_sc_v2(arg1.group(1))
        session.cookies.set("acw_sc__v2", acw_sc_v2, domain="anyrouter.top")

        login_resp = session.post(
            f"{url}?turnstile=",
            json={"username": username, "password": password},
            timeout=30
        )
        session_cookie = session.cookies.get("session")

        user_id = None
        display_name = None
        login_data = login_resp.json()
        if login_data.get("success") and "data" in login_data:
            user_id = str(login_data["data"].get("id", ""))
            display_name = login_data["data"].get("username", username)

        return acw_sc_v2, session_cookie, user_id, display_name

    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return None, None, None, None
    except (ValueError, KeyError, AttributeError) as e:
        print(f"解析响应失败: {e}")
        return None, None, None, None


def get_total_cost(acw_sc_v2, session_cookie, user_id, start_timestamp, end_timestamp):
    API_URL = "https://anyrouter.top/api/log/self/stat"
    cookie_str = f"acw_sc__v2={acw_sc_v2}; session={session_cookie}"

    HEADERS = {
        "host": "anyrouter.top",
        "new-api-user": user_id,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://anyrouter.top/console/log",
        "cookie": cookie_str,
    }

    params = {
        "type": "0",
        "token_name": "",
        "model_name": "",
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "group": "",
    }

    try:
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        data = response.json()

        if data.get("success"):
            e = data["data"]["quota"]
            return f"${(e / 500000):.2f}"
        else:
            return None
    except requests.exceptions.RequestException:
        return None
    except (ValueError, KeyError):
        return None


def draw_progress_bar(model_quotas, total_quota, bar_width=50):
    colors = {
        "haiku": "\033[38;2;22;100;255m",
        "sonnet": "\033[38;2;148;239;255m",
        "opus": "\033[38;2;255;196;0m",
    }
    reset = "\033[0m"

    if total_quota == 0:
        print("█" * bar_width)
        return

    bar = ""
    models = ["haiku", "sonnet", "opus"]
    current_length = 0

    for i, model in enumerate(models):
        quota = model_quotas[model]
        ratio = quota / total_quota
        block_count = int(ratio * bar_width)

        if i == len(models) - 1:
            block_count = bar_width - current_length

        bar += colors[model] + "█" * block_count + reset
        current_length += block_count

    print(bar)


def get_model_stats(acw_sc_v2, session_cookie, user_id, start_timestamp, end_timestamp):
    API_URL = "https://anyrouter.top/api/log/self"
    cookie_str = f"acw_sc__v2={acw_sc_v2}; session={session_cookie}"

    HEADERS = {
        "host": "anyrouter.top",
        "new-api-user": user_id,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://anyrouter.top/console/log",
        "cookie": cookie_str,
    }

    model_quotas = {"haiku": 0, "sonnet": 0, "opus": 0}
    page = 1
    page_size = 100

    try:
        while True:
            params = {
                "p": page,
                "page_size": page_size,
                "type": "0",
                "token_name": "",
                "model_name": "",
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "group": "",
            }

            response = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
            data = response.json()

            if not data.get("success"):
                break

            items = data["data"]["items"]
            if not items:
                break

            for item in items:
                model_name = item["model_name"].lower()
                quota = item["quota"]

                if "haiku" in model_name:
                    model_quotas["haiku"] += quota
                elif "sonnet" in model_name:
                    model_quotas["sonnet"] += quota
                elif "opus" in model_name:
                    model_quotas["opus"] += quota

            if len(items) < page_size:
                break
            page += 1

    except (requests.exceptions.RequestException, ValueError, KeyError):
        pass

    return model_quotas


def display_stats(model_quotas):
    colors = {
        "haiku": "\033[38;2;22;100;255m",
        "sonnet": "\033[38;2;148;239;255m",
        "opus": "\033[38;2;255;196;0m",
    }
    reset = "\033[0m"

    total_quota = sum(model_quotas.values())
    draw_progress_bar(model_quotas, total_quota)

    print("\n┌─────────┬──────────┐")
    print("│  模型   │   消耗   │")
    print("├─────────┼──────────┤")

    for model in ["haiku", "sonnet", "opus"]:
        total = model_quotas[model]
        result = f"${(total / 500000):.2f}"
        color = colors[model]
        print(f"│ {color}{model.capitalize():<7}{reset} │ {color}{result:^8}{reset} │")

    print("└─────────┴──────────┘")


if __name__ == "__main__":
    config = load_config()
    username = config["username"]
    password = config["password"]
    REFRESH_INTERVAL = config.get("refresh_interval", 240)
    TOTAL_DURATION = config.get("total_duration", 7200)

    acw_sc_v2, session, user_id, display_name = get_tokens(username, password)

    if not (acw_sc_v2 and session and user_id and display_name):
        print("登录失败,无法获取token或用户ID")
        exit(1)

    start_time = time.time()

    while True:
        clear_terminal()

        elapsed_time = time.time() - start_time
        if elapsed_time >= TOTAL_DURATION:
            print("\n程序运行结束")
            break

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_timestamp = int(today.timestamp())
        end_timestamp = int(time.time())

        total_cost = get_total_cost(
            acw_sc_v2, session, user_id, start_timestamp, end_timestamp
        )

        model_quotas = get_model_stats(
            acw_sc_v2, session, user_id, start_timestamp, end_timestamp
        )

        print("=" * 60)
        print(f"[Username] {display_name}")
        print(f"[Time] {current_time}")
        print("-" * 60)

        if total_cost:
            print(f"总消耗: {total_cost}")
        else:
            print("总消耗: 获取失败")

        display_stats(model_quotas)

        print("\n" + "=" * 60)

        time.sleep(REFRESH_INTERVAL)
