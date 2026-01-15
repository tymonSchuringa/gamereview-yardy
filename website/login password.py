# from flask import Flask, Response, request, redirect, url_for, abort
# from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
# from flask import Blueprint
# app = Flask(__name__)










# def __init__(self, id):
#     self.id = id 





# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         if password == username + '_secret':
#             id = username.split('user')[1]
#             user = user(id)
#             login_user(user)
#             return redirect(request.args.get("next"))
#         else:
#             return abort(401)
#     else:
#         return Response('''
#         <form action''')