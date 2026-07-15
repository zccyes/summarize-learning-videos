# 贡献指南

感谢你改进 `summarize-learning-videos`。这个项目的第一原则是：性能优化不能以内容覆盖、事实准确性或发布前质量检查为代价。

## 适合贡献的方向

- 新的视频平台适配。
- Windows、Linux 和 Intel Mac 的本地语音识别后端。
- 更稳健的字幕清洗、章节划分和说话人归属。
- 画面依赖型教程的关键帧选择。
- 多语言术语校正。
- Obsidian 索引、主题 MOC 和附件组织。
- 能证明“不降低笔记质量”的性能优化。

## 开发约定

1. 不要提交 `project-config.yaml`、Cookies、Token、登录数据或个人绝对路径。
2. 不要提交视频、音频、完整转写中间文件或模型缓存。
3. 新增行为时同步更新 README、示例配置和测试。
4. 不要默认缩小 ASR 模型、跳过视频章节、关闭事实核验或绕过质量门。
5. 对视频平台条款、版权和访问权限保持保守处理，不增加绕过 DRM、付费墙或私有权限的功能。

## 本地检查

在仓库根目录运行：

```bash
python3 -m py_compile scripts/*.py tests/*.py
python3 -m unittest discover -s tests -v
bash -n scripts/setup_macos.sh
```

如果本机有 Codex 自带的 `skill-creator`，再运行：

```bash
uv run --with pyyaml \
  python /path/to/skill-creator/scripts/quick_validate.py .
```

## Pull Request 说明

请说明：

- 解决了什么问题。
- 影响哪些平台和视频类型。
- 使用了哪些测试样例。
- 是否改变默认输出结构、来源等级或质量门。
- 如果是性能优化，提供优化前后的阶段耗时和质量对照结果。

真实视频可能受版权保护，不应作为公开测试素材提交。自动测试应使用短小的自建字幕、转写稿和笔记样例。
