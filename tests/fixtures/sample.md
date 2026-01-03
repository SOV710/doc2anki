---
title: TCP/IP 基础
author: test
tags:
  - networking
  - tcp
---

# TCP/IP 基础

本文介绍 TCP/IP 协议的基础知识。

## 三次握手

TCP 建立连接需要三次握手：

1. 客户端发送 SYN 包
2. 服务端回复 SYN+ACK 包
3. 客户端发送 ACK 包

## 四次挥手

TCP 断开连接需要四次挥手：

1. 主动方发送 FIN
2. 被动方回复 ACK
3. 被动方发送 FIN
4. 主动方回复 ACK
