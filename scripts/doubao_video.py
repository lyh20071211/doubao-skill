#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doubao_video.py - 调用火山方舟（Volcengine Ark）豆包 Seedance 生成视频。

用法示例:
    python doubao_video.py --prompt "卡通风格动画：两只可爱吉祥物..." --out promo.mp4
    python doubao_video.py --prompt "..." --model doubao-seedance-2-5-260628 --duration 10

流程: 提交任务 -> 轮询 -> 下载 mp4
环境变量:
    ARK_API_KEY  火山方舟 API Key（必填）
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedance-2-0-mini-260615"


def build_opener(no_proxy: bool):
    if no_proxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener()


def req_json(opener, method, url, payload, api_key, timeout):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": "Bearer " + api_key}
    if data:
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with opener.open(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call(api_key, base_url, method, path, payload, timeout, no_proxy):
    proxy_env = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    plan = [False] if (no_proxy or not proxy_env) else [False, True]
    last_err = None
    for use_no_proxy in plan:
        try:
            return req_json(build_opener(use_no_proxy), method, base_url.rstrip("/") + path, payload, api_key, timeout)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {body}") from e
        except (urllib.error.URLError, OSError) as e:
            last_err = e
    raise RuntimeError(f"连接失败: {last_err}")


def main():
    parser = argparse.ArgumentParser(description="调用豆包 Seedance 生成视频")
    parser.add_argument("--prompt", required=True, help="视频描述")
    parser.add_argument("--out", required=True, help="输出视频路径（.mp4）")
    parser.add_argument("--api-key", default=None, help="火山方舟 API Key（默认读 ARK_API_KEY）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型 ID（默认 {DEFAULT_MODEL}）")
    parser.add_argument("--base-url", default=os.environ.get("DOUBAO_BASE_URL", DEFAULT_BASE_URL), help="API 地址")
    parser.add_argument("--duration", type=int, default=10, help="视频时长（秒）")
    parser.add_argument("--watermark", action="store_true", default=True, help="加水印（默认开）")
    parser.add_argument("--no-watermark", dest="watermark", action="store_false", help="不加 AI 水印")
    parser.add_argument("--poll-interval", type=int, default=12, help="轮询间隔（秒）")
    parser.add_argument("--timeout", type=int, default=180, help="单次请求超时秒数")
    parser.add_argument("--max-wait", type=int, default=600, help="最长等待秒数")
    parser.add_argument("--no-proxy", action="store_true", help="强制直连")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ARK_API_KEY")
    if not api_key:
        print("错误：未提供 API Key。请设置环境变量 ARK_API_KEY 或使用 --api-key 参数。", file=sys.stderr)
        sys.exit(1)

    text = args.prompt
    if "--duration" not in text:
        text += f" --duration {args.duration}"
    if "--watermark" not in text:
        text += " --watermark " + ("true" if args.watermark else "false")

    print("提交视频生成任务...")
    resp = call(api_key, args.base_url, "POST", "/contents/generations/tasks",
                {"model": args.model, "content": [{"type": "text", "text": text}]},
                args.timeout, args.no_proxy)
    task_id = resp.get("id")
    if not task_id:
        print("响应中没有任务 id:", json.dumps(resp, ensure_ascii=False)[:500], file=sys.stderr)
        sys.exit(2)
    print("任务 id:", task_id)

    start = time.time()
    while time.time() - start < args.max_wait:
        time.sleep(args.poll_interval)
        r = call(api_key, args.base_url, "GET", f"/contents/generations/tasks/{task_id}", None, args.timeout, args.no_proxy)
        status = r.get("status")
        print(f"[{int(time.time() - start)}s] status={status}")
        if status == "succeeded":
            url = (r.get("content") or {}).get("video_url")
            if not url:
                print("响应没有 video_url:", json.dumps(r, ensure_ascii=False)[:800], file=sys.stderr)
                sys.exit(3)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=180) as resp2:
                raw = resp2.read()
            with open(args.out, "wb") as f:
                f.write(raw)
            print(f"视频已保存: {args.out} ({len(raw)} bytes)")
            return
        if status == "failed":
            print("任务失败:", json.dumps(r, ensure_ascii=False)[:800], file=sys.stderr)
            sys.exit(4)
    print("等待超时", file=sys.stderr)
    sys.exit(5)


if __name__ == "__main__":
    main()
