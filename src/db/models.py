from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
from typing import List, Optional
from datetime import datetime
import uuid


class User(SQLModel, table=True):
    __tablename__="Users"

    uid: uuid.UUID = Field(
    sa_column=Column(
        pg.UUID, 
        nullable=False,
        primary_key=True,
        default=uuid.uuid4
    ))
    username: str
    email:str
    firstname:str
    lastname:str
    role: str = Field(sa_column=Column(
      pg.VARCHAR,
      nullable=False,
      server_default="user"  
    ))
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )
    password:str
    houses: "House" = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    reviews: "Review" = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})


    def __repr__(self):
        return f"<User> {self.username}, {self.email}, {self.role}, {self.is_verified}, {self.created_at}, {self.updated_at}, {self.password}, {self.uid}, {self.firstname}, {self.lastname}"
    
class House(SQLModel, table=True):
    __tablename__="houses"
    house_uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            nullable=False,
        default=uuid.uuid4
        )
    )
    title: str
    address: str
    state: str
    bedroom: int
    bathroom: int
    price_per_night: float
    description: str
    Available: bool
    rating: float = Field(lt=6,gt=-1, default=0, sa_column=Column(pg.FLOAT))
    user_uid: uuid.UUID = Field(
        default=None,
        foreign_key="Users.uid"
    )
    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP,
            nullable=False,
        default=datetime.now()
        )
    )
    user: "User" = Relationship(back_populates="houses")
    reviews : "Review" = Relationship(back_populates="houses")

    def __repr__(self):
        return f"House {self.title}"

class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    uid: uuid.UUID = Field(
        sa_column= Column(
            pg.UUID,
            primary_key=True,
            nullable=False,
            default=uuid.uuid4()
        )
    )
    review_text: str
    rating: float = Field(lt=6)
    house_uid: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="houses.house_uid"
    )
    user_uid: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="Users.uid"
    )
    created_at: datetime = Field(
        sa_column= Column(
            pg.TIMESTAMP,
            nullable=False,
            default=datetime.now()
        )
    )
    updated_at: datetime = Field(
        sa_column= Column(
            pg.TIMESTAMP,
            nullable=False,
            default=datetime.now()
        )
    )
    user: "User" = Relationship(back_populates="reviews")
    houses: "House" = Relationship(back_populates="reviews")

    def __repr__(self):
        return f"<Review for {self.house_uid} by {self.user_uid}>"