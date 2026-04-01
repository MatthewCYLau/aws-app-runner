from api.config.logging import get_logger
from api.product.models import Product
from api.product.repository import ProductRepository
from api.product.schemas import ProductBase, ProductResponse

logger = get_logger(__name__)


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def create_product(self, product_data: ProductBase) -> Product:
        return self.repository.create(product_data)

    def get_all_products(self, limit, pageSize, currentPage) -> list[ProductResponse]:
        if limit:
            products = self.repository.get_all_raw_sql(limit)
        else:
            products = self.repository.get_all(pageSize, currentPage)
        return [ProductResponse.model_validate(product) for product in products]

    def get_product_by_id(self, product_id: int) -> ProductResponse:
        product = self.repository.get_by_id(product_id)
        return ProductResponse.model_validate(product)

    def update_product_by_id(
        self, product_id: str, product_data: ProductBase
    ) -> Product:
        return self.repository.update_by_id(product_id, product_data)

    def delete_product_by_id(self, product_id: str) -> None:
        self.repository.delete_product_by_id(product_id)
