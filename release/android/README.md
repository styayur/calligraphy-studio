# Android v0.7.0

**本版不发布 APK。** Android 构建、包内容和签名校验已经通过，但可用签名是 debug 预览签名，不能作为生产发行包。

源码支持 Android 7.0+。开发构建需要 Node.js 22+、Java 21、Android SDK 36 和 build-tools 36.0.0：

```sh
cd apps/web
npm ci
npm run cap:sync
cd android
./gradlew assembleRelease
```

Windows 使用 `gradlew.bat assembleRelease`。未配置生产签名时生成的 APK 仅供开发预览。
生产签名配置、证书校验及升级兼容性见[签名说明](../../docs/RELEASE_SIGNING_0.7.0.md)。

物理设备上的保存、分享、旋转、后台恢复和升级行为尚未验收，见[原生测试清单](../../docs/RELEASE_SMOKE_TEST_0.7.0.md)。
变更签名可能要求卸载旧版；卸载前务必导出项目备份。

[v0.6.0 历史预览版](https://github.com/styayur/calligraphy-studio/releases/tag/v0.6.0) 保留在旧 Release 中，不代表 v0.7.0 已提供 Android 下载。
