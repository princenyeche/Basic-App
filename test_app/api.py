import random
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Annotated, Literal, Any
from fastapi import FastAPI, Query, Path, Body, Cookie, Header, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, AfterValidator, Field, HttpUrl, EmailStr
from test_app.routers import routers
from uuid import UUID


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    name: str
    url: HttpUrl

class Item(BaseModel):
    name: str = Field(examples=["Foo"])
    description: str | None = Field(
        default=None, description="Description of the item", max_length=300,
        examples=["A very nice Item"]
    )
    price: float = Field(gt=0, description="Price of the item should be "
                                           "greater than 0",
                         examples=[35.4])
    tax: float = Field(default=None, examples=[3.2])
    tags: list[str] = []
    image: list[Image] | None = None

    # declarative examples
    # model_config = {
    #     "json_schema_extra": {
    #         "examples": [
    #             {
    #                 "name": "Foo",
    #                 "description": "A very nice Item",
    #                 "price": 35.4,
    #                 "tax": 3.2,
    #             }
    #         ]
    #     }
    # }


class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item]

class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


class User(BaseModel):
    username: str
    full_name: str | None = None


class Cookies(BaseModel):
    model_config = {"extra": "forbid"}
    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None


class CommonHeaders(BaseModel):
    model_config = {"extra": "forbid"}

    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str | None = None


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    email: EmailStr
    full_name: str | None = None

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"},
                 {"item_name": "Baz"}]

data = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
}

items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The Bar fighters", "price": 62, "tax": 20.2},
    "baz": {
        "name": "Baz",
        "description": "There goes my baz",
        "price": 50.2,
        "tax": 10.5,
    },
}


def check_valid_id(ids: str):
    if not ids.startswith(("isbn-", "imdb-")):
        raise ValueError(
            'Invalid ID format, it must start with "isbn-" or "imdb-"')
    return ids


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello")
async def hello():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def hello_name(name: str):
    return {"message": f"Hello {name}"}


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
        user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {
                "description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: limit]


@app.get(f"{routers.users}{routers.item_id}")
async def read_item13(item_id: str):
    return {"item_id": item_id}


@app.get("/items2/")
async def read_items2(
        q: Annotated[
            str | None, Query(min_length=3, max_length=50,
                              pattern="^fixedquery$")
        ] = None,
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/items3/")
async def read_items3(q: Annotated[str, Query(min_length=3)] = "fixedquery"):
    """Using default values"""
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/items4/")
async def read_items4(q: Annotated[list[str] | None, Query()] = None):
    """Receiving a list of values"""
    query_items = {"q": q}
    return query_items


@app.get("/items5/")
async def read_items5(
        q: Annotated[
            str | None,
            Query(
                title="Query string",
                description="Query string for the items to search in the "
                            "database that have a good match",
                min_length=3,
            ),
        ] = None,
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}


@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.get("/items6/")
async def read_items6(
        q: Annotated[
            str | None,
            Query(
                alias="item-query",
                title="Query string",
                description="Query string for the items to search in the database that have a good match",
                min_length=3,
                max_length=50,
                pattern="^fixedquery$",
                deprecated=True,
            ),
        ] = None,
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/items7/")
async def read_items7(
        hidden_query: Annotated[
            str | None, Query(include_in_schema=False)] = None,
):
    if hidden_query:
        return {"hidden_query": hidden_query}
    else:
        return {"hidden_query": "Not found"}


@app.get("/items8/")
async def read_items8(
        ids: Annotated[str | None, AfterValidator(check_valid_id)] = None,
):
    if ids:
        item = data.get(ids)
    else:
        ids, item = random.choice(list(data.items()))
    return {"id": ids, "name": item}


@app.get("/items9/{item_id}")
async def read_items9(
        item_id: Annotated[int, Path(title="The ID of the item to get")],
        q: Annotated[str | None, Query(alias="item-query")] = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


@app.get("/items10/{item_id}")
async def read_items10(q: str,
                       item_id: int = Path(title="The ID of the item to get")):
    """Without using the Annotated class in path parameters"""
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


@app.get("/items11/{item_id}")
async def read_items11(
        *,
        item_id: Annotated[
            int, Path(title="The ID of the item to get", ge=0, le=1000)],
        q: str,
        size: Annotated[float, Query(gt=0, lt=10.5)],
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if size:
        results.update({"size": size})
    return results


@app.get("/items12/")
async def read_items12(filter_query: Annotated[FilterParams, Query()]):
    return filter_query


@app.put("/items1/{item_id}")
async def update_item1(
        item_id: Annotated[
            int, Path(title="The ID of the item to get", ge=0, le=1000)],
        q: str | None = None,
        item: Item | None = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if item:
        results.update({"item": item})
    return results


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result


@app.put("/items3/{item_id}")
async def update_item3(item_id: int, item: Item, user: User):
    results = {"item_id": item_id, "item": item, "user": user}
    return results


@app.put("/items4/{item_id}")
async def update_item4(
        item_id: int, item: Item, user: User, importance: Annotated[int, Body()]
):
    results = {"item_id": item_id, "item": item, "user": user,
               "importance": importance}
    return results


# multiple parameter
@app.put("/items5/{item_id}")
async def update_item5(
        *,
        item_id: int,
        item: Item,
        user: User,
        importance: Annotated[int, Body(gt=0)],
        q: str | None = None,
):
    results = {"item_id": item_id, "item": item, "user": user,
               "importance": importance}
    if q:
        results.update({"q": q})
    return results


# return only a single body request
@app.put("/items6/{item_id}")
async def update_item6(item_id: int, item: Annotated[Item, Body(embed=True)]):
    results = {"item_id": item_id, "item": item}
    return results

@app.put("/items7/{item_id}")
async def update_item7(
    item_id: int,
    item: Annotated[
        Item,
        Body(
            examples=[
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                }
            ],
        ),
    ],
):
    results = {"item_id": item_id, "item": item}
    return results


@app.put("/items8/{item_id}")
async def update_item8(
    *,
    item_id: int,
    item: Annotated[
        Item,
        Body(
            openapi_examples={ # noqa
                "normal": {
                    "summary": "A normal example",
                    "description": "A **normal** item works correctly.",
                    "value": {
                        "name": "Foo",
                        "description": "A very nice Item",
                        "price": 35.4,
                        "tax": 3.2,
                    },
                },
                "converted": {
                    "summary": "An example with converted data",
                    "description": "FastAPI can convert "
                                   "price `strings` to actual"
                                   " `numbers` automatically",
                    "value": {
                        "name": "Bar",
                        "price": "35.4",
                    },
                },
                "invalid": {
                    "summary": "Invalid data is rejected with an error",
                    "value": {
                        "name": "Baz",
                        "price": "thirty five point four",
                    },
                },
            },
        ),
    ],
):
    results = {"item_id": item_id, "item": item}
    return results


@app.put("/items9/{item_id}")
async def update_items9(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }


# cookies declaration
@app.get("/items/")
async def cookie_items(ads_id: Annotated[str | None, Cookie()] = None):
    return {"ads_id": ads_id}

# headers declaration
@app.get("/items/")
async def header_items(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}


@app.get("/items2/")
async def cookie_items2(cookies: Annotated[Cookies, Cookie()]):
    return cookies


@app.get("/items2/")
async def headers_items(headers: Annotated[CommonHeaders,
Header(convert_underscores=False)]):
    return headers


# using a return response declaration
@app.get("/items15/")
async def fine_items() -> list[Item]:
    return [
        Item(name="Portal Gun", price=42.0),
        Item(name="Plumbus", price=32.0),
    ]

# using a response_model from the api router
# the response_model parameter takes priority in fastapi
@app.get("/items16/", response_model=list[Item])
async def fine_items() -> Any:
    return [
        {"name": "Portal Gun", "price": 42.0},
        {"name": "Plumbus", "price": 32.0},
    ]

@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn) -> Any:
    return user


# response declaration return type
@app.get("/portal")
async def get_portal(teleport: bool = False) -> Response:
    if teleport:
        return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    return JSONResponse(content={"message": "Here's your interdimensional portal."})


# disabling response model from using fastapi validation or pydantic validation
# when the return type is not a pydantic class such as below which uses a dict object
@app.get("/portal", response_model=None)
async def get_portal(teleport: bool = False) -> Response | dict:
    if teleport:
        return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    return {"message": "Here's your interdimensional portal."}


@app.get(
    "/items/{item_id}/name",
    response_model=Item,
    response_model_include={"name", "description"},
)
async def read_item_name(item_id: str):
    return items[item_id]


@app.get("/items/{item_id}/public", response_model=Item,
         response_model_exclude={"tax"})
async def read_item_public_data(item_id: str):
    return items[item_id]

# user models
def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password


def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
    print("User saved! ..not really")
    return user_in_db


@app.post("/user/", response_model=UserOut)
async def create_user(user_in: UserIn):
    user_saved = fake_save_user(user_in)
    return user_saved