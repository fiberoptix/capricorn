"""
Category Model
Hierarchical category structure with parent-child relationships
Migrated from Finance Manager categories table
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category_type = Column(String(20), nullable=False, index=True)  # 'expense' or 'income'
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Self-referential relationship for hierarchy
    parent = relationship("Category", remote_side=[id], backref="children")
    
    def __repr__(self):
        parent_info = f", parent_id={self.parent_id}" if self.parent_id else ""
        return f"<Category(id={self.id}, name='{self.name}', type='{self.category_type}'{parent_info})>"
    
    @property
    def full_path(self):
        """Get full category path (e.g., 'Parent > Child')"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

