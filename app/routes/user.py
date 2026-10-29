from flask import request
from flask_restx import fields, Namespace
from app.utils import get_logger
from app import utils
from . import  HarrierResource
from app import modules

ns = Namespace('user', description="Administrator login authentication")

logger = get_logger()



login_fields = ns.model('LoginHarrier', {
    'username': fields.String(required=True, description="Username"),
    'password': fields.String(required=True, description="Password"),
})


@ns.route('/login')
class LoginHarrier(HarrierResource):

    @ns.expect(login_fields)
    def post(self):
        """
        User login
        """
        args = self.parse_args(login_fields)


        return build_data(utils.user_login(**args))




@ns.route('/logout')
class LogoutHarrier(HarrierResource):

    def get(self):
        """
        User logout
        """
        token = request.headers.get("Token")
        utils.user_logout(token)

        return build_data({})


change_pass_fields = ns.model('ChangePassHarrier', {
    'old_password': fields.String(required=True, description="Old password"),
    'new_password': fields.String(required=True, description="New password"),
    'check_password': fields.String(required=True, description="Confirm password"),
})


@ns.route('/change_pass')
class ChangePassHarrier(HarrierResource):
    @ns.expect(change_pass_fields)
    def post(self):
        """
        Change password
        """
        args = self.parse_args(change_pass_fields)
        ret = {
            "message": "success",
            "code": 200,
            "data": {}
        }
        token = request.headers.get("Token")

        if args["new_password"] != args["check_password"]:
            ret["code"] = 301
            ret["message"] = "new password and confirmation do not match"
            return ret

        if not args["new_password"]:
            ret["code"] = 302
            ret["message"] = "new password cannot be empty"
            return ret

        if utils.change_pass(token, args["old_password"], args["new_password"]):
            utils.user_logout(token)
        else:
            ret["message"] = "old password is incorrect"
            ret["code"] = 303

        return ret


def build_data(data):
    ret = {
        "message": "success",
        "code": 200,
        "data": {}
    }

    if data:
        ret["data"] = data
    else:
        ret["code"] = 401

    return ret


