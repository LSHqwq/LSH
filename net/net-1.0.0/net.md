
## 2. 网络库完整文档

保存为 `/lib/net.md`：

```markdown
# NetLib - ESP32-S3 全功能网络通信库

## 📖 简介

NetLib是一个为ESP32-S3设计的全功能网络通信库，集成了WiFi连接、热点功能和蓝牙通信。提供一键式操作接口，自动处理错误和重连，让网络编程变得极其简单。

## ✨ 特性

- ✅ **一键连接** - 自动处理连接、等待、超时
- ✅ **智能扫描** - 快速扫描并格式化显示WiFi
- ✅ **热点模式** - 轻松开启加密/开放热点
- ✅ **蓝牙通信** - 支持广播、扫描、数据传输
- ✅ **错误恢复** - 自动处理状态错误
- ✅ **状态监控** - 完整的网络状态查询

## 📦 安装

1. 将 `net.py` 复制到 ESP32-S3 的 `/lib/` 目录
2. 确保MicroPython包含 `network` 和 `bluetooth` 模块

```python
# 推荐导入方式
from lib import net

# 或直接导入常用函数
from lib.net import wifi, ip, ble, ble_send, status