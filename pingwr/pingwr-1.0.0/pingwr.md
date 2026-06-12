# PingWR - ESP32-S3 GPIO智能控制库

## 📖 简介

PingWR是一个为ESP32-S3设计的智能GPIO控制库，支持数字输出、模拟输出(PWM)和RGB灯控制。库会自动识别输出类型，让GPIO操作变得极其简单。

## ✨ 特性

- ✅ **智能识别** - 自动判断数字/模拟输出
- ✅ **PWM支持** - 0-255模拟输出，实现呼吸灯、电机调速
- ✅ **RGB控制** - 集成WS2812 RGB灯驱动
- ✅ **高性能** - 对象缓存机制，避免重复初始化
- ✅ **简洁API** - 一行代码完成GPIO操作

## 📦 安装

1. 将 `pingwr.py` 复制到 ESP32-S3 的 `/lib/` 目录
2. 在代码中导入使用

```python
# 方式1：导入整个库
from lib import pingwr

# 方式2：直接导入函数（推荐）
from lib.pingwr import write, read, rgb, off