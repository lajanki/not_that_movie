from jobs import create_image



# Map environment to bucket name
bucket_map = {
	"prod": "prod_not_that_movie",
	"stg": "dev_not_that_movie",
	"dev": "dev_not_that_movie",
}

# Map environment to image creation function
create_image_ = {
	"prod": create_image.create_image,
	"stg": create_image.create_image,
	"dev": create_image.get_template_image,
}
