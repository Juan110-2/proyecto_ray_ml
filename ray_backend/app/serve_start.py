import ray
from ray import serve
from app.main import entrypoint

ray.init()
serve.run(entrypoint)
