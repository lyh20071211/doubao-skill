---
name: doubao
description: Use Volcengine Ark Doubao (豆包) APIs for vision, image generation, and video generation. Use when the user asks to identify/describe/read an image, screenshot, or photo; when the user asks to generate, create, or edit an image (including cartoon, illustration, photo style, or img2img edits of an existing image); or when the user asks to generate a video/promo animation. Provides ready-to-run scripts for vision understanding (doubao_vision.py), Seedream image generation (doubao_image.py), and Seedance video generation (doubao_video.py). Requires ARK_API_KEY environment variable.
---

# Doubao (豆包) 能力接入

调用火山方舟的豆包系列模型：视觉理解、Seedream 生图、Seedance 视频。

## 前置条件

- 环境变量 `ARK_API_KEY` 必须可用（用户已配置；如缺失，提示用户用 `setx ARK_API_KEY "<key>"` 并重启 Codex）。
- 网络受限时脚本会自动重试直连；也可加 `--no-proxy` 强制直连。

## 图片识别（豆包视觉）

用户需要看图/识别截图/理解图片内容时，运行：

```bash
python scripts/doubao_vision.py --image <本地路径或URL> --prompt "<具体问题>"
```

- 本地图片传路径，网络图片传 URL，脚本自动转 base64。
- 默认模型 `doubao-seed-2-0-mini-260428`；可 `--model` 换模型。
- 把返回文字直接整合进回答，不要凭空猜测图片内容。

## 生图 / 改图（Seedream）

用户要求生成图片、卡通插画，或对已有图片做风格化 P 图时，运行：

```bash
python scripts/doubao_image.py --prompt "<描述>" --out 输出.png [--image 参考图路径] [--model doubao-seedream-5-0-260128] [--size 2048x2048] [--no-watermark]
```

- 文生图：不传 `--image`；图生图/改图：传 `--image`（参考照片路径）。
- 尺寸：支持 `1K/2K/4K` 或 `宽x高`，**最小约 3,686,400 像素**（如 2048x2048、竖图 2048x3072）。
- 默认模型 `doubao-seedream-5-0-260128`（0.22 元/张，免费额度后计费）。
- 把生成结果保存到用户可见的 outputs 目录并展示给用户。

## 视频生成（Seedance）

用户要求生成视频/宣传动画时，运行：

```bash
python scripts/doubao_video.py --prompt "<视频描述>" --out 输出.mp4 --model doubao-seedance-2-0-mini-260615 --duration 10
```

- 流程：提交任务 → 自动轮询 → 下载 mp4（最多等 10 分钟）。
- ⚠️ Seedance 开通需要账户余额 ≥200 元（下单预留）；若报 `ModelNotOpen`，提示用户该限制，并给出免费替代方案（如用 PIL 渲染 GIF/MP4）。

## 注意事项

- 模型 ID 以火山方舟控制台为准；预置模型直接填 ID，自定义接入点用 `ep-xxxxx`。
- 所有脚本输出中文报错到 stderr，失败时把错误原样转述给用户。
