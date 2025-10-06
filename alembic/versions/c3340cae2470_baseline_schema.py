"""baseline schema

Revision ID: c3340cae2470
Revises: 
Create Date: 2025-10-01 19:11:25.480211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3340cae2470'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# This revision replaces all previous migrations.
replaces = (
    "66d59c68d3e0",
    "7535094cbba5",
    "a29b4845b058",
    "fb8754a8a912",
    "ff1b68c5ea9c",
    "7f455894d063",
    "7f369bccd148",
)


def upgrade() -> None:
    conn = op.get_bind()

    # Debug: print schema + tables Alembic sees before doing anything
    current_schema = conn.exec_driver_sql("SELECT current_schema()").scalar()
    existing_tables = conn.exec_driver_sql(
        "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
    ).fetchall()
    print(f">>> DEBUG: Alembic connection schema = {current_schema}, tables = {existing_tables}")

    # Enforce search_path = public to avoid schema drift
    conn.exec_driver_sql("SET search_path TO public")

    print(">>> DEBUG: entering baseline upgrade()")

    # --- orgs ---
    print(">>> DEBUG: about to create orgs")
    op.create_table(
        'orgs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # --- users ---
    print(">>> DEBUG: about to create users")
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # --- memberships ---
    print(">>> DEBUG: about to create memberships")
    op.create_table(
        'memberships',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'member', name='roleenum'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id', 'org_id')
    )

    # --- videos ---
    print(">>> DEBUG: about to create videos")
    op.create_table(
        'videos',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('yt_video_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('channel_id', sa.String(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'yt_video_id', name='uq_video_per_org')
    )

    # --- comments ---
    print(">>> DEBUG: about to create comments")
    op.create_table(
        'comments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('video_id', sa.String(), nullable=False),
        sa.Column('yt_comment_id', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'yt_comment_id', name='uq_org_comment')
    )

    # --- keywords ---
    print(">>> DEBUG: about to create keywords")
    op.create_table(
        'keywords',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('video_id', sa.String(), nullable=False),
        sa.Column('term', sa.String(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'video_id', 'term', name='uq_org_video_term')
    )

    # --- sentiment_aggregates ---
    print(">>> DEBUG: about to create sentiment_aggregates")
    op.create_table(
        'sentiment_aggregates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('video_id', sa.String(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('pos_pct', sa.Float(), nullable=False),
        sa.Column('neg_pct', sa.Float(), nullable=False),
        sa.Column('neu_pct', sa.Float(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'video_id', 'window_start', 'window_end', name='uq_org_video_window')
    )

    # --- comment_sentiment ---
    print(">>> DEBUG: about to create comment_sentiment")
    op.create_table(
        'comment_sentiment',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('comment_id', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'comment_id', name='uq_org_comment_sentiment')
    )

    print(">>> DEBUG: baseline upgrade() finished")


def downgrade() -> None:
    op.drop_table('comment_sentiment')
    op.drop_table('sentiment_aggregates')
    op.drop_table('keywords')
    op.drop_table('comments')
    op.drop_table('videos')
    op.drop_table('memberships')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('orgs')
