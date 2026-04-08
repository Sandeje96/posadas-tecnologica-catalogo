from datetime import datetime
from decimal import Decimal
from app import db


class SaleBatch(db.Model):
    __tablename__ = 'sale_batches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    sales = db.relationship('Sale', backref='batch', lazy=True)
    expenses = db.relationship('BatchExpense', backref='batch', lazy=True, cascade='all, delete-orphan')

    @property
    def is_closed(self):
        return self.closed_at is not None

    @property
    def total_profit_usd(self):
        return sum(Decimal(str(s.profit_usd)) for s in self.sales)

    @property
    def total_profit_ars(self):
        return sum(Decimal(str(s.profit_ars)) for s in self.sales)

    @property
    def total_expenses_usd(self):
        return sum(Decimal(str(e.amount_usd)) for e in self.expenses)

    @property
    def total_expenses_ars(self):
        return sum(Decimal(str(e.amount_ars)) for e in self.expenses)

    @property
    def net_profit_usd(self):
        return self.total_profit_usd - self.total_expenses_usd

    @property
    def net_profit_ars(self):
        return self.total_profit_ars - self.total_expenses_ars

    def __repr__(self):
        return f'<SaleBatch {self.name}>'


class BatchExpense(db.Model):
    __tablename__ = 'batch_expenses'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('sale_batches.id'), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(100), nullable=False, default='otros')
    amount_usd = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    amount_ars = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BatchExpense {self.description}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=False, default='')
    model = db.Column(db.String(100), nullable=False, default='')
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False, default='Accesorios')
    cost_price_usd = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    sale_price_usd = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    image_filename = db.Column(db.String(255), nullable=True)
    ram = db.Column(db.String(50), nullable=True)
    storage = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    stock = db.Column(db.Boolean, default=True, nullable=False)
    mercadolibre_active = db.Column(db.Boolean, default=False, nullable=False)
    badge = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sales = db.relationship('Sale', backref='product', lazy=True)

    def sale_price_ars(self, exchange_rate):
        try:
            rate = Decimal(str(exchange_rate))
            return Decimal(str(self.sale_price_usd)) * rate
        except Exception:
            return Decimal('0')

    @property
    def profit_usd(self):
        try:
            return Decimal(str(self.sale_price_usd)) - Decimal(str(self.cost_price_usd))
        except Exception:
            return Decimal('0')

    @property
    def profit_margin_percent(self):
        try:
            cost = Decimal(str(self.cost_price_usd))
            if cost == 0:
                return Decimal('0')
            return (self.profit_usd / cost) * Decimal('100')
        except Exception:
            return Decimal('0')

    def __repr__(self):
        return f'<Product {self.name}>'


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sales = db.relationship('Sale', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'


class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('sale_batches.id'), nullable=True)
    sale_price_usd = db.Column(db.Numeric(10, 2), nullable=False)
    exchange_rate = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price_ars = db.Column(db.Numeric(12, 2), nullable=False)
    cost_price_usd = db.Column(db.Numeric(10, 2), nullable=False)
    profit_usd = db.Column(db.Numeric(10, 2), nullable=False)
    profit_ars = db.Column(db.Numeric(12, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Sale {self.id}>'


class Setting(db.Model):
    __tablename__ = 'settings'

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=None):
        try:
            setting = cls.query.filter_by(key=key).first()
            if setting:
                return setting.value
            return default
        except Exception:
            return default

    @classmethod
    def set(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            setting.updated_at = datetime.utcnow()
        else:
            setting = cls(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'
