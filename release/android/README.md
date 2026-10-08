# Android v0.7.1

本版发布生产密钥签名的 [Android APK](https://github.com/styayur/calligraphy-studio/releases/download/v0.7.1/CalligraphyStudio-Android-0.7.1.apk)。安装前可核对 Release 中的 SHA256SUMS.txt 与签名证书指纹。

源码支持 Android 7.0+。开发构建需要 Node.js 22+、Java 21、Android SDK 36 和 build-tools 36.0.0：

```sh
cd apps/web
npm ci
npm run cap:sync
cd android
./gradlew assembleRelease
```

Windows 使用 `gradlew.bat assembleRelease`。未配置生产签名时生成的 APK 仅供开发预览。
生产签名配置、证书校验及升级兼容性见[签名说明](../../docs/RELEASE_SIGNING_0.7.1.md)。

物理设备上的保存、分享、旋转、后台恢复和升级行为尚未验收，见[原生测试清单](../../docs/RELEASE_SMOKE_TEST_0.7.0.md)。
变更签名可能要求卸载旧版；卸载前务必导出项目备份。

[v0.6.0 历史预览版](https://github.com/styayur/calligraphy-studio/releases/tag/v0.6.0) 使用不同签名，不能保证原地升级。请先导出项目。
