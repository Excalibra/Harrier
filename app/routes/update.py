from flask_restx import Resource, Namespace
from app.utils import auth
from app import utils
from app import celerytask
from app.modules import ErrorMsg
from app.services.update_nuclei import get_status, STATUS_ID

ns = Namespace('update', description="vulnerability engine self-update")


@ns.route('/nuclei/')
class NucleiUpdate(Resource):
    @auth
    def get(self):
        """
        Nuclei engine/template update status and version info
        """
        item = get_status()
        item.pop("_id", None)
        return utils.build_ret(ErrorMsg.Success, item)

    @auth
    def post(self):
        """
        Start a nuclei engine + templates update on the worker
        """
        item = get_status()
        if item.get("status") == "running":
            return utils.build_ret(ErrorMsg.Success,
                                   {"message": "update already running", "running": True})

        celerytask.nuclei_update_task.delay()
        return utils.build_ret(ErrorMsg.Success,
                               {"message": "update started", "running": True})
