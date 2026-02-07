# 数字口腔临床决策支持系统 - 后端

## 项目概述
基于Flask的口腔临床决策支持系统后端，提供患者管理、病历管理、决策支持等功能。

## 功能模块
- 用户管理（医生、实习生、管理员）
- 患者信息管理
- 病历管理与临床特征录入
- 规则引擎与评分系统
- 多层级决策算法
- 相似历史病例查询
- 数据可视化接口

## 技术栈
- Python 3.8+
- Flask
- MySQL
- SQLAlchemy

## 安装与运行
1. 安装依赖：`pip install -r requirements.txt`
2. 配置数据库：修改config.yaml中的数据库配置
3. 初始化数据库：`python run.py`（首次运行会自动创建表）
4. 启动服务：`python run.py`

## API文档
启动后访问：http://localhost:5000/api/docs