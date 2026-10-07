# Calligraphy Studio 网页离线包

这是已经构建的静态网页，不需要安装 Node.js 或 API。

1. 解压整个压缩包，保留 `fonts/`、`demo/` 和 `assets/` 目录。
2. 在解压目录启动 HTTP 服务，例如已安装 Python 时运行 `python -m http.server 8080`。
3. 打开 http://localhost:8080 。请勿直接双击 `index.html`，浏览器会限制本地文件请求。

字库随压缩包分发，运行时不需要联网。草稿保存在当前浏览器和地址下，长期保存请下载项目 JSON。

中文样本许可位于 `demo/licenses/`，字体许可位于 `fonts/licenses/`，CODH 和 HarfBuzz 许可位于 `licenses/`；其他第三方说明见 `THIRD_PARTY_NOTICE.md`。字体不是历史原迹，CODH 样本及其墨迹蒙版独立遵循 CC BY-SA 4.0，不属于代码的 MIT 许可。

工作台支持 1000 字；长卷模式支持最多 20000 字。长卷结果仅保留于当前会话，刷新前请导出 ZIP。Visual Profile 与特征缓存需要现代浏览器的 Worker、Web Crypto 与 IndexedDB 支持。
