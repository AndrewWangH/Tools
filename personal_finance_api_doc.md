# 个人财务管理 API 文档

## 基本信息

- **Base URL**: `http://localhost:5000`
- **数据格式**: JSON
- **字符编码**: UTF-8

## 响应格式

所有接口返回统一格式：

```json
{
    "code": 0,        // 0表示成功，非0表示错误
    "data": {},       // 返回数据
    "message": ""     // 提示信息
}
```

---

## 资产管理接口

### 获取所有资产
```
GET /api/assets
```

**响应示例**:
```json
{
    "code": 0,
    "data": [
        {
            "id": "1a2b3c4d",
            "name": "招商银行储蓄卡",
            "type": "bank",
            "amount": 50000.00,
            "note": "工资卡",
            "update_time": "2026-03-05T10:30:00"
        }
    ],
    "message": "success"
}
```

### 获取单个资产
```
GET /api/assets/{id}
```

### 创建资产
```
POST /api/assets
Content-Type: application/json

{
    "name": "招商银行储蓄卡",
    "type": "bank",
    "amount": 50000,
    "note": "工资卡"
}
```

**资产类型 (type)**:
| 值 | 说明 |
|---|---|
| cash | 现金 |
| bank | 银行存款 |
| alipay | 支付宝 |
| wechat | 微信钱包 |
| stock | 股票基金 |
| fund | 理财产品 |
| bond | 债券 |
| crypto | 数字货币 |
| property | 房产 |
| car | 车辆 |
| insurance | 保险 |
| other | 其他资产 |

### 更新资产
```
PUT /api/assets/{id}
Content-Type: application/json

{
    "name": "招商银行储蓄卡",
    "type": "bank",
    "amount": 55000,
    "note": "工资卡-已更新"
}
```

### 删除资产
```
DELETE /api/assets/{id}
```

---

## 收入管理接口

### 获取收入记录
```
GET /api/incomes?start_date=2026-03-01&end_date=2026-03-31&category=salary
```

**查询参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| start_date | string | 开始日期 (YYYY-MM-DD) |
| end_date | string | 结束日期 (YYYY-MM-DD) |
| category | string | 收入类型 |

### 获取单条收入
```
GET /api/incomes/{id}
```

### 添加收入
```
POST /api/incomes
Content-Type: application/json

{
    "category": "salary",
    "amount": 15000,
    "date": "2026-03-05",
    "note": "3月工资"
}
```

**收入类型 (category)**:
| 值 | 说明 |
|---|---|
| salary | 工资薪金 |
| bonus | 奖金 |
| parttime | 兼职收入 |
| investment | 投资收益 |
| interest | 利息收入 |
| rent | 租金收入 |
| refund | 退款 |
| gift | 礼金红包 |
| other | 其他收入 |

### 更新收入
```
PUT /api/incomes/{id}
Content-Type: application/json

{
    "category": "salary",
    "amount": 16000,
    "date": "2026-03-05",
    "note": "3月工资(含加班)"
}
```

### 删除收入
```
DELETE /api/incomes/{id}
```

---

## 支出管理接口

### 获取支出记录
```
GET /api/expenses?start_date=2026-03-01&end_date=2026-03-31&category=food
```

**查询参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| start_date | string | 开始日期 (YYYY-MM-DD) |
| end_date | string | 结束日期 (YYYY-MM-DD) |
| category | string | 支出类型 |

### 获取单条支出
```
GET /api/expenses/{id}
```

### 添加支出
```
POST /api/expenses
Content-Type: application/json

{
    "category": "food",
    "amount": 128.5,
    "date": "2026-03-05",
    "note": "午餐聚餐"
}
```

**支出类型 (category)**:
| 值 | 说明 |
|---|---|
| food | 餐饮美食 |
| transport | 交通出行 |
| shopping | 购物消费 |
| entertainment | 休闲娱乐 |
| medical | 医疗健康 |
| education | 教育培训 |
| housing | 住房物业 |
| utilities | 水电煤气 |
| communication | 通讯网络 |
| insurance | 保险 |
| gift | 人情往来 |
| travel | 旅游度假 |
| pet | 宠物 |
| children | 子女教育 |
| elderly | 孝敬长辈 |
| other | 其他支出 |

### 更新支出
```
PUT /api/expenses/{id}
Content-Type: application/json

{
    "category": "food",
    "amount": 150,
    "date": "2026-03-05",
    "note": "午餐聚餐(AA后)"
}
```

### 删除支出
```
DELETE /api/expenses/{id}
```

---

## 统计接口

### 获取汇总数据
```
GET /api/summary
```

**响应示例**:
```json
{
    "code": 0,
    "data": {
        "total_assets": 150000.00,
        "month_income": 18000.00,
        "month_expense": 5600.00,
        "month_balance": 12400.00
    },
    "message": "success"
}
```

### 按类型统计资产
```
GET /api/statistics/assets-by-type
```

**响应示例**:
```json
{
    "code": 0,
    "data": [
        {"type": "bank", "amount": 80000},
        {"type": "stock", "amount": 50000},
        {"type": "alipay", "amount": 20000}
    ],
    "message": "success"
}
```

### 按类别统计支出
```
GET /api/statistics/expenses-by-category?start_date=2026-03-01&end_date=2026-03-31
```

### 按类别统计收入
```
GET /api/statistics/incomes-by-category?start_date=2026-03-01&end_date=2026-03-31
```

### 获取月度收支趋势
```
GET /api/statistics/monthly-trend?months=6
```

**响应示例**:
```json
{
    "code": 0,
    "data": [
        {"month": "10月", "year_month": "2025-10", "income": 15000, "expense": 8000, "balance": 7000},
        {"month": "11月", "year_month": "2025-11", "income": 15500, "expense": 7500, "balance": 8000},
        {"month": "12月", "year_month": "2025-12", "income": 18000, "expense": 12000, "balance": 6000},
        {"month": "1月", "year_month": "2026-01", "income": 16000, "expense": 9000, "balance": 7000},
        {"month": "2月", "year_month": "2026-02", "income": 15000, "expense": 15000, "balance": 0},
        {"month": "3月", "year_month": "2026-03", "income": 18000, "expense": 5600, "balance": 12400}
    ],
    "message": "success"
}
```

---

## CSV导出接口

### 导出资产
```
GET /api/export/assets
```
返回CSV文件下载

### 导出收入
```
GET /api/export/incomes
```

### 导出支出
```
GET /api/export/expenses
```

---

## CSV导入接口

### 导入资产
```
POST /api/import/assets
Content-Type: multipart/form-data

file: (CSV文件)
```

**CSV格式**:
```csv
ID,资产名称,资产类型,金额,备注,更新时间
abc123,招商银行,bank,50000,工资卡,2026-03-05T10:00:00
```

### 导入收入
```
POST /api/import/incomes
Content-Type: multipart/form-data

file: (CSV文件)
```

**CSV格式**:
```csv
ID,收入类型,金额,日期,备注,创建时间
abc123,salary,15000,2026-03-05,3月工资,2026-03-05T10:00:00
```

### 导入支出
```
POST /api/import/expenses
Content-Type: multipart/form-data

file: (CSV文件)
```

**CSV格式**:
```csv
ID,支出类型,金额,日期,备注,创建时间
abc123,food,128.5,2026-03-05,午餐,2026-03-05T12:00:00
```

---

## 批量操作接口

### 批量创建资产
```
POST /api/batch/assets
Content-Type: application/json

{
    "items": [
        {"name": "现金", "type": "cash", "amount": 1000, "note": "钱包"},
        {"name": "支付宝", "type": "alipay", "amount": 5000, "note": ""}
    ]
}
```

### 批量创建收入
```
POST /api/batch/incomes
Content-Type: application/json

{
    "items": [
        {"category": "salary", "amount": 15000, "date": "2026-03-05", "note": "工资"},
        {"category": "bonus", "amount": 3000, "date": "2026-03-05", "note": "奖金"}
    ]
}
```

### 批量创建支出
```
POST /api/batch/expenses
Content-Type: application/json

{
    "items": [
        {"category": "food", "amount": 50, "date": "2026-03-05", "note": "早餐"},
        {"category": "transport", "amount": 10, "date": "2026-03-05", "note": "地铁"}
    ]
}
```

### 清空所有数据
```
DELETE /api/clear-all
```

---

## 健康检查
```
GET /api/health
```

---

## 快速开始

1. 安装依赖:
```bash
pip install flask flask-cors
```

2. 启动服务:
```bash
python personal_finance_api.py
```

3. 测试接口:
```bash
# 获取汇总
curl http://localhost:5000/api/summary

# 添加资产
curl -X POST http://localhost:5000/api/assets \
  -H "Content-Type: application/json" \
  -d '{"name":"招商银行","type":"bank","amount":50000,"note":"工资卡"}'

# 添加收入
curl -X POST http://localhost:5000/api/incomes \
  -H "Content-Type: application/json" \
  -d '{"category":"salary","amount":15000,"date":"2026-03-05","note":"工资"}'

# 添加支出
curl -X POST http://localhost:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"category":"food","amount":50,"date":"2026-03-05","note":"午餐"}'
```

---

## 错误码说明

| 代码 | 说明 |
|---|---|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
