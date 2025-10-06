import typing as t
from jiraone.utils import DotNotation

route_object: dict = {
    "users": "/users/{user_id}",
    "item_id": "/items13/{item_id}",
    "models": "/models/{model_id}",
    "files": "/files/{file_path}",
    "projects": "/projects/{project_id}",
}

route_notation: t.Any = lambda route: DotNotation(route)
routers: t.Dict = route_notation(route_object)