import unittest
from app import create_app, db

class TodoApiTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def make(self, **kwargs):
        return self.client.post('/api/todos/', json={"text": "우유 사기", **kwargs})

    def test_create_with_note(self):
        r = self.make(note="2리터짜리로")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json, {"id": 1, "text": "우유 사기", "done": False, "note": "2리터짜리로"})

    def test_list_without_filter_keeps_completed_items(self):
        self.make(done=True)
        self.make(text="책 반납")
        r = self.client.get('/api/todos/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json), 2)
        self.assertEqual(r.json[1]['note'], '')
        self.assertEqual([x['id'] for x in self.client.get('/api/todos/?done=true').json], [1])
        self.assertEqual([x['id'] for x in self.client.get('/api/todos/?done=false').json], [2])

    def test_patch_preserves_omitted_fields(self):
        made = self.make(note="2리터짜리로").json
        r = self.client.patch('/api/todos/1', json={"done": True})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, {**made, 'done': True})

    def test_delete_empty_body_then_notfound(self):
        self.make()
        r = self.client.delete('/api/todos/1')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.data, b'')
        self.assertEqual(self.client.get('/api/todos/1').status_code, 404)

    def test_missing_id_returns_json(self):
        for method, payload in [('get', None), ('patch', {'done': True}), ('put', {'text': '교체'}), ('delete', None)]:
            with self.subTest(method=method):
                r = getattr(self.client, method)('/api/todos/999', **({'json': payload} if payload else {}))
                self.assertEqual(r.status_code, 404)
                self.assertEqual(r.json, {'message': '999 번 할 일이 없습니다'})

if __name__ == '__main__':
    unittest.main()
