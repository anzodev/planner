import argparse

from planner import web
from planner.web.config import Config


parser = argparse.ArgumentParser()
parser.add_argument(
    "--env", type=str, default=None, help="environment configuration file path"
)
args = parser.parse_args()

config = Config.from_env(args.env)
app = web.create_app(config)


if __name__ == "__main__":
    app.templates_auto_reload = True
    app.jinja_options["auto_reload"] = True
    app.run(use_reloader=True, threaded=True)
