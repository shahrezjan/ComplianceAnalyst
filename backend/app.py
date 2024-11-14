from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.sql.expression import func

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./norm.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Enum definitions
class StatusEnum(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class NodeTypeEnum(str, Enum):
    SUB_CHECK = "SUB_CHECK"
    CHECK = "CHECK"
    ROOT = "ROOT"


# Database model
class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    type = Column(String, index=True)
    name = Column(String)
    status = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    children = relationship(
        "Node", back_populates="parent", cascade="all, delete-orphan"
    )
    parent = relationship("Node", back_populates="children", remote_side=[id])

    __table_args__ = (
        CheckConstraint(status.in_([status.value for status in StatusEnum])),
        CheckConstraint(type.in_([type.value for type in NodeTypeEnum])),
    )


# Create the database tables
Base.metadata.create_all(bind=engine)

# FastAPI instance
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # or "*" to allow all in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model for response
class NodeResponse(BaseModel):
    id: int = Field(..., description="The id of the node")
    type: NodeTypeEnum = Field(..., description="The type of the node")
    name: str = Field(..., description="The name of the node")
    status: Optional[StatusEnum] = Field(None, description="The status of the node")
    reason: Optional[str] = Field(None, description="The reason of the node")
    children: List[NodeResponse] = Field(
        default_factory=list, description="The children of the node"
    )

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, node: Node) -> NodeResponse:
        return cls(
            id=node.id,
            type=node.type,
            name=node.name,
            status=node.status,
            reason=node.reason,
            children=[cls.from_orm(child) for child in node.children],
        )


# Endpoint to get a random tree (already included in initial `app.py`)
@app.get(
    "/", response_model=NodeResponse, summary="Get a random root node and its children."
)
def get_random_tree(db: Session = Depends(get_db)) -> NodeResponse:
    root_node = (
        db.query(Node)
        .filter(Node.type == NodeTypeEnum.ROOT)
        .order_by(func.random())
        .first()
    )
    if not root_node:
        raise HTTPException(status_code=404, detail="No root node found.")
    return NodeResponse.from_orm(root_node)


@app.get("/node/{node_id}", response_model=NodeResponse)
def get_node(node_id: int, db: Session = Depends(get_db)) -> NodeResponse:
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeResponse.from_orm(node)


# New endpoint to override node status and propagate changes
@app.put("/override/{node_id}", response_model=NodeResponse)
def override_status(node_id, new_status, db=Depends(get_db)):
    # ...
    """
    Override the status of a node by changing it to the new status and change parent if neccesaary
    """
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.status = new_status
    db.add(node)

    def propagate_up(node):
        # If node has a parent, update its status based on children
        if node.parent:
            parent_status = all(
                child.status == StatusEnum.PASS for child in node.parent.children
            )
            node.parent.status = StatusEnum.PASS if parent_status else StatusEnum.FAIL
            db.add(node.parent)
            propagate_up(node.parent)

    propagate_up(node)

    # Commit changes
    db.commit()
    db.refresh(node)

    return NodeResponse.from_orm(node)  # Return updated node as response
