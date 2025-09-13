"""add videos table

Revision ID: <newhash>
Revises: 7535094cbba5
Create Date: 2025-09-12 XX:XX:XX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a29b4845b058"
down_revision = "7535094cbba5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "videos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("org_id", sa.String(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("yt_video_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("channel_id", sa.String(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("org_id", "yt_video_id", name="uq_video_per_org"),
    )


def downgrade():
    op.drop_table("videos")
