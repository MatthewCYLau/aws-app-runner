import boto3
from sqlalchemy import create_engine, engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


REGION = "us-east-1"
DB_HOST = (
    "terraform-20260402105256633800000001.c3bji2qrl6dz.us-east-1.rds.amazonaws.com"
)
DB_PORT = 5432
DB_USER = "iam_user"
DB_NAME = "apprunnerdb"

rds_client = boto3.client("rds", region_name=REGION)


def get_iam_token():
    return rds_client.generate_db_auth_token(
        DBHostname=DB_HOST, Port=DB_PORT, DBUsername=DB_USER, Region=REGION
    )


engine = create_engine(f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


@event.listens_for(engine, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    cparams["password"] = get_iam_token()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
