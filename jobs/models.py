from pydantic import BaseModel

class ArticleData(BaseModel):
	title: str  
	content: dict
	infobox: dict
	metadata: dict
	img: dict