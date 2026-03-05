"""
个人资产与消费账单管理系统 - 主应用
Flask + SQLite + JWT认证
"""

from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import csv
import io
from datetime import datetime, timedelta
from config import Config

# 初始化Flask应用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 初始化数据库
db = SQLAlchemy(app)


# ==================== 数据库模型 ====================

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    assets = db.relationship('Asset', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    incomes = db.relationship('Income', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname or self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Asset(db.Model):
    """资产表"""
    __tablename__ = 'assets'
    
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    note = db.Column(db.Text)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'amount': self.amount,
            'note': self.note or '',
            'update_time': self.update_time.isoformat() if self.update_time else None
        }


class Income(db.Model):
    """收入表"""
    __tablename__ = 'incomes'
    
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    date = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': self.amount,
            'date': self.date,
            'note': self.note or '',
            'create_time': self.create_time.isoformat() if self.create_time else None
        }


class Expense(db.Model):
    """支出表"""
    __tablename__ = 'expenses'
    
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    date = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': self.amount,
            'date': self.date,
            'note': self.note or '',
            'create_time': self.create_time.isoformat() if self.create_time else None
        }


# ==================== 工具函数 ====================

def generate_id():
    """生成唯一ID"""
    import random
    import string
    timestamp = hex(int(datetime.now().timestamp() * 1000))[2:]
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{timestamp}{random_str}"


def token_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'code': 401, 'message': '用户不存在'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'message': '登录已过期，请重新登录'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'message': '无效的登录凭证'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/login')
def login_page():
    """登录页"""
    return render_template('login.html')


# ==================== 认证接口 ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    nickname = data.get('nickname', '').strip()
    
    if not username or len(username) < 3:
        return jsonify({'code': 400, 'message': '用户名至少3个字符'}), 400
    if not password or len(password) < 6:
        return jsonify({'code': 400, 'message': '密码至少6个字符'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400
    
    user = User(username=username, nickname=nickname or username)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '注册成功',
        'data': user.to_dict()
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '请输入用户名和密码'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401
    
    # 生成JWT token
    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(seconds=app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'code': 0,
        'message': '登录成功',
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    })


@app.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户信息"""
    return jsonify({
        'code': 0,
        'data': current_user.to_dict(),
        'message': 'success'
    })


@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """修改密码"""
    data = request.get_json()
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not current_user.check_password(old_password):
        return jsonify({'code': 400, 'message': '原密码错误'}), 400
    
    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '新密码至少6个字符'}), 400
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '密码修改成功'})


# ==================== 资产接口 ====================

@app.route('/api/assets', methods=['GET'])
@token_required
def get_assets(current_user):
    """获取所有资产"""
    assets = current_user.assets.order_by(Asset.update_time.desc()).all()
    return jsonify({
        'code': 0,
        'data': [a.to_dict() for a in assets],
        'message': 'success'
    })


@app.route('/api/assets/<asset_id>', methods=['GET'])
@token_required
def get_asset(current_user, asset_id):
    """获取单个资产"""
    asset = Asset.query.filter_by(id=asset_id, user_id=current_user.id).first()
    if asset:
        return jsonify({'code': 0, 'data': asset.to_dict(), 'message': 'success'})
    return jsonify({'code': 404, 'data': None, 'message': '资产不存在'}), 404


@app.route('/api/assets', methods=['POST'])
@token_required
def create_asset(current_user):
    """创建资产"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'code': 400, 'message': '资产名称不能为空'}), 400
    if not data.get('amount') or float(data.get('amount', 0)) <= 0:
        return jsonify({'code': 400, 'message': '请输入有效金额'}), 400
    
    asset = Asset(
        id=generate_id(),
        user_id=current_user.id,
        name=data.get('name'),
        type=data.get('type', 'other'),
        amount=float(data.get('amount', 0)),
        note=data.get('note', ''),
        update_time=datetime.utcnow()
    )
    
    db.session.add(asset)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'data': {'id': asset.id},
        'message': '资产添加成功'
    }), 201


@app.route('/api/assets/<asset_id>', methods=['PUT'])
@token_required
def update_asset(current_user, asset_id):
    """更新资产"""
    data = request.get_json()
    
    asset = Asset.query.filter_by(id=asset_id, user_id=current_user.id).first()
    if not asset:
        return jsonify({'code': 404, 'message': '资产不存在'}), 404
    
    asset.name = data.get('name', asset.name)
    asset.type = data.get('type', asset.type)
    asset.amount = float(data.get('amount', asset.amount))
    asset.note = data.get('note', asset.note)
    asset.update_time = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '资产更新成功'})


@app.route('/api/assets/<asset_id>', methods=['DELETE'])
@token_required
def delete_asset(current_user, asset_id):
    """删除资产"""
    asset = Asset.query.filter_by(id=asset_id, user_id=current_user.id).first()
    if not asset:
        return jsonify({'code': 404, 'message': '资产不存在'}), 404
    
    db.session.delete(asset)
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '资产删除成功'})


# ==================== 收入接口 ====================

@app.route('/api/incomes', methods=['GET'])
@token_required
def get_incomes(current_user):
    """获取收入记录"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    
    query = current_user.incomes
    
    if start_date:
        query = query.filter(Income.date >= start_date)
    if end_date:
        query = query.filter(Income.date <= end_date)
    if category:
        query = query.filter(Income.category == category)
    
    incomes = query.order_by(Income.date.desc(), Income.create_time.desc()).all()
    
    return jsonify({
        'code': 0,
        'data': [i.to_dict() for i in incomes],
        'message': 'success'
    })


@app.route('/api/incomes', methods=['POST'])
@token_required
def create_income(current_user):
    """添加收入"""
    data = request.get_json()
    
    if not data.get('amount') or float(data.get('amount', 0)) <= 0:
        return jsonify({'code': 400, 'message': '请输入有效金额'}), 400
    if not data.get('date'):
        return jsonify({'code': 400, 'message': '请选择日期'}), 400
    
    income = Income(
        id=generate_id(),
        user_id=current_user.id,
        category=data.get('category', 'other'),
        amount=float(data.get('amount', 0)),
        date=data.get('date'),
        note=data.get('note', ''),
        create_time=datetime.utcnow()
    )
    
    db.session.add(income)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'data': {'id': income.id},
        'message': '收入添加成功'
    }), 201


@app.route('/api/incomes/<income_id>', methods=['PUT'])
@token_required
def update_income(current_user, income_id):
    """更新收入"""
    data = request.get_json()
    
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
    if not income:
        return jsonify({'code': 404, 'message': '收入记录不存在'}), 404
    
    income.category = data.get('category', income.category)
    income.amount = float(data.get('amount', income.amount))
    income.date = data.get('date', income.date)
    income.note = data.get('note', income.note)
    
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '收入更新成功'})


@app.route('/api/incomes/<income_id>', methods=['DELETE'])
@token_required
def delete_income(current_user, income_id):
    """删除收入"""
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
    if not income:
        return jsonify({'code': 404, 'message': '收入记录不存在'}), 404
    
    db.session.delete(income)
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '收入删除成功'})


# ==================== 支出接口 ====================

@app.route('/api/expenses', methods=['GET'])
@token_required
def get_expenses(current_user):
    """获取支出记录"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    
    query = current_user.expenses
    
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category:
        query = query.filter(Expense.category == category)
    
    expenses = query.order_by(Expense.date.desc(), Expense.create_time.desc()).all()
    
    return jsonify({
        'code': 0,
        'data': [e.to_dict() for e in expenses],
        'message': 'success'
    })


@app.route('/api/expenses', methods=['POST'])
@token_required
def create_expense(current_user):
    """添加支出"""
    data = request.get_json()
    
    if not data.get('amount') or float(data.get('amount', 0)) <= 0:
        return jsonify({'code': 400, 'message': '请输入有效金额'}), 400
    if not data.get('date'):
        return jsonify({'code': 400, 'message': '请选择日期'}), 400
    
    expense = Expense(
        id=generate_id(),
        user_id=current_user.id,
        category=data.get('category', 'other'),
        amount=float(data.get('amount', 0)),
        date=data.get('date'),
        note=data.get('note', ''),
        create_time=datetime.utcnow()
    )
    
    db.session.add(expense)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'data': {'id': expense.id},
        'message': '支出添加成功'
    }), 201


@app.route('/api/expenses/<expense_id>', methods=['PUT'])
@token_required
def update_expense(current_user, expense_id):
    """更新支出"""
    data = request.get_json()
    
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    if not expense:
        return jsonify({'code': 404, 'message': '支出记录不存在'}), 404
    
    expense.category = data.get('category', expense.category)
    expense.amount = float(data.get('amount', expense.amount))
    expense.date = data.get('date', expense.date)
    expense.note = data.get('note', expense.note)
    
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '支出更新成功'})


@app.route('/api/expenses/<expense_id>', methods=['DELETE'])
@token_required
def delete_expense(current_user, expense_id):
    """删除支出"""
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    if not expense:
        return jsonify({'code': 404, 'message': '支出记录不存在'}), 404
    
    db.session.delete(expense)
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '支出删除成功'})


# ==================== 统计接口 ====================

@app.route('/api/summary', methods=['GET'])
@token_required
def get_summary(current_user):
    """获取汇总统计数据"""
    now = datetime.now()
    month_start = now.replace(day=1).strftime('%Y-%m-%d')
    
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 总资产
    total_assets = db.session.query(db.func.sum(Asset.amount)).filter(
        Asset.user_id == current_user.id
    ).scalar() or 0
    
    # 本月收入
    month_income = db.session.query(db.func.sum(Income.amount)).filter(
        Income.user_id == current_user.id,
        Income.date >= month_start,
        Income.date <= month_end
    ).scalar() or 0
    
    # 本月支出
    month_expense = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= month_start,
        Expense.date <= month_end
    ).scalar() or 0
    
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
@token_required
def get_assets_by_type(current_user):
    """按类型统计资产"""
    result = db.session.query(
        Asset.type,
        db.func.sum(Asset.amount).label('total')
    ).filter(
        Asset.user_id == current_user.id
    ).group_by(Asset.type).having(db.func.sum(Asset.amount) > 0).all()
    
    data = [{'type': r.type, 'amount': r.total} for r in result]
    
    return jsonify({'code': 0, 'data': data, 'message': 'success'})


@app.route('/api/statistics/expenses-by-category', methods=['GET'])
@token_required
def get_expenses_by_category(current_user):
    """按类别统计支出"""
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
        end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    result = db.session.query(
        Expense.category,
        db.func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).group_by(Expense.category).having(db.func.sum(Expense.amount) > 0).all()
    
    data = [{'category': r.category, 'amount': r.total} for r in result]
    
    return jsonify({'code': 0, 'data': data, 'message': 'success'})


@app.route('/api/statistics/monthly-trend', methods=['GET'])
@token_required
def get_monthly_trend(current_user):
    """获取近6个月收支趋势"""
    months = request.args.get('months', 6, type=int)
    
    result = []
    now = datetime.now()
    
    for i in range(months - 1, -1, -1):
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
        
        next_month_start = datetime(next_year, next_month, 1)
        month_end = (next_month_start - timedelta(days=1)).strftime('%Y-%m-%d')
        
        income = db.session.query(db.func.sum(Income.amount)).filter(
            Income.user_id == current_user.id,
            Income.date >= month_start,
            Income.date <= month_end
        ).scalar() or 0
        
        expense = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date <= month_end
        ).scalar() or 0
        
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
@token_required
def export_assets_csv(current_user):
    """导出资产CSV"""
    assets = current_user.assets.order_by(Asset.update_time.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '资产名称', '资产类型', '金额', '备注', '更新时间'])
    
    for asset in assets:
        writer.writerow([
            asset.id,
            asset.name,
            asset.type,
            asset.amount,
            asset.note,
            asset.update_time.isoformat() if asset.update_time else ''
        ])
    
    content = '\ufeff' + output.getvalue()
    
    return Response(
        content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=assets_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@app.route('/api/export/incomes', methods=['GET'])
@token_required
def export_incomes_csv(current_user):
    """导出收入CSV"""
    incomes = current_user.incomes.order_by(Income.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '收入类型', '金额', '日期', '备注', '创建时间'])
    
    for income in incomes:
        writer.writerow([
            income.id,
            income.category,
            income.amount,
            income.date,
            income.note,
            income.create_time.isoformat() if income.create_time else ''
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
@token_required
def export_expenses_csv(current_user):
    """导出支出CSV"""
    expenses = current_user.expenses.order_by(Expense.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '支出类型', '金额', '日期', '备注', '创建时间'])
    
    for expense in expenses:
        writer.writerow([
            expense.id,
            expense.category,
            expense.amount,
            expense.date,
            expense.note,
            expense.create_time.isoformat() if expense.create_time else ''
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
@token_required
def import_assets_csv(current_user):
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
        for row in reader:
            asset_id = row.get('ID') or generate_id()
            
            existing = Asset.query.filter_by(id=asset_id, user_id=current_user.id).first()
            if existing:
                existing.name = row.get('资产名称', '')
                existing.type = row.get('资产类型', 'other')
                existing.amount = float(row.get('金额', 0))
                existing.note = row.get('备注', '')
                existing.update_time = datetime.utcnow()
            else:
                asset = Asset(
                    id=asset_id,
                    user_id=current_user.id,
                    name=row.get('资产名称', ''),
                    type=row.get('资产类型', 'other'),
                    amount=float(row.get('金额', 0)),
                    note=row.get('备注', ''),
                    update_time=datetime.utcnow()
                )
                db.session.add(asset)
            imported += 1
        
        db.session.commit()
        
        return jsonify({'code': 0, 'data': {'imported': imported}, 'message': f'成功导入 {imported} 条资产记录'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'导入失败: {str(e)}'}), 500


@app.route('/api/import/incomes', methods=['POST'])
@token_required
def import_incomes_csv(current_user):
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
        for row in reader:
            income_id = row.get('ID') or generate_id()
            
            existing = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
            if existing:
                existing.category = row.get('收入类型', 'other')
                existing.amount = float(row.get('金额', 0))
                existing.date = row.get('日期', '')
                existing.note = row.get('备注', '')
            else:
                income = Income(
                    id=income_id,
                    user_id=current_user.id,
                    category=row.get('收入类型', 'other'),
                    amount=float(row.get('金额', 0)),
                    date=row.get('日期', ''),
                    note=row.get('备注', ''),
                    create_time=datetime.utcnow()
                )
                db.session.add(income)
            imported += 1
        
        db.session.commit()
        
        return jsonify({'code': 0, 'data': {'imported': imported}, 'message': f'成功导入 {imported} 条收入记录'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'导入失败: {str(e)}'}), 500


@app.route('/api/import/expenses', methods=['POST'])
@token_required
def import_expenses_csv(current_user):
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
        for row in reader:
            expense_id = row.get('ID') or generate_id()
            
            existing = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
            if existing:
                existing.category = row.get('支出类型', 'other')
                existing.amount = float(row.get('金额', 0))
                existing.date = row.get('日期', '')
                existing.note = row.get('备注', '')
            else:
                expense = Expense(
                    id=expense_id,
                    user_id=current_user.id,
                    category=row.get('支出类型', 'other'),
                    amount=float(row.get('金额', 0)),
                    date=row.get('日期', ''),
                    note=row.get('备注', ''),
                    create_time=datetime.utcnow()
                )
                db.session.add(expense)
            imported += 1
        
        db.session.commit()
        
        return jsonify({'code': 0, 'data': {'imported': imported}, 'message': f'成功导入 {imported} 条支出记录'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'导入失败: {str(e)}'}), 500


# ==================== 批量操作接口 ====================

@app.route('/api/clear-all', methods=['DELETE'])
@token_required
def clear_all_data(current_user):
    """清空当前用户所有数据"""
    Asset.query.filter_by(user_id=current_user.id).delete()
    Income.query.filter_by(user_id=current_user.id).delete()
    Expense.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    return jsonify({'code': 0, 'message': '所有数据已清空'})


# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'code': 0,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# ==================== 初始化数据库 ====================

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("数据库初始化完成")


if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("个人财务管理系统")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("登录页面: http://localhost:5000/login")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
