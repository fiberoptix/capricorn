"""
Transaction Model
Banking transactions (debits, credits)
Migrated from Finance Manager transactions table
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profile.id'), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False, index=True)  # 'debit' or 'credit'
    is_processed = Column(Boolean, default=False, nullable=False)  # True if auto-tagged
    
    # Relationships
    user = relationship("UserProfile", backref="transactions")
    account = relationship("Account", backref="transactions")
    category = relationship("Category", backref="transactions")
    
    def __repr__(self):
        category_info = f", category_id={self.category_id}" if self.category_id else ""
        return f"<Transaction(id={self.id}, date={self.transaction_date}, amount={self.amount}, type='{self.transaction_type}'{category_info})>"
    
    @property
    def merchant_name(self):
        """Extract merchant name from description (for future use)"""
        # Simple extraction - can be enhanced with ML later
        return self.description.split(' ')[0] if self.description else None

