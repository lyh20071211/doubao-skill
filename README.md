# Codex Doubao Skill（豆包：视觉 / 生图 / 视频）

一个让 [Codex](https://openai.com/codex) 直接调用火山方舟（Volcengine Ark）豆包系模型的技能包：

- 👀 **图片识别**（doubao_vision.py）— doubao-seed-2-0-mini
- 🎨 **生图 / 图生图 P 图**（doubao_image.py）— Seedream `doubao-seedream-5-0-260128`
- 🎬 **视频生成**（doubao_video.py）— Seedance `doubao-seedance-2-0-mini-260615`

## 安装

```bash
# 克隆到 Codex 用户 skills 目录
git clone https://github.com/<你的用户名>/doubao-skill.git "$HOME/.codex/skills/doubao"
# 或手动复制 SKILL.md + scripts/ + agents/ 到 ~/.codex/skills/doubao/
```

## 环境变量

```bash
export ARK_API_KEY="你的火山方舟 API Key"
# Windows:
# setx ARK_API_KEY "你的火山方舟 API Key"
```

Key 获取：https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey

## 用法（在任意 Codex 对话中）

- "帮我看这张图是什么"
- "让豆包生成一张卡通图" / "把这张照片 P 成 Q 版"
- "生成一段 10 秒宣传动画"

## 说明

- 模型 ID 以火山方舟控制台为准；接口为 OpenAI 兼容格式（Responses/Chat）。
- Seedream 尺寸最小约 3,686,400 像素；免费额度用完后约 0.22 元/张。
- Seedance 视频模型开通需要账户余额 ≥ 200 元（下单预留金额）。
- 本仓库不包含任何 API Key，凭据只从环境变量 `ARK_API_KEY` 读取。

## License

MIT

## Examples（演示）

- 🎨 卡通 UI 页面：[examples/cartoon-ui/index.html](examples/cartoon-ui/index.html)（吉祥物由豆包 Seedream 生成，代码由 DeepSeek 编写）
- 🎬 10 秒卡通宣传动画：[examples/promo/promo-10s.mp4](examples/promo/promo-10s.mp4) / [GIF](examples/promo/promo-10s.gif)，生成脚本 [generate_promo.py](examples/promo/generate_promo.py)

