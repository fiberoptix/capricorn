"""
Budget Model
Budget tracking by category
Migrated from Finance Manager budgets table (currently empty)
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profile.id'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False, index=True)
    
    amount = Column(Numeric(12, 2), nullable=False)
    period = Column(String(20), nullable=False, default='monthly')  # 'monthly', 'yearly'
    
    # Relationships
    user = relationship("UserProfile", backref="budgets")
    category = relationship("Category", backref="budgets")
    
    def __repr__(self):
        return f"<Budget(id={self.id}, category_id={self.category_id}, amount={self.amount}, period='{self.period}')>"

