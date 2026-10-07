# Release 文件

[GitHub Release v0.7.1](https://github.com/styayur/calligraphy-studio/releases/tag/v0.7.1)
已发布 Windows 安装版、便携版、Web 离线 ZIP 和生产签名 Android APK；二进制不提交到源码仓库。

- Windows：[下载与使用](windows/README.md)
- Web：[离线运行说明](WEB_README.md)
- Android：[下载与签名状态](android/README.md)
- [更新说明](RELEASE_NOTES_0.7.1.md)
- [SHA256SUMS.txt](https://github.com/styayur/calligraphy-studio/releases/download/v0.7.1/SHA256SUMS.txt)
- [签名与恢复](../docs/RELEASE_SIGNING_0.7.1.md)

Windows 包未签名；Android 使用持久生产密钥签名，但物理设备验收尚未完成。
Release 附带构建来源、签名状态和文件清单，所有发布包来自同一干净标签提交。

`windows/SHA256SUMS.txt` 与 `android/SHA256SUMS.txt` 保留为 v0.4.0 历史记录。
当前版本以对应 GitHub Release 中的统一 `SHA256SUMS.txt` 为准。
