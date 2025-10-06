from fastapi import Depends, FastAPI

from .dependents import get_query_token, get_token_header
from test_app import internal_admin
from test_app import api_users, api_items

app = FastAPI(dependencies=[Depends(get_query_token)])


app.include_router(api_users.router)
app.include_router(api_items.router)
app.include_router(
    internal_admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}