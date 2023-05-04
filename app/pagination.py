from fastapi_pagination.default import Params as DefaultParams

DEFAULT_PAGE_SIZE = 10
DEFAULT_PAGE_NUMBER = 1

DEFAULT_PAGINATION_PARAMS = DefaultParams(
    page=DEFAULT_PAGE_NUMBER,
    size=DEFAULT_PAGE_SIZE
)
