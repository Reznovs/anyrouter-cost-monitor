#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import re
import time
import os
import json
import sys
from datetime import datetime
import logging

# 禁用 urllib3 的警告日志
urllib3.disable_warnings()
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


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
        0xF,
        0x23,
        0x1D,
        0x18,
        0x21,
        0x10,
        0x1,
        0x26,
        0xA,
        0x9,
        0x13,
        0x1F,
        0x28,
        0x1B,
        0x16,
        0x17,
        0x19,
        0xD,
        0x6,
        0xB,
        0x27,
        0x12,
        0x14,
        0x8,
        0xE,
        0x15,
        0x20,
        0x1A,
        0x2,
        0x1E,
        0x7,
        0x4,
        0x11,
        0x5,
        0x3,
        0x1C,
        0x22,
        0x25,
        0xC,
        0x24,
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


def get_session_with_retry():
    """创建带重试机制的session"""
    session = requests.Session()

    # 配置重试策略
    retry_strategy = Retry(
        total=5,  # 总共重试5次
        backoff_factor=1,  # 重试间隔:1s, 2s, 4s, 8s, 16s
        status_forcelist=[429, 500, 502, 503, 504],  # 这些状态码会触发重试
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # 允许重试的方法
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def clear_terminal():
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


def get_tokens(username, password):
    url = "https://anyrouter.top/api/user/login"
    session = get_session_with_retry()

    try:
        resp1 = session.get(url, timeout=30)
        arg1 = re.search(r"var arg1='([A-F0-9]+)'", resp1.text)
        if not arg1:
            print("警告: 无法获取 arg1")
            return None, None, None, None

        acw_sc_v2 = generate_acw_sc_v2(arg1.group(1))
        session.cookies.set("acw_sc__v2", acw_sc_v2, domain="anyrouter.top")

        login_resp = session.post(
            f"{url}?turnstile=",
            json={"username": username, "password": password},
            timeout=30,
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
        print(f"网络请求错误: {e}")
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

    session = get_session_with_retry()

    try:
        response = session.get(API_URL, headers=HEADERS, params=params, timeout=30)

        # 调试信息:输出HTTP状态码
        if response.status_code != 200:
            print(f"[调试] HTTP状态码: {response.status_code}")
            print(f"[调试] 响应内容(前500字符): {response.text[:500]}")

        data = response.json()

        if data.get("success"):
            e = data["data"]["quota"]
            return f"${(e / 500000):.2f}"
        else:
            print(f"API返回失败: {data.get('message', '未知错误')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"获取总消耗失败(网络错误): {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"获取总消耗失败(解析错误): {e}")
        print(f"[调试] 响应状态码: {response.status_code}")
        print(f"[调试] 响应内容(前500字符): {response.text[:500]}")
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

    # 找到最后一个有消耗的模型索引
    last_active_idx = -1
    for i, model in enumerate(models):
        if model_quotas[model] > 0:
            last_active_idx = i

    for i, model in enumerate(models):
        quota = model_quotas[model]
        ratio = quota / total_quota
        block_count = int(ratio * bar_width)

        # 最后一个有消耗的模型补齐剩余格子
        if i == last_active_idx:
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

    session = get_session_with_retry()

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

            response = session.get(API_URL, headers=HEADERS, params=params, timeout=30)

            # 调试信息:输出HTTP状态码
            if response.status_code != 200:
                print(f"[调试] 页{page} HTTP状态码: {response.status_code}")
                print(f"[调试] 响应内容(前500字符): {response.text[:500]}")

            data = response.json()

            if not data.get("success"):
                print(f"API返回失败: {data.get('message', '未知错误')}")
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

    except requests.exceptions.RequestException as e:
        print(f"获取模型统计失败(网络错误) - 页{page}: {e}")
    except (ValueError, KeyError) as e:
        print(f"获取模型统计失败(解析错误) - 页{page}: {e}")
        print(f"[调试] 响应状态码: {response.status_code}")
        print(f"[调试] 响应内容(前500字符): {response.text[:500]}")

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

    print("=" * 60)
    print("AnyRouter API 成本监控")
    print("=" * 60)

    start_time = time.time()
    is_first_run = True  # 标记是否首次运行

    while True:
        # 每次刷新前重新登录获取新的 Cookie
        if is_first_run:
            print("\n正在登录...")

        acw_sc_v2, session_cookie, user_id, display_name = get_tokens(
            username, password
        )

        if not (acw_sc_v2 and session_cookie and user_id and display_name):
            print("\n登录失败,无法获取token或用户ID")
            print("\n可能的原因:")
            print("1. 用户名或密码错误")
            print("2. 网络连接失败 - 检查是否能访问 https://anyrouter.top")
            print("3. 阿里云CDN防护策略更新 - arg1映射表可能已变更")
            print("\n将在30秒后重试...")
            time.sleep(30)
            continue

        if is_first_run:
            print(f"登录成功! 用户: {display_name}")
            is_first_run = False

        elapsed_time = time.time() - start_time
        if elapsed_time >= TOTAL_DURATION:
            print("\n程序运行结束")
            break

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_timestamp = int(today.timestamp())
        end_timestamp = int(time.time())

        # 先请求获取数据
        total_cost = get_total_cost(
            acw_sc_v2, session_cookie, user_id, start_timestamp, end_timestamp
        )

        model_quotas = get_model_stats(
            acw_sc_v2, session_cookie, user_id, start_timestamp, end_timestamp
        )

        # 数据获取完成后再清屏并立即打印
        clear_terminal()

        print("=" * 50)
        print(f"[Username] {display_name}")
        print(f"[Time] {current_time}")
        print("-" * 50)

        if total_cost:
            print(f"总消耗: {total_cost}")
        else:
            print("总消耗: 获取失败")

        display_stats(model_quotas)

        print("\n" + "=" * 50)
        print(f"刷新:{REFRESH_INTERVAL}s")

        try:
            time.sleep(REFRESH_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
