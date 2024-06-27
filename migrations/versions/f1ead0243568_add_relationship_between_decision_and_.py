"""Add relationship between Decision and Feedback

Revision ID: f1ead0243568
Revises: c4d6d2275536
Create Date: 2024-06-28 01:06:27.670491

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1ead0243568'
down_revision = 'c4d6d2275536'
branch_labels = None
depends_on = None


def upgrade():
    # This migration doesn't need to make any changes to the database schema
    # The relationship is established in the Python code
    pass

def downgrade():
    # This migration doesn't need to make any changes to the database schema
    pass
