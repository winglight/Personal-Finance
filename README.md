
# 个人财务管理系统

该项目是一个开源的个人财务管理系统，使用Python（Flask）和SQLAlchemy构建。它帮助用户管理和跟踪收入、支出和账户。

## 特别说明

本代码70%来自AI（Claudie）的协助生成，另有文档说明整个过程：[AI助我写代码（8）：个人记账（Personal Finance）](https://www.broyustudio.com/2024/09/06/AI-Help-Personal-Finance.html)

## TODO
- 开发前端页面
  - 基础信息维护
  - 录入记账
  - 统计查询
- 引入AI
  - 实现对话式交互
  - 自动分析自然语言、语音、照片，然后录入
  - 基于自然语言进行统计分析
  - 基于历史数据提供财务报告

## 功能特点

- **类别管理**：将收入和支出分类管理。
- **账户管理**：支持多币种管理不同账户。
- **交易跟踪**：记录所有的财务交易，包括描述、金额和相关的类别。
- **报告生成**：生成资产、收入/支出细分和按类别统计的汇总报告。
- **认证系统**：通过基于令牌的用户身份验证来确保访问安全。
- **货币转换**：基于存储的汇率在不同货币之间转换。

## 适用场景

本项目适用于个人财务跟踪、小型企业会计或个人财务报告。它提供了一个简单的界面，用于跟踪多个账户和货币的交易情况。

## 优势

- 轻量且易于设置。
- 使用SQLAlchemy支持的数据库，便于数据操作。
- 基于令牌的用户身份验证。
- 可扩展：可以根据需求添加更多功能。

## 安装指南

1. 克隆仓库：

```bash
git clone https://github.com/winglight/Personal-Finance.git
cd Personal-Finance
```

2. 创建虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
```

3. 安装所需依赖：

```bash
pip install -r requirements.txt
```

4. 设置SQLite数据库（可选）：

```bash
flask db init
flask db migrate
flask db upgrade
```

5. 修改配置文件 (`config.py.example`)：

```bash
cp config.py.example config.py
# 编辑 USER_TOKENS 字典，添加你的令牌
```

6. 启动应用程序：

```bash
flask run
```

服务器将在 `http://127.0.0.1:5000/` 上运行。

## 使用指南

### API端点：

- **POST /category** - 添加新类别。
- **POST /account** - 添加新账户。
- **POST /transaction** - 添加新交易。
- **GET /stats** - 获取财务报告。

前三个接口支持Restful风格调用。
每个端点都需要在请求头中提供 `Bearer` 令牌以进行身份验证。

## 配置文件

在 `config.py` 文件中，可以设置用户令牌：

```python
USER_TOKENS = {
    'Bearer your_token1': {
        'username': 'User1',
        'default_account_id': 1
    },
    'Bearer your_token2': {
        'username': 'User2',
        'default_account_id': 2
    }
}
```

将示例令牌替换为真实令牌。

## 许可证

该项目基于MIT许可证发布。
