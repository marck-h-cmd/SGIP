"""add_sensor_id_to_anomalies

Revision ID: 002
Revises: 001
Create Date: 2026-07-16 18:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('anomalies', sa.Column('sensor_id', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('anomalies', 'sensor_id')
