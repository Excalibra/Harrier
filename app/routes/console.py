from flask_restx import fields, Namespace
from app.utils import get_logger, auth
from app import utils
from app.modules import ErrorMsg
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('console', description="Console information")

logger = get_logger()


@ns.route('/info')
class HarrierConsole(HarrierResource):

    @auth
    def get(self):
        """
        View console information
        """

        data = {
            "device_info": utils.device_info()   # includes CPU, memory and disk information
        }

        return utils.build_ret(ErrorMsg.Success, data)



