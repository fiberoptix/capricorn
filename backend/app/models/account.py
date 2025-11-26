"""
Account Model
Banking accounts (checking, savings, credit cards)
Migrated from Finance Manager accounts table
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profile.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=False, index=True)  # 'checking', 'savings', 'credit_card'
    account_number = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)
    balance = Column(Numeric(12, 2), nullable=False, default=0)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    user = relationship("UserProfile", backref="accounts")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.account_type}', balance={self.balance})>"
    
    @property
    def available_credit(self):
        """Calculate available credit for credit cards"""
        if self.account_type == 'credit_card' and self.credit_limit:
            return float(self.credit_limit) - float(self.balance)
        return None

