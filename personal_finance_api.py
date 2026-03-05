"""
个人资产与消费账单管理 - 后端API
Flask + SQLite RESTful API
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
import os
import csv
import io
from datetime import datetime
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据库配置
DATABASE = os.path.join(os.path.dirname(__file__), 'personal_finance.db')


@contextmanager
def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 资产表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                note TEXT,
                update_time TEXT NOT NULL
            )
        ''')
        
        # 收入表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incomes (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                date TEXT NOT NULL,
                note TEXT,
                create_time TEXT NOT NULL
            )
        ''')
        
        # 支出表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                date TEXT NOT NULL,
                note TEXT,
                create_time TEXT NOT NULL
            )
        ''')
        
        conn.commit()


def generate_id():
    """生成唯一ID"""
    import random
    import string
    timestamp = hex(int(datetime.now().timestamp() * 1000))[2:]
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{timestamp}{random_str}"


# ==================== 资产接口 ====================

@app.route('/api/assets', methods=['GET'])
def get_assets():
    """获取所有资产"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assets ORDER BY update_time DESC')
        assets = [dict(row) for row in cursor.fetchall()]
    return jsonify({'code': 0, 'data': assets, 'message': 'success'})


@app.route('/api/assets/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    """获取单个资产"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assets WHERE id = ?', (asset_id,))
        asset = cursor.fetchone()
        if asset:
            return jsonify({'code': 0, 'data': dict(asset), 'message': 'success'})
        return jsonify({'code': 404, 'data': None, 'message': '资产不存在'}), 404


@app.route('/api/assets', methods=['POST'])
def create_asset():
    """创建资产"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'code': 400, 'message': '资产名称不能为空'}), 400
    if not data.get('amount') or float(data.get('amount', 0)) <= 0:
        return jsonify({'code': 400, 'message': '请输入有效金额'}), 400
    
    asset_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assets (id, name, type, amount, note, update_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            asset_id,
            data.get('name'),
            data.get('type', 'other'),
            float(data.get('amount', 0)),
            data.get('note', ''),
            now
        ))
        conn.commit()
    
    return jsonify({
        'code': 0,
        'data': {'id': asset_id},
        'message': '资产添加成功'
    }), 201


@app.route('/api/assets/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """更新资产"""
    data = request.get_json()
    now = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE assets 
            SET name = ?, type = ?, amount = ?, note = ?, update_time = ?
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('type'),
            float(data.get('amount', 0)),
            data.get('note', ''),
            now,
            asset_id
        ))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'code': 404, 'message': '资产不存在'}), 404
    
    return jsonify({'code': 0, 'message': '资产更新成功'})


@app.route('/api/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """删除资产"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'code': 404, 'message': '资产不存在'}), 404
    
    return jsonify({'code': 0, 'message': '资产删除成功'})


# ==================== 收入接口 ====================

@app.route('/api/incomes', methods=['GET'])
def get_incomes():
    """获取收入记录（支持筛选）"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    
    query = 'SELECT * FROM incomes WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    query += ' ORDER BY date DESC, create_time DESC'
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        incomes = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'code': 0, 'data': incomes, 'message': 'success'})


@app.route('/api/incomes/<income_id>', methods=['GET'])
def get_income(income_id):
    """获取单条收入"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM incomes WHERE id = ?', (income_id,))
        income = cursor.fetchone()
        if income:
            return jsonify({'code': 0, 'data': dict(income), 'message': 'success'})
        return jsonify({'code': 404, 'data': None, 'message': '收入记录不存在'}), 404


@app.route('/api/incomes', methods=['POST'])
def create_income():
    """添加收入"""
    data = request.get_json()
    
    if not data.get('amount') or float(data.get('amount', 0)) <= 0:
        return jsonify({'code': 400, 'message': '请输入有效金额'}), 400
    if not data.get('date'):
        return jsonify({'code': 400, 'message': '请选择日期'}), 400
    
    income_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO incomes (id, category, amount, date, note, create_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            income_id,
            data.get('category', 'other'),
            float(data.get('amount', 0)),
            data.get('date'),
            data.get('note', ''),
            now
        ))
        conn.commit()
    
    return jsonify({
        'code': 0,
        'data': {'id': income_id},
        'message': '收入添加成功'
    }), 201


@app.route('/api/incomes/<income_id>', methods=['PUT'])
def update_income(income_id):
    """更新收入"""
    data = request.get_json()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE incomes 
            SET category = ?, amount = ?, date = ?, note = ?
            WHERE id = ?
        ''', (
            data.get('category'),
            float(data.get('amount', 0)),
            data.get('date'),
            data.get('note', ''),
            income_id
        ))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'code': 404, 'message': '收入记录不存在'}), 404
    
    return jsonify({'code': 0, 'message': '收入更新成功'})


@app.route('/api/incomes/<income_id>', methods=['DELETE'])
def delete_income(income_id):
    """删除收入"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM incomes WHERE id = ?', (income_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'code': 404, 'message': '收入记录不存在'}), 404
    
    return jsonify({'code': 0, 'message': '收入删除成功'})


# ==================== 支出接口 ====================

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """获取支出记录（支持筛选）"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    
    query = 'SELECT * FROM expenses WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    query += ' ORDER BY date DESC, create_time DESC'
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        expenses = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'code': 0, 'data': expenses, 'message': 'success'})


@app.route('/api/expenses/<expense_id>', methods=['GET'])
def get_expense(expense_id):
    """获取单条支出"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        expense = cursor.fetchone()
        if expense:
            return jsonify({'code': 0, 'data': dict(expense), 'message': 'success'})
        return jsonify({'code': 404, 'data': None, 'message': '支出记录不存在'}), 404


@app.route('/api/expenses', methods=['POST'])
def create_expense():
    """添加支出"""
    data = request.get_json()
    
    if not data.get('amount') or float(data.get('amount', 0)) <= 0:
        return jsonify({'code': 400, 'message': '请输入有效金额'}), 400
    if not data.get('date'):
        return jsonify({'code': 400, 'message': '请选择日期'}), 400
    
    expense_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (id, category, amount, date, note, create_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            expense_id,
            data.get('category', 'other'),
            float(data.get('amount', 0)),
            data.get('date'),
            data.get('note', ''),
            now
        ))
        conn.commit()
    
    return jsonify({
        'code': 0,
        'data': {'id': expense_id},
        'message': '支出添加成功'
    }), 201


@app.route('/api/expenses/<expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """更新支出"""
    data = request.get_json()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE expenses 
            SET category = ?, amount = ?, date = ?, note = ?
            WHERE id = ?
        ''', (
            data.get('category'),
            float(data.get('amount', 0)),
            data.get('date'),
            data.get('note', ''),
            expense_id
        ))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'code': 404, 'message': '支出记录不存在'}), 404
    
    return jsonify({'code': 0, 'message': '支出更新成功'})


@app.route('/api/expenses/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """删除支出"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'code': 404, 'message': '支出记录不存在'}), 404
    
    return jsonify({'code': 0, 'message': '支出删除成功'})


# ==================== 统计接口 ====================

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """获取汇总统计数据"""
    now = datetime.now()
    month_start = now.replace(day=1).strftime('%Y-%m-%d')
    
    # 计算月末
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    from datetime import timedelta
    month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 总资产
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM assets')
        total_assets = cursor.fetchone()['total']
        
        # 本月收入
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total 
            FROM incomes 
            WHERE date >= ? AND date <= ?
        ''', (month_start, month_end))
        month_income = cursor.fetchone()['total']
        
        # 本月支出
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total 
            FROM expenses 
            WHERE date >= ? AND date <= ?
        ''', (month_start, month_end))
        month_expense = cursor.fetchone()['total']
    
    return jsonify({
        'code': 0,
        'data': {
            'total_assets': total_assets,
            'month_income': month_income,
            'month_expense': month_expense,
            'month_balance': month_income - month_expense
        },
        'message': 'success'
    })


@app.route('/api/statistics/assets-by-type', methods=['GET'])
def get_assets_by_type():
    """按类型统计资产"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT type, SUM(amount) as total 
            FROM assets 
            GROUP BY type 
            HAVING total > 0
            ORDER BY total DESC
        ''')
        data = [{'type': row['type'], 'amount': row['total']} for row in cursor.fetchall()]
    
    return jsonify({'code': 0, 'data': data, 'message': 'success'})


@app.route('/api/statistics/expenses-by-category', methods=['GET'])
def get_expenses_by_category():
    """按类别统计支出（默认本月）"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 默认本月
    if not start_date:
        now = datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        now = datetime.now()
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        from datetime import timedelta
        end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE date >= ? AND date <= ?
            GROUP BY category 
            HAVING total > 0
            ORDER BY total DESC
        ''', (start_date, end_date))
        data = [{'category': row['category'], 'amount': row['total']} for row in cursor.fetchall()]
    
    return jsonify({'code': 0, 'data': data, 'message': 'success'})


@app.route('/api/statistics/incomes-by-category', methods=['GET'])
def get_incomes_by_category():
    """按类别统计收入（默认本月）"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        now = datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        now = datetime.now()
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        from datetime import timedelta
        end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM incomes 
            WHERE date >= ? AND date <= ?
            GROUP BY category 
            HAVING total > 0
            ORDER BY total DESC
        ''', (start_date, end_date))
        data = [{'category': row['category'], 'amount': row['total']} for row in cursor.fetchall()]
    
    return jsonify({'code': 0, 'data': data, 'message': 'success'})


@app.route('/api/statistics/monthly-trend', methods=['GET'])
def get_monthly_trend():
    """获取近6个月收支趋势"""
    months = request.args.get('months', 6, type=int)
    
    result = []
    now = datetime.now()
    
    for i in range(months - 1, -1, -1):
        # 计算月份
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1
        
        from datetime import timedelta
        next_month_start = datetime(next_year, next_month, 1)
        month_end = (next_month_start - timedelta(days=1)).strftime('%Y-%m-%d')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM incomes 
                WHERE date >= ? AND date <= ?
            ''', (month_start, month_end))
            income = cursor.fetchone()['total']
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM expenses 
                WHERE date >= ? AND date <= ?
            ''', (month_start, month_end))
            expense = cursor.fetchone()['total']
        
        result.append({
            'month': f"{month}月",
            'year_month': f"{year}-{month:02d}",
            'income': income,
            'expense': expense,
            'balance': income - expense
        })
    
    return jsonify({'code': 0, 'data': result, 'message': 'success'})


# ==================== CSV导出接口 ====================

@app.route('/api/export/assets', methods=['GET'])
def export_assets_csv():
    """导出资产CSV"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assets ORDER BY update_time DESC')
        assets = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '资产名称', '资产类型', '金额', '备注', '更新时间'])
    
    for asset in assets:
        writer.writerow([
            asset['id'],
            asset['name'],
            asset['type'],
            asset['amount'],
            asset['note'],
            asset['update_time']
        ])
    
    content = '\ufeff' + output.getvalue()  # UTF-8 BOM
    
    return Response(
        content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=assets_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@app.route('/api/export/incomes', methods=['GET'])
def export_incomes_csv():
    """导出收入CSV"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM incomes ORDER BY date DESC')
        incomes = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '收入类型', '金额', '日期', '备注', '创建时间'])
    
    for income in incomes:
        writer.writerow([
            income['id'],
            income['category'],
            income['amount'],
            income['date'],
            income['note'],
            income['create_time']
        ])
    
    content = '\ufeff' + output.getvalue()
    
    return Response(
        content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=incomes_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@app.route('/api/export/expenses', methods=['GET'])
def export_expenses_csv():
    """导出支出CSV"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
        expenses = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '支出类型', '金额', '日期', '备注', '创建时间'])
    
    for expense in expenses:
        writer.writerow([
            expense['id'],
            expense['category'],
            expense['amount'],
            expense['date'],
            expense['note'],
            expense['create_time']
        ])
    
    content = '\ufeff' + output.getvalue()
    
    return Response(
        content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=expenses_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


# ==================== CSV导入接口 ====================

@app.route('/api/import/assets', methods=['POST'])
def import_assets_csv():
    """导入资产CSV"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请选择文件'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'code': 400, 'message': '请上传CSV文件'}), 400
    
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        
        imported = 0
        with get_db() as conn:
            cursor = conn.cursor()
            for row in reader:
                asset_id = row.get('ID') or generate_id()
                
                # 检查是否存在
                cursor.execute('SELECT id FROM assets WHERE id = ?', (asset_id,))
                if cursor.fetchone():
                    # 更新
                    cursor.execute('''
                        UPDATE assets 
                        SET name = ?, type = ?, amount = ?, note = ?, update_time = ?
                        WHERE id = ?
                    ''', (
                        row.get('资产名称', ''),
                        row.get('资产类型', 'other'),
                        float(row.get('金额', 0)),
                        row.get('备注', ''),
                        row.get('更新时间') or datetime.now().isoformat(),
                        asset_id
                    ))
                else:
                    # 插入
                    cursor.execute('''
                        INSERT INTO assets (id, name, type, amount, note, update_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        asset_id,
                        row.get('资产名称', ''),
                        row.get('资产类型', 'other'),
                        float(row.get('金额', 0)),
                        row.get('备注', ''),
                        row.get('更新时间') or datetime.now().isoformat()
                    ))
                imported += 1
            conn.commit()
        
        return jsonify({'code': 0, 'data': {'imported': imported}, 'message': f'成功导入 {imported} 条资产记录'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'导入失败: {str(e)}'}), 500


@app.route('/api/import/incomes', methods=['POST'])
def import_incomes_csv():
    """导入收入CSV"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请选择文件'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'code': 400, 'message': '请上传CSV文件'}), 400
    
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        
        imported = 0
        with get_db() as conn:
            cursor = conn.cursor()
            for row in reader:
                income_id = row.get('ID') or generate_id()
                
                cursor.execute('SELECT id FROM incomes WHERE id = ?', (income_id,))
                if cursor.fetchone():
                    cursor.execute('''
                        UPDATE incomes 
                        SET category = ?, amount = ?, date = ?, note = ?
                        WHERE id = ?
                    ''', (
                        row.get('收入类型', 'other'),
                        float(row.get('金额', 0)),
                        row.get('日期', ''),
                        row.get('备注', ''),
                        income_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO incomes (id, category, amount, date, note, create_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        income_id,
                        row.get('收入类型', 'other'),
                        float(row.get('金额', 0)),
                        row.get('日期', ''),
                        row.get('备注', ''),
                        row.get('创建时间') or datetime.now().isoformat()
                    ))
                imported += 1
            conn.commit()
        
        return jsonify({'code': 0, 'data': {'imported': imported}, 'message': f'成功导入 {imported} 条收入记录'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'导入失败: {str(e)}'}), 500


@app.route('/api/import/expenses', methods=['POST'])
def import_expenses_csv():
    """导入支出CSV"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请选择文件'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'code': 400, 'message': '请上传CSV文件'}), 400
    
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        
        imported = 0
        with get_db() as conn:
            cursor = conn.cursor()
            for row in reader:
                expense_id = row.get('ID') or generate_id()
                
                cursor.execute('SELECT id FROM expenses WHERE id = ?', (expense_id,))
                if cursor.fetchone():
                    cursor.execute('''
                        UPDATE expenses 
                        SET category = ?, amount = ?, date = ?, note = ?
                        WHERE id = ?
                    ''', (
                        row.get('支出类型', 'other'),
                        float(row.get('金额', 0)),
                        row.get('日期', ''),
                        row.get('备注', ''),
                        expense_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO expenses (id, category, amount, date, note, create_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        expense_id,
                        row.get('支出类型', 'other'),
                        float(row.get('金额', 0)),
                        row.get('日期', ''),
                        row.get('备注', ''),
                        row.get('创建时间') or datetime.now().isoformat()
                    ))
                imported += 1
            conn.commit()
        
        return jsonify({'code': 0, 'data': {'imported': imported}, 'message': f'成功导入 {imported} 条支出记录'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'导入失败: {str(e)}'}), 500


# ==================== 批量操作接口 ====================

@app.route('/api/clear-all', methods=['DELETE'])
def clear_all_data():
    """清空所有数据"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM assets')
        cursor.execute('DELETE FROM incomes')
        cursor.execute('DELETE FROM expenses')
        conn.commit()
    
    return jsonify({'code': 0, 'message': '所有数据已清空'})


@app.route('/api/batch/assets', methods=['POST'])
def batch_create_assets():
    """批量创建资产"""
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({'code': 400, 'message': '请提供资产数据'}), 400
    
    created = 0
    with get_db() as conn:
        cursor = conn.cursor()
        for item in items:
            asset_id = generate_id()
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO assets (id, name, type, amount, note, update_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                asset_id,
                item.get('name', ''),
                item.get('type', 'other'),
                float(item.get('amount', 0)),
                item.get('note', ''),
                now
            ))
            created += 1
        conn.commit()
    
    return jsonify({'code': 0, 'data': {'created': created}, 'message': f'成功创建 {created} 条资产记录'})


@app.route('/api/batch/incomes', methods=['POST'])
def batch_create_incomes():
    """批量创建收入"""
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({'code': 400, 'message': '请提供收入数据'}), 400
    
    created = 0
    with get_db() as conn:
        cursor = conn.cursor()
        for item in items:
            income_id = generate_id()
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO incomes (id, category, amount, date, note, create_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                income_id,
                item.get('category', 'other'),
                float(item.get('amount', 0)),
                item.get('date', now.split('T')[0]),
                item.get('note', ''),
                now
            ))
            created += 1
        conn.commit()
    
    return jsonify({'code': 0, 'data': {'created': created}, 'message': f'成功创建 {created} 条收入记录'})


@app.route('/api/batch/expenses', methods=['POST'])
def batch_create_expenses():
    """批量创建支出"""
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({'code': 400, 'message': '请提供支出数据'}), 400
    
    created = 0
    with get_db() as conn:
        cursor = conn.cursor()
        for item in items:
            expense_id = generate_id()
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO expenses (id, category, amount, date, note, create_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                expense_id,
                item.get('category', 'other'),
                float(item.get('amount', 0)),
                item.get('date', now.split('T')[0]),
                item.get('note', ''),
                now
            ))
            created += 1
        conn.commit()
    
    return jsonify({'code': 0, 'data': {'created': created}, 'message': f'成功创建 {created} 条支出记录'})


# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'code': 0,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("个人财务管理 API 服务")
    print("=" * 50)
    print("API 地址: http://localhost:5000")
    print("API 文档: 查看 personal_finance_api_doc.md")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
