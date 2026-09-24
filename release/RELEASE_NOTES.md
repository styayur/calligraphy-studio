# Calligraphy Studio v0.5.0

将演示编辑器升级为可直接使用的集字工作台，并重新整理界面。

## 新功能与修复

- 内置楷、行、草三款 OFL 字体，各覆盖 7,015 个字符；按需生成透明字形，不依赖 API。
- 横排、竖排右起与方格布局自动适配纸面，修复竖排越界，缺字留位并提示。
- 同字替换保留位置与大小；支持复制、删除、键盘微移、撤销重做与精细调整。
- NCCU 黑底白字原帖自动净底，保留来源和授权。
- 本机输入及作品恢复；JSON 保留名称、排版参数和字形；PNG 支持透明背景与 2 倍尺寸。
- 精简工具栏和面板，适配手机；Android 导出接入原生文件写入与系统分享面板。
- 发布流程绑定版本标签，统一提供安装包、离线网页包和 SHA-256 校验文件。

## 下载

| 文件 | 说明 |
| --- | --- |
| `CalligraphyStudio-Setup-0.5.0-x64.exe` | Windows x64 安装版 |
| `CalligraphyStudio-Portable-0.5.0-x64.exe` | Windows x64 便携版 |
| `CalligraphyStudio-Android-0.5.0.apk` | Android 7.0+ 预览版 |
| `CalligraphyStudio-Web-0.5.0.zip` | 已构建的网页离线包，解压后通过本地 HTTP 服务运行 |
| `SHA256SUMS.txt` | 全部附件的 SHA-256 校验值 |

[在线使用](https://styayur.github.io/calligraphy-studio/) · [使用说明](https://github.com/styayur/calligraphy-studio#readme)

## 验证与边界

生产构建与浏览器回归覆盖排版、纸面选字、同字替换、历史记录、本机恢复、PNG 尺寸/透明通道、项目往返导入、原帖净底、搜索及手机布局。Windows 与 Android 安装包由 GitHub Actions 构建；Android 原生分享入口尚未经过物理设备验证。

单幅文本最多 200 字；原帖字库仍是样本及用户自行导入的数据。草稿仅保存在本机，升级或卸载前请导出 JSON 备份。

Windows 安装包未使用商业代码签名。Android 使用 debug 预览签名，旧版可能需要先备份再卸载安装；不适用于应用商店发行。包内保留 OFL / MIT 等许可证，MCCD 等受限数据不随包分发。
