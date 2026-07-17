import uuid
import pandas as pd
import boto3
import io
from io import StringIO
from datetime import datetime, timezone
from sqlalchemy import text
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from api.config.database import (
    get_session,
    get_read_only_session,
    read_only_engine,
    engine,
)
from api.config.logging import get_logger
from api.config.constants import S3_BUCKET_NAME, PRODUCT_DF
from api.product.models import Product
from api.product.repository import ProductRepository
from api.product.schemas import ProductBase, ProductResponse
from api.product.service import ProductService

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1/products", tags=["products"])


def get_product_service(session: Session = Depends(get_session)) -> ProductService:
    repository = ProductRepository(session)
    return ProductService(repository)


def get_read_onlyproduct_service(
    session: Session = Depends(get_read_only_session),
) -> ProductService:
    repository = ProductRepository(session)
    return ProductService(repository)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductBase, service: ProductService = Depends(get_product_service)
):
    """Register a new product."""
    logger.info(
        "registering_product",
        product_name=product_data.name,
        product_price=product_data.price,
        status="success",
    )
    return service.create_product(product_data)


@router.get("/", response_model=list[ProductResponse])
def get_all_products(
    service: ProductService = Depends(get_read_onlyproduct_service),
    limit: int = None,
    pageSize: int = 5,
    currentPage: int = 1,
) -> list[ProductResponse]:
    """Get all products."""
    logger.debug("Fetching all products")
    try:
        products = service.get_all_products(limit, pageSize, currentPage)
        logger.info(f"Retrieved {len(products)} products")
        return products
    except Exception as e:
        logger.error(f"Failed to fetch products: {str(e)}")
        raise


@router.get("/dataframe")
def get_all_products_dataframe(upload_to_s3: bool = False):
    """Get all products dataframe."""
    logger.debug("Fetching all products dataframe")

    all_df = []
    try:
        query = text("SELECT * FROM products")

        chunk_iterator = pd.read_sql_query(
            sql=query, con=read_only_engine, chunksize=10
        )
        for chunk_df in chunk_iterator:
            all_df.append(chunk_df)

        concat_df = pd.concat(all_df)

        merged_df = concat_df.merge(PRODUCT_DF, on="name", how="left")
        df_filled = merged_df.fillna("Unknown")

        if upload_to_s3:
            s3_client = boto3.client("s3")
            csv_buffer = StringIO()
            df_filled.to_csv(csv_buffer, index=False)
            object_key = f"{datetime.now().timestamp()}_products_df.csv"
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME, Key=object_key, Body=csv_buffer.getvalue()
            )
            logger.info(f"Successfully uploaded to {object_key}")

        return df_filled.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Failed to fetch products dataframe: {str(e)}")
        raise


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    logger.info(f"Getting product {product_id}")
    try:
        product = service.get_product_by_id(product_id)
        logger.info(f"Retrieved product {product_id}")
        return product
    except Exception as e:
        logger.error(f"Failed to fetch product {product_id}: {e}")
        raise


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product_by_id(
    product_id: uuid.UUID,
    product_data: ProductBase,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Update product by ID."""
    logger.debug(f"Updating product {product_id}")
    try:
        product = service.update_product_by_id(product_id, product_data)
        logger.info(f"Updated product {product_id}")
        return product
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {str(e)}")
        raise


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
):
    logger.info(f"Deleting product: {product_id}")
    service.delete_product_by_id(product_id)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_products_from_csv(upload_file: UploadFile = File(...)):
    contents = await upload_file.read()
    df = pd.read_csv(io.BytesIO(contents))
    df["id"] = [uuid.uuid4() for _ in range(len(df))]
    df["created_at"] = datetime.now(timezone.utc)
    df.to_sql(name=Product.__tablename__, con=engine, if_exists="append", index=False)

    return {
        "message": "CSV data successfully uploaded to RDS",
        "rows_inserted": len(df),
    }
