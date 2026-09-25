# Calligraphy Studio v0.6.0

可解释的字形比较、1000 字集字工作台与自动长卷。

## 新功能

- **Visual Profile**：bbox、宽高比、墨量、重心、图像矩与 Hu 不变量、横纵投影、四象限密度、留白、欧氏距离统计、骨架长度/端点/分支、方向分布。
- **上下文比较**：Context Profile、作品协调度、已加载候选按协调度排序、差异解释、置入作品预览。
- **千字工作台**：从 200 字扩展到 1000 字；自动适配大纸面、虚拟选字条、按显示尺寸分配画布像素，导出恢复原尺寸。
- **按需计算**：候选分页、图片懒加载、Web Worker、内容哈希与版本化 IndexedDB 缓存、局部重算。
- **长卷模式**：最多 20000 字，beam search 与局部代价自动选字，重复字变化、分页分栏、虚拟化预览、异常字与缺字检测、任务取消。
- **批量导出**：ZIP 包含每页 PNG、输入与选择参数、字形来源/位置清单、缺字 CSV。
- **实验分析**：投影 1D OT、连通/孔洞拓扑和 H0 持久条码；独立于默认排序。
- 重写 README，新增当前界面截图、算法定义、文献映射和性能测量。

## 下载

| 文件 | 说明 |
| --- | --- |
| `CalligraphyStudio-Setup-0.6.0-x64.exe` | Windows x64 安装版 |
| `CalligraphyStudio-Portable-0.6.0-x64.exe` | Windows x64 便携版 |
| `CalligraphyStudio-Android-0.6.0.apk` | Android 7.0+ 预览版 |
| `CalligraphyStudio-Web-0.6.0.zip` | 离线网页包，解压后通过 localhost HTTP 服务运行 |
| `SHA256SUMS.txt` | 所有附件的 SHA-256 校验值 |

[在线体验](https://styayur.github.io/calligraphy-studio/) · [使用说明](https://github.com/styayur/calligraphy-studio#readme) · [算法与文献](https://github.com/styayur/calligraphy-studio/blob/v0.6.0/docs/visual-profiles.md)

## 验证

数值测试覆盖特征、骨架、距离变换、拓扑、H0、OT、1000 字边界、分页、beam search、重复变化及取消。生产网页回归覆盖现有工作台，以及 1031 字长卷、缺字留位、ZIP 完整性、实际墨迹与手机布局。

本机 Edge 开发模式测量：1000 个不同汉字排版约 13.43 s，首次特征分析约 3.91 s，缓存复用生成 1001 字长卷约 1.90 s。耗时随设备和字库变化，不是跨设备保证。

## 使用边界与升级

- 协调度是原始字形与上下文的相近度，不是审美评分，未纳入手动变形与墨色。
- 实验 OT 为投影 1D 距离；持久性为 H0，未实现完整 2D OT 或 H1。
- 长卷结果仅保留在当前会话，刷新前请导出 ZIP；工作台草稿仅存于本机，建议升级前导出 JSON。
- 每字最多分析 8 个候选，beam search 不保证全局最优。大型 ZIP 在内存中组装，实际容量取决于设备。
- Windows 未使用商业代码签名；Android 使用 debug 预览签名，物理设备分享未验证。若 Android 升级遇到签名冲突，先备份后卸载旧版。
- 字库和许可证随包分发，MCCD 等受限数据不包含在发行包中。
