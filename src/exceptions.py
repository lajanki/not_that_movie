from urllib.parse import quote

class NotValidArticleException(Exception):

	def __init__(self, title):
		message = f"https://en.wikipedia.org/wiki/{quote(title)} doesn't apper to be a valid movie article."
		super(NotValidArticleException, self).__init__(message)
