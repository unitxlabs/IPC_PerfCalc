from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base


class IPCModel(Base):
    __tablename__ = "ipc_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    cpu_model = Column(String, nullable=True)
    ram = Column(String, nullable=True)
    gpu_info = Column(String, nullable=True)
    ssd = Column(String, nullable=True)
    hdd = Column(String, nullable=True)

    test_records = relationship(
        "TestRecord",
        back_populates="ipc_model",
        cascade="all",  # 删除 IPC 时级联删测试记录；删除记录不会反删 IPC
        passive_deletes=True,
    )


class TestRecord(Base):
    __tablename__ = "test_records"

    id = Column(Integer, primary_key=True, index=True)
    ipc_model_id = Column(
        Integer, ForeignKey("ipc_models.id", ondelete="CASCADE"), nullable=False
    )
    software_version = Column(String, nullable=False)
    resolution_mp = Column(Integer, nullable=False)
    camera_count = Column(Integer, nullable=False)
    model_count = Column(Integer, nullable=False, default=2)
    segments_count = Column(Integer, nullable=False, default=50)
    image_count = Column(Integer, nullable=True, default=48)
    save_image = Column(Integer, nullable=True, default=0)  # 0/1 to fit SQLite boolean
    measured_perf_mps = Column(Float, nullable=False)
    ex_perf_mps = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ipc_model = relationship("IPCModel", back_populates="test_records")


class FormulaCoefficient(Base):
    __tablename__ = "formula_coefficients"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String, nullable=False)
    param_key = Column(String, nullable=False)
    param_value = Column(Float, nullable=False)
    is_active = Column(Integer, default=0)  # 0/1 to fit SQLite boolean


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_params = Column(JSON, nullable=False)
    calculated_result = Column(JSON, nullable=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
