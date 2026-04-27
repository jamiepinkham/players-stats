from sqlalchemy import Column, Integer, String, JSON, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class PlayerStat(Base):
    """
    Player statistics for a given year.

    Denormalized model - no foreign keys!
    Uses bbrefid (Baseball Reference ID) and year instead of relationships.
    This allows the stats database to be shared across environments.
    """
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    bbrefid = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    stats = Column(JSONB, nullable=False, default={})

    # Composite index for efficient lookups
    __table_args__ = (
        Index('idx_player_stats_bbrefid_year', 'bbrefid', 'year', unique=True),
    )

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "bbrefid": self.bbrefid,
            "year": self.year,
            "stats": self.stats
        }
