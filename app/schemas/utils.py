from bson import ObjectId
from typing import Annotated
from pydantic.functional_validators import BeforeValidator

ObjectIdStr = Annotated[str, BeforeValidator(lambda v: str(v))]
