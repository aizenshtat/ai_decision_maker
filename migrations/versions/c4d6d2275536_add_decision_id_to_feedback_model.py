"""Add decision_id to Feedback model

Revision ID: c4d6d2275536
Revises: 5c899505b0bd
Create Date: 2024-06-28 00:58:59.643982

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d6d2275536'
down_revision = '5c899505b0bd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.add_column(sa.Column('decision_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_feedback_decision_id', 'decision', ['decision_id'], ['id'])
        
    # Data migration: set decision_id to a valid decision for existing feedback
    op.execute('UPDATE feedback SET decision_id = (SELECT id FROM decision WHERE decision.user_id = feedback.user_id LIMIT 1)')
    
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.alter_column('decision_id')

def downgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.drop_constraint('fk_feedback_decision_id', type_='foreignkey')
        batch_op.drop_column('decision_id')
