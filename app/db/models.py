import datetime
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Politician(Base):
    __tablename__ = "politicians"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    chamber: Mapped[str] = mapped_column(String(50), nullable=False)  # "house" | "senate"
    electorate_or_state: Mapped[str | None] = mapped_column(String(255))
    party: Mapped[str | None] = mapped_column(String(255))
    aph_url: Mapped[str | None] = mapped_column(Text)
    register_pdf_url: Mapped[str | None] = mapped_column(Text)
    updated_at_text: Mapped[str | None] = mapped_column(String(255))  # raw string from APH
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    summaries: Mapped[list["InterestsSummary"]] = relationship(
        back_populates="politician", cascade="all, delete-orphan"
    )


class InterestsSummary(Base):
    __tablename__ = "interests_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    politician_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "pdf" | "unavailable"
    total_interests: Mapped[int | None] = mapped_column(Integer)
    self_properties: Mapped[int | None] = mapped_column(Integer)
    self_shares: Mapped[int | None] = mapped_column(Integer)
    partner_properties: Mapped[int | None] = mapped_column(Integer)
    partner_shares: Mapped[int | None] = mapped_column(Integer)
    children_properties: Mapped[int | None] = mapped_column(Integer)
    children_shares: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    refreshed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    politician: Mapped["Politician"] = relationship(back_populates="summaries")


class RefreshRun(Base):
    __tablename__ = "refresh_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "running" | "success" | "partial" | "failed"
    message: Mapped[str | None] = mapped_column(Text)
