"""initial

Revision ID: 3a91cc42d28e
Revises: 
Create Date: 2024-12-22 13:45:45.540695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a91cc42d28e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


te = sa.Enum('CREATED', 'PROCESSED', 'DONE', 'CANCELED', name='transactionstatus', metadata=sa.MetaData())

def upgrade() -> None:
    te.create(op.get_bind())
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('fullname', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('balance', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fullname')
    )
    op.create_table('transactions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dt', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('from_user_id', sa.Uuid(), nullable=False),
    sa.Column('to_user_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('status', te, nullable=False),
    sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transactions')
    op.drop_table('users')
    # ### end Alembic commands ###
    te.drop(op.get_bind())