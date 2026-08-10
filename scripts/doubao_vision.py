#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doubao_vision.py - 调用火山方舟（Volcengine Ark）豆包视觉模型识别图片。

用法示例:
    python doubao_vision.py --image C:/path/screenshot.png --prompt "描述这张图的布局和配色"
    python doubao_vision.py --image https://example.com/a.png --prompt "图里有什么错误信息？"
    python doubao_vision.py --image a.png --prompt "提取图中文字" --model doubao-seed-2-1-pro-260628

环境变量:
    ARK_API_KEY  火山方舟 API Key（必填，也可用 --api-key 传入）
    DOUBAO_BASE_URL  可选，默认 https://ark.cn-beijing.volces.com/api/v3
    DOUBAO_MODEL     可选，默认 doubao-seed-2-0-mini-260428

说明:
    如果设置了 HTTP_PROXY/HTTPS_PROXY 但代理不可用（例如在 Codex 沙箱里），
    首次连接失败后会自动改用直连重试一次；也可用 --no-proxy 强制直连。
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = os.environ.get("DOUBAO_MODEL", "doubao-seed-2-0-mini-260428")


def build_opener(no_proxy: bool):
    if no_proxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener()


def image_to_data_uri(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def call_doubao(api_key, image, prompt, model, base_url, detail, max_tokens, temperature, timeout, no_proxy=False):
    # 本地文件 -> base64 data URI；http(s)/data: 直接透传
    if image.startswith(("http://", "https://", "data:")):
        image_url = image
    else:
        image_url = image_to_data_uri(image)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": detail}},
                ],
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    endpoint = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )

    attempts = []
    proxy_env = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    # 第一次按当前环境（可能走代理）；失败且设置了代理时，第二次直连
    plan = [False] if (no_proxy or not proxy_env) else [False, True]
    last_err = None
    for use_no_proxy in plan:
        try:
            with build_opener(use_no_proxy).open(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return json.dumps(data, ensure_ascii=False, indent=2)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last_err = e
            attempts.append(use_no_proxy)
            if isinstance(e, urllib.error.HTTPError) and e.code < 500:
                # 4xx 是业务错误（key 无效/模型未开通等），重试没有意义
                body = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {e.code}: {body}") from e
    raise RuntimeError(f"连接失败（已尝试 {len(attempts)} 次）: {last_err}")


def main():
    parser = argparse.ArgumentParser(description="调用豆包视觉模型识别图片")
    parser.add_argument("--image", required=True, help="本地图片路径或 http(s) URL")
    parser.add_argument("--prompt", required=True, help="对图片的指令，越具体越好")
    parser.add_argument("--api-key", default=None, help="火山方舟 API Key（默认读 ARK_API_KEY 环境变量）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型 ID（默认 {DEFAULT_MODEL}）")
    parser.add_argument("--base-url", default=os.environ.get("DOUBAO_BASE_URL", DEFAULT_BASE_URL), help="API 地址")
    parser.add_argument("--detail", default="auto", choices=["auto", "low", "high"], help="图片精度")
    parser.add_argument("--max-tokens", type=int, default=4096, help="最大输出 token 数")
    parser.add_argument("--temperature", type=float, default=1.0, help="采样温度 0~2")
    parser.add_argument("--timeout", type=int, default=120, help="请求超时秒数")
    parser.add_argument("--no-proxy", action="store_true", help="强制直连，不走系统代理")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ARK_API_KEY")
    if not api_key:
        print("错误：未提供 API Key。请设置环境变量 ARK_API_KEY 或使用 --api-key 参数。", file=sys.stderr)
        print("获取方法：https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey", file=sys.stderr)
        sys.exit(1)

    try:
        result = call_doubao(
            api_key, args.image, args.prompt, args.model,
            args.base_url, args.detail, args.max_tokens, args.temperature, args.timeout,
            no_proxy=args.no_proxy,
        )
    except Exception as e:
        print(f"调用失败：{e}", file=sys.stderr)
        sys.exit(2)

    print(result)


if __name__ == "__main__":
    main()
