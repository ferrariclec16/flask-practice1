from flask import Flask, Blueprint, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields


db = SQLAlchemy()


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    note = db.Column(db.String(500), default="")
    done = db.Column(db.Boolean, default=False)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///todo.db",
                      SQLALCHEMY_TRACK_MODIFICATIONS=False,
                      RESTX_ERROR_404_HELP=False)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            todo = Todo(text=request.form['todo'], note=request.form['note'])
            db.session.add(todo)
            db.session.commit()
            return redirect(url_for('index'))
        todos = Todo.query.all()
        return render_template('index.html', todos=todos)


    @app.route('/toggle/<int:id>')
    def toggle(id):
        todo = db.get_or_404(Todo, id)
        todo.done = not todo.done
        db.session.commit()
        return redirect(url_for('index'))


    @app.route('/edit/<int:id>', methods=['GET', 'POST'])
    def edit(id):
        todo = db.get_or_404(Todo, id)
        if request.method == 'POST':
            todo.text = request.form['todo']
            todo.note = request.form['note']
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('edit.html', todo=todo)


    @app.route('/delete/<int:id>')
    def delete(id):
        todo = db.get_or_404(Todo, id)
        db.session.delete(todo)
        db.session.commit()
        return redirect(url_for('index'))


    blueprint = Blueprint("api", __name__, url_prefix="/api")
    api = Api(blueprint, version="1.0", title="Todo API",
              description="Todo 앱의 API: 설명(note)과 완료 여부 필터링", doc="/docs")
    ns = api.namespace("todos", description="할 일 관리")
    todo_model = api.model("Todo", {
        "id": fields.Integer(description="할 일 번호"),
        "text": fields.String(required=True, description="할 일", example="우유 사기"),
        "done": fields.Boolean(description="완료 여부", example=False),
        "note": fields.String(description="설명", example="2리터짜리로"),
    })
    todo_input = api.model("TodoInput", {
        "text": fields.String(required=True, example="우유 사기"),
        "done": fields.Boolean(example=False),
        "note": fields.String(description="설명", example="2리터짜리로"),
    })
    todo_patch = api.model("TodoPatch", {
        "text": fields.String(),
        "done": fields.Boolean,
        "note": fields.String(description="설명"),
    })

    def get_or_abort(id):
        todo = db.session.get(Todo, id)
        if todo is None:
            api.abort(404, f"{id} 번 할 일이 없습니다")
        return todo

    @ns.route("/")
    class TodoList(Resource):
        @ns.doc("목록보기")
        @ns.param("done", "true면 완료만, false면 아직 안 한 것만")
        @ns.marshal_list_with(todo_model)
        def get(self):
            """할 일을 돌려준다. done을 주면 걸러서 돌려준다"""
            q = Todo.query
            done = request.args.get("done")
            if done is not None:
                q = q.filter_by(done=(done.lower() == "true"))
            return q.order_by(Todo.id).all()

        @ns.doc("만들기")
        @ns.expect(todo_input, validate=True)
        @ns.marshal_with(todo_model, code=201)
        def post(self):
            """새 할 일을 만든다"""
            todo = Todo(text=api.payload["text"],
                        done=api.payload.get("done", False),
                        note=api.payload.get("note", ""))
            db.session.add(todo)
            db.session.commit()
            return todo, 201

    @ns.route("/<int:id>")
    @ns.param("id", "할 일의 줄 번호")
    @ns.response(404, "그 번호의 할 일이 없습니다")
    class TodoItem(Resource):
        @ns.doc("하나보기")
        @ns.marshal_with(todo_model)
        def get(self, id):
            """할 일 하나를 돌려준다"""
            return get_or_abort(id)

        @ns.doc("전체바꾸기")
        @ns.expect(todo_input, validate=True)
        @ns.marshal_with(todo_model)
        def put(self, id):
            """할 일 전체를 바꾼다"""
            todo = get_or_abort(id)
            todo.text = api.payload["text"]
            todo.done = api.payload.get("done", False)
            todo.note = api.payload.get("note", "")
            db.session.commit()
            return todo

        @ns.doc("일부바꾸기")
        @ns.expect(todo_patch, validate=True)
        @ns.marshal_with(todo_model)
        def patch(self, id):
            """보낸 칸만 바꾼다"""
            todo = get_or_abort(id)
            if "text" in api.payload:
                todo.text = api.payload["text"]
            if "done" in api.payload:
                todo.done = api.payload["done"]
            if "note" in api.payload:
                todo.note = api.payload["note"]
            db.session.commit()
            return todo

        @ns.doc("지우기")
        @ns.response(204, "삭제 완료")
        def delete(self, id):
            """할 일을 지운다"""
            todo = get_or_abort(id)
            db.session.delete(todo)
            db.session.commit()
            return "", 204

    app.register_blueprint(blueprint)
    return app


# Flask CLI가 create_app을 찾아 실행한다. 테스트도 같은 팩토리를 사용한다.
if __name__ == "__main__":
    create_app().run(debug=True)
