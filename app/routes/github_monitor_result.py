from flask_restx import fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('github_monitor_result', description="Github monitor result details")

logger = get_logger()

base_search_fields = {
    'path': fields.String(required=False, description="Path name"),
    'repo_full_name': fields.String(description="Repository name"),
    'human_content': fields.String(description="Content"),
    'keyword': fields.String(description="Keyword"),
    "github_scheduler_id": fields.String(description="Github monitor ID"),
    'github_task_id': fields.String(description="Task ID")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierGithubMonitorResult(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Github monitor result details
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='github_monitor_result')

        return data


