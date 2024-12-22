import enum
import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import NUMERIC, Float, Numeric
from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata_obj = sa.MetaData(naming_convention=convention)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.c}

    def __repr__(self):
        d = self.as_dict()
        name = self.__tablename__
        params = ','.join(f'{k}={v}' for k, v in d.items())
        return f'{name}({params})'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fullname: Mapped[str] = mapped_column(nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    password_set_time: Mapped[datetime] = mapped_column(server_default=sa.func.now(), nullable=False) # for token invalidation
    transactions: Mapped[list['Transaction']] = relationship(
        primaryjoin='or_(User.id==Transaction.to_user_id, User.id==Transaction.from_user_id)')

class TransactionStatus(enum.StrEnum):
     CREATED: int = enum.auto()
     PROCESSED: int = enum.auto()
     DONE: int = enum.auto()
     CANCELED: int = enum.auto()

TransactionStateDB = sa.Enum(
    TransactionStatus, metadata=Base.metadata, create_type=False
)

class Transaction(Base):
    __tablename__ = 'transactions'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dt: Mapped[datetime] = mapped_column(server_default=sa.func.now(), server_onupdate=sa.func.now())
    from_user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey('users.id', ondelete='SET NULL'))
    to_user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey('users.id', ondelete='SET NULL'))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(nullable=False, default=TransactionStatus.CREATED)
