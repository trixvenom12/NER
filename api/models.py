from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, JSON, ForeignKey, Date
from .database import Base
from datetime import datetime

class Segment(Base):
    __tablename__ = "segment"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    osm_way_id = Column(BigInteger)
    u_node = Column(BigInteger, nullable=False, index=True)
    v_node = Column(BigInteger, nullable=False)
    road_ref = Column(String)
    highway = Column(String)
    length_m = Column(Float, nullable=False)
    free_speed_kph = Column(Integer, nullable=False, default=40)
    mean_slope_deg = Column(Float)
    susceptibility = Column(Float)
    geom = Column(String, nullable=False)

class WeatherObs(Base):
    __tablename__ = "weather_obs"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    point_id = Column(Integer)
    ts = Column(DateTime(timezone=True), nullable=False)
    rain_mm = Column(Float)
    rain_24h_mm = Column(Float)
    visibility_m = Column(Float)
    geom = Column(String)

class Incident(Base):
    __tablename__ = "incident"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    occurred_on = Column(Date)
    kind = Column(String) # landslide | flood | blockade
    duration_hours = Column(Float)
    source_url = Column(String)
    geom = Column(String)

class SegmentRisk(Base):
    __tablename__ = "segment_risk"
    segment_id = Column(BigInteger, ForeignKey("segment.id"), primary_key=True)
    computed_at = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow)
    score = Column(Float, nullable=False)
    band = Column(String, nullable=False)
    factors = Column(JSON, nullable=False)

class Facility(Base):
    __tablename__ = "facility"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    kind = Column(String)
    capacity = Column(Integer)
    attrs = Column(JSON)
    geom = Column(String)

class Report(Base):
    __tablename__ = "report"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    device_id = Column(String)
    kind = Column(String) # blocked | slide | water | sos
    note = Column(String)
    confirmed_count = Column(Integer, default=0)
    geom = Column(String)
