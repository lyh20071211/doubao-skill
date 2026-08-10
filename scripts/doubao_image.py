#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doubao_image.py - 调用火山方舟（Volcengine Ark）豆包 Seedream 模型生成图片。

用法示例:
    python doubao_image.py --prompt "一只白猫戴天使翅膀" --out angel_cat.png
    python doubao_image.py --prompt "..." --model doubao-seedream-5-0-pro-260628 --size 2048x2048

环境变量:
    ARK_API_KEY  火山方舟 API Key（必填，也可用 --api-key 传入）
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedream-5-0-lite-260128"


def build_opener(no_proxy: bool):
    if no_proxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener()


def request_json(opener, endpoint, payload, api_key, timeout):
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
        method="POST",
    )
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_seedream(api_key, prompt, model, base_url, size, watermark, timeout, no_proxy=False, image=None):
    payload = {"model": model, "prompt": prompt, "size": size, "watermark": watermark, "n": 1}
    if image:
        if image.startswith(("http://", "https://", "data:")):
            payload["image"] = image
        else:
            import base64, mimetypes
            mime = mimetypes.guess_type(image)[0] or "image/jpeg"
            with open(image, "rb") as f:
                payload["image"] = f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")
    endpoint = base_url.rstrip("/") + "/images/generations"
    proxy_env = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    plan = [False] if (no_proxy or not proxy_env) else [False, True]
    last_err = None
    for use_no_proxy in plan:
        try:
            data = request_json(build_opener(use_no_proxy), endpoint, payload, api_key, timeout)
            return data
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {body}") from e
        except (urllib.error.URLError, OSError) as e:
            last_err = e
    raise RuntimeError(f"连接失败: {last_err}")


def save_image(data, out_path):
    item = data.get("data", [{}])[0]
    if item.get("b64_json"):
        raw = base64.b64decode(item["b64_json"])
        with open(out_path, "wb") as f:
            f.write(raw)
        return out_path, "b64"
    url = item.get("url")
    if not url:
        raise RuntimeError("响应里没有图片数据: " + json.dumps(data, ensure_ascii=False)[:500])
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path, "url"


def main():
    parser = argparse.ArgumentParser(description="调用豆包 Seedream 生成图片")
    parser.add_argument("--prompt", required=True, help="图片描述/编辑指令")
    parser.add_argument("--image", default=None, help="参考图片路径或 URL（图生图/编辑时传）")
    parser.add_argument("--out", required=True, help="输出图片路径（如 angel.png）")
    parser.add_argument("--api-key", default=None, help="火山方舟 API Key（默认读 ARK_API_KEY）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型 ID（默认 {DEFAULT_MODEL}）")
    parser.add_argument("--base-url", default=os.environ.get("DOUBAO_BASE_URL", DEFAULT_BASE_URL), help="API 地址")
    parser.add_argument("--size", default="1024x1024", help="尺寸：1K/2K/4K 或 宽x高")
    parser.add_argument("--watermark", action="store_true", default=True, help="加 AI 水印（默认开启）")
    parser.add_argument("--no-watermark", dest="watermark", action="store_false", help="不加 AI 水印")
    parser.add_argument("--timeout", type=int, default=180, help="请求超时秒数")
    parser.add_argument("--no-proxy", action="store_true", help="强制直连")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ARK_API_KEY")
    if not api_key:
        print("错误：未提供 API Key。请设置环境变量 ARK_API_KEY 或使用 --api-key 参数。", file=sys.stderr)
        sys.exit(1)

    try:
        data = call_seedream(api_key, args.prompt, args.model, args.base_url, args.size, args.watermark, args.timeout, args.no_proxy, image=args.image)
        path, src = save_image(data, args.out)
        print(f"图片已保存: {path} (来源: {src})")
    except Exception as e:
        print(f"调用失败：{e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

