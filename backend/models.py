from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    steps = relationship("Step", back_populates="workflow")
    executions = relationship("Execution", back_populates="workflow")


class Step(Base):
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    model = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    completion_criteria = Column(Text, nullable=True)
    retry_limit = Column(Integer, nullable=False, default=0)
    step_order = Column(Integer)   # ⭐ THIS MUST EXIST
    workflow = relationship("Workflow", back_populates="steps")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(String(20), nullable=False, default="RUNNING")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="executions")
    step_logs = relationship("ExecutionStepLog", back_populates="execution")


class ExecutionStepLog(Base):
    __tablename__ = "execution_step_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="RUNNING")
    output = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    execution = relationship("Execution", back_populates="step_logs")
