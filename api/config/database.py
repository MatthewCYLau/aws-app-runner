import boto3
import os
from sqlalchemy import create_engine, engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from api.config.constants import AWS_REGION

DB_HOST = os.environ.get("DB_HOST")
DB_HOST_READ_ONLY = os.environ.get(
    "DB_HOST_READ_ONLY",
    "postgres-read-replica.c3bji2qrl6dz.us-east-1.rds.amazonaws.com",
)
DB_PORT = 5432
DB_USER = "iam_user"
DB_NAME = "apprunnerdb"

rds_client = boto3.client("rds", region_name=AWS_REGION)


def get_iam_token(read_only: bool = False):
    if read_only:
        db_host = DB_HOST_READ_ONLY
    else:
        db_host = DB_HOST
    return rds_client.generate_db_auth_token(
        DBHostname=db_host, Port=DB_PORT, DBUsername=DB_USER, Region=AWS_REGION
    )


engine = create_engine(f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
read_only_engine = create_engine(
    f"postgresql://{DB_USER}@{DB_HOST_READ_ONLY}:{DB_PORT}/{DB_NAME}"
)


@event.listens_for(engine, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    cparams["password"] = get_iam_token()


@event.listens_for(read_only_engine, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    cparams["password"] = get_iam_token(read_only=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ReadOnlySessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=read_only_engine
)

Base = declarative_base()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_read_only_session():
    session = ReadOnlySessionLocal()
    try:
        yield session
    finally:
        session.close()
