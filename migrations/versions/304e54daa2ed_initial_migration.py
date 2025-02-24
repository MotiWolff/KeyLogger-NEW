"""Initial migration

Revision ID: 304e54daa2ed
Revises: 
Create Date: 2025-02-24 10:35:45.988910

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '304e54daa2ed'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('log')
    op.drop_table('user')
    op.drop_table('post')
    op.drop_table('keystrokes')
    op.drop_table('device')
    op.drop_table('feature')
    op.drop_table('newsletter')
    op.drop_table('faq')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('faq',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('question', sa.VARCHAR(length=200), nullable=False),
    sa.Column('answer', sa.TEXT(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('newsletter',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('email', sa.VARCHAR(length=120), nullable=False),
    sa.Column('subscribed_at', sa.DATETIME(), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('feature',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('device',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('device_id', sa.VARCHAR(length=100), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('last_seen', sa.DATETIME(), nullable=True),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('os_info', sa.VARCHAR(length=100), nullable=True),
    sa.Column('hostname', sa.VARCHAR(length=100), nullable=True),
    sa.Column('battery_level', sa.INTEGER(), nullable=True),
    sa.Column('ip_address', sa.VARCHAR(length=45), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('device_id')
    )
    op.create_table('keystrokes',
    sa.Column('id', sa.INTEGER(), nullable=True),
    sa.Column('device_id', sa.TEXT(), nullable=False),
    sa.Column('timestamp', sa.TEXT(), nullable=False),
    sa.Column('content', sa.TEXT(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('post',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), nullable=True),
    sa.Column('content', sa.TEXT(), nullable=True),
    sa.Column('date', sa.DATETIME(), nullable=True),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('email', sa.VARCHAR(length=120), nullable=False),
    sa.Column('password_hash', sa.VARCHAR(length=128), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('log',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('device_id', sa.VARCHAR(length=100), nullable=False),
    sa.Column('content', sa.TEXT(), nullable=False),
    sa.Column('date', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['device.device_id'], name='fk_log_device'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
