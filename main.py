from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.sql import expression
from sqlalchemy import func
from sqlalchemy.orm import aliased

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///personal_finance.db'
db = SQLAlchemy(app)

# 数据库模型
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    type = db.Column(db.String(10))  # 'income' or 'expense'
    is_deleted = db.Column(db.Boolean, server_default=expression.false(), nullable=False)
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'type': self.type,
            'is_deleted': self.is_deleted
        }

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    balance = db.Column(db.Float, default=0)
    is_deleted = db.Column(db.Boolean, server_default=expression.false(), nullable=False)
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'currency': self.currency,
            'balance': self.balance
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    description = db.Column(db.String(200))
    created_by = db.Column(db.String(50))
    is_deleted = db.Column(db.Boolean, server_default=expression.false(), nullable=False)
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'amount': self.amount,
            'type': self.type,
            'category_id': self.category_id,
            'account_id': self.account_id,
            'description': self.description,
            'created_by': self.created_by
        }

class ExchangeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(3), nullable=False)
    to_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)

with app.app_context():
    db.create_all()

# 路由和视图函数
@app.route('/category', methods=['GET', 'POST', 'PUT', 'DELETE'])
def category_operations():
    if request.method == 'GET':
        category_id = request.args.get('id')
        if category_id:
            category = Category.query.get_or_404(category_id)
            return jsonify(category.to_dict())
        else:
            parent_id = request.args.get('parent_id')
            category_type = request.args.get('category_type')
            categories = Category.query.filter_by(is_deleted=False)
            if parent_id:
                categories = categories.filter_by(parent_id=parent_id)
            else:
                categories = categories.filter_by(parent_id=None)
            if category_type:
                categories = categories.filter_by(type=category_type)
            return jsonify([category.to_dict() for category in categories.all()])

    elif request.method == 'POST':
        data = request.json
        category = Category(name=data['name'], parent_id=data.get('parent_id'), type=data['type'])
        db.session.add(category)
        db.session.commit()
        return jsonify({'message': 'Category added successfully', 'id': category.id}), 201

    elif request.method == 'PUT':
        data = request.json
        category = Category.query.get_or_404(data['id'])
        category.name = data.get('name', category.name)
        category.is_deleted = data.get('is_deleted', category.is_deleted)
        category.parent_id = data.get('parent_id', category.parent_id)
        category.type = data.get('type', category.type)
        db.session.commit()
        return jsonify({'message': 'Category updated successfully'})

    elif request.method == 'DELETE':
        category_id = request.args.get('id')
        category = Category.query.get_or_404(category_id)
        category.is_deleted = True
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully'})

@app.route('/categories/hierarchical', methods=['GET'])
def get_hierarchical_categories():
    category_type = request.args.get('type')  # 可以是 'income' 或 'expense'

    # 创建两个别名以区分父类别和子类别
    ParentCategory = aliased(Category)
    ChildCategory = aliased(Category)

    # 构建查询
    query = db.session.query(ParentCategory, ChildCategory)\
        .outerjoin(ChildCategory, ParentCategory.id == ChildCategory.parent_id)\
        .filter(ParentCategory.parent_id == None)\
        .filter(ParentCategory.is_deleted == False)

    # 如果指定了类型，添加类型过滤
    if category_type:
        query = query.filter(ParentCategory.type == category_type)

    # 执行查询
    results = query.all()

    # 组织结果
    categories = {}
    for parent, child in results:
        if parent.id not in categories:
            categories[parent.id] = parent.to_dict()
            categories[parent.id]['subcategories'] = []
        
        if child and not child.is_deleted:
            child_dict = child.to_dict()
            child_dict.pop('parent_id', None)  # 移除子类别中的parent_id字段
            categories[parent.id]['subcategories'].append(child_dict)

    # 转换为列表并返回
    return jsonify(list(categories.values()))
    
@app.route('/account', methods=['GET', 'POST', 'PUT', 'DELETE'])
def account_operations():
    if request.method == 'GET':
        account_id = request.args.get('id')
        if account_id:
            account = Account.query.get_or_404(account_id)
            return jsonify(account.to_dict())
        else:
            accounts = Account.query.filter_by(is_deleted=False).all()
            return jsonify([account.to_dict() for account in accounts])

    elif request.method == 'POST':
        data = request.json
        account = Account(name=data['name'], currency=data['currency'], balance=data.get('balance', 0))
        db.session.add(account)
        db.session.commit()
        return jsonify({'message': 'Account added successfully', 'id': account.id}), 201

    elif request.method == 'PUT':
        data = request.json
        account = Account.query.get_or_404(data['id'])
        account.name = data.get('name', account.name)
        account.is_deleted = data.get('is_deleted', account.is_deleted)
        account.currency = data.get('currency', account.currency)
        account.balance = data.get('balance', account.balance)
        db.session.commit()
        return jsonify({'message': 'Account updated successfully'})

    elif request.method == 'DELETE':
        account_id = request.args.get('id')
        account = Account.query.get_or_404(account_id)
        account.is_deleted = True
        db.session.commit()
        return jsonify({'message': 'Account deleted successfully'})
    
@app.route('/transaction', methods=['GET', 'POST', 'PUT', 'DELETE'])
def transaction_operations():
    if request.method == 'GET':
        transaction_id = request.args.get('id')
        if transaction_id:
            transaction = Transaction.query.get_or_404(transaction_id)
            return jsonify(transaction.to_dict())
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            query = Transaction.query.filter_by(is_deleted=False)
            
            # 添加过滤条件
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            category_id = request.args.get('category_id')
            account_id = request.args.get('account_id')
            
            if start_date:
                query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d'))
            if category_id:
                query = query.filter_by(category_id=category_id)
            if account_id:
                query = query.filter_by(account_id=account_id)
            
            pagination = query.order_by(Transaction.date.desc()).paginate(page=page, per_page=per_page)
            
            return jsonify({
                'items': [item.to_dict() for item in pagination.items],
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total
            })

    elif request.method == 'POST':
        data = request.json
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        account = Account.query.get(data['account_id'])
        
        amount_in_rmb = convert_currency(data['amount'], account.currency, 'CNY', date.date())
        
        transaction = Transaction(
            date=date,
            amount=amount_in_rmb,
            type=data['type'],
            category_id=data['category_id'],
            account_id=data['account_id'],
            description=data.get('description'),
            created_by=data.get('created_by')
        )
        db.session.add(transaction)
        
        # 更新账户余额
        if data['type'] == 'income':
            account.balance += data['amount']
        else:
            account.balance -= data['amount']
        
        db.session.commit()
        return jsonify({'message': 'Transaction added successfully', 'id': transaction.id}), 201

    elif request.method == 'PUT':
        data = request.json
        transaction = Transaction.query.get_or_404(data['id'])
        
        # 更新账户余额（先恢复原状，再应用新的变化）
        old_account = Account.query.get(transaction.account_id)
        if transaction.type == 'income':
            old_account.balance -= transaction.amount
        else:
            old_account.balance += transaction.amount
        
        # 更新交易信息
        transaction.date = datetime.strptime(data.get('date', transaction.date.strftime('%Y-%m-%d')), '%Y-%m-%d')
        transaction.amount = data.get('amount', transaction.amount)
        transaction.type = data.get('type', transaction.type)
        transaction.category_id = data.get('category_id', transaction.category_id)
        transaction.account_id = data.get('account_id', transaction.account_id)
        transaction.description = data.get('description', transaction.description)
        
        # 应用新的账户余额变化
        new_account = Account.query.get(transaction.account_id)
        if transaction.type == 'income':
            new_account.balance += transaction.amount
        else:
            new_account.balance -= transaction.amount
        
        db.session.commit()
        return jsonify({'message': 'Transaction updated successfully'})

    elif request.method == 'DELETE':
        transaction_id = request.args.get('id')
        transaction = Transaction.query.get_or_404(transaction_id)
        
        # 恢复账户余额
        account = Account.query.get(transaction.account_id)
        if transaction.type == 'income':
            account.balance -= transaction.amount
        else:
            account.balance += transaction.amount
        
        transaction.is_deleted = True
        db.session.commit()
        return jsonify({'message': 'Transaction deleted successfully'})
    
# 统计查询功能
@app.route('/stats', methods=['GET'])
def get_stats():
    period = request.args.get('period', 'month')
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    
    # 总资产统计
    total_assets = db.session.query(func.sum(Account.balance)).scalar()
    
    # 收入支出统计
    income_expense = db.session.query(
        func.date_trunc(period, Transaction.date).label('period'),
        Transaction.type,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.date.between(start_date, end_date)
    ).group_by(
        func.date_trunc(period, Transaction.date),
        Transaction.type
    ).all()
    
    # 分类统计
    category_stats = db.session.query(
        func.date_trunc(period, Transaction.date).label('period'),
        Category.name,
        func.sum(Transaction.amount).label('total')
    ).join(Category).filter(
        Transaction.date.between(start_date, end_date)
    ).group_by(
        func.date_trunc(period, Transaction.date),
        Category.name
    ).all()
    
    # 账户资金统计
    account_stats = db.session.query(
        func.date_trunc(period, Transaction.date).label('period'),
        Account.name,
        func.sum(Transaction.amount).label('total')
    ).join(Account).filter(
        Transaction.date.between(start_date, end_date)
    ).group_by(
        func.date_trunc(period, Transaction.date),
        Account.name
    ).all()
    
    return jsonify({
        'total_assets': total_assets,
        'income_expense': [{'period': i[0], 'type': i[1], 'total': i[2]} for i in income_expense],
        'category_stats': [{'period': i[0], 'category': i[1], 'total': i[2]} for i in category_stats],
        'account_stats': [{'period': i[0], 'account': i[1], 'total': i[2]} for i in account_stats]
    })

def convert_currency(amount, from_currency, to_currency, date):
    if from_currency == to_currency:
        return amount
    
    rate = ExchangeRate.query.filter_by(
        from_currency=from_currency,
        to_currency=to_currency,
        date=date
    ).first()
    
    if rate is None:
        raise ValueError(f"Exchange rate not found for {from_currency} to {to_currency} on {date}")
    
    return amount * rate.rate

if __name__ == '__main__':
    app.run(debug=True)