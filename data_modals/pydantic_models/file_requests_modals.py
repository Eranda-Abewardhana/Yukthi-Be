from pydantic import  BaseModel


class File_name(BaseModel):
    file_name: str
    category: str