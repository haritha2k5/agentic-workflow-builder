"""SQLAlchemy models for Workflow and Step."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    steps = relationship("Step", back_populates="workflow")


class Step(Base):
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    model = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    completion_criteria = Column(Text, nullable=True)
    retry_limit = Column(Integer, nullable=False, default=0)

    workflow = relationship("Workflow", back_populates="steps")
