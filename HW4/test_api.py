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

    def test_note_defaults_to_empty(self):
        self.assertEqual(self.make().json['note'], '')

    def test_get_item(self):
        made = self.make(note="설명").json
        r = self.client.get(f"/api/todos/{made['id']}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, made)

    def test_list_without_filter_keeps_completed_items(self):
        self.make(done=True)
        self.make(text="책 반납")
        r = self.client.get('/api/todos/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json), 2)

    def test_filter_true_and_false(self):
        self.make(done=True)
        self.make(text="책 반납")
        for value, expected in [('true', 1), ('false', 2), ('TRUE', 1)]:
            with self.subTest(value=value):
                r = self.client.get('/api/todos/?done=' + value)
                self.assertEqual(r.status_code, 200)
                self.assertEqual([x['id'] for x in r.json], [expected])

    def test_patch_preserves_omitted_fields(self):
        made = self.make(note="2리터짜리로").json
        r = self.client.patch('/api/todos/1', json={"done": True})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, {**made, 'done': True})

    def test_patch_note_and_text(self):
        self.make()
        r = self.client.patch('/api/todos/1', json={"text": "책 반납", "note": "도서관"})
        self.assertEqual(r.json, {"id": 1, "text": "책 반납", "note": "도서관", "done": False})

    def test_put_replaces_fields(self):
        self.make(done=True, note="설명")
        r = self.client.put('/api/todos/1', json={"text": "교체"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, {"id": 1, "text": "교체", "done": False, "note": ""})

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

    def test_invalid_input_is_rejected(self):
        for payload in [{}, {'text': ''}, {'text': '할 일', 'done': 'yes'}, {'text': '할 일', 'note': None}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/api/todos/', json=payload).status_code, 400)

    def test_docs_and_six_operations(self):
        self.assertEqual(self.client.get('/api/docs').status_code, 200)
        schema = self.client.get('/api/swagger.json').json
        self.assertTrue({'get', 'post'} <= schema['paths']['/todos/'].keys())
        self.assertTrue({'get', 'put', 'patch', 'delete'} <= schema['paths']['/todos/{id}'].keys())
        self.assertIn('done', [x['name'] for x in schema['paths']['/todos/']['get']['parameters']])

    def test_api_and_existing_web_screen_share_data(self):
        self.make(note="2리터짜리로")
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('2리터짜리로', r.get_data(as_text=True))
        self.client.post('/edit/1', data={'todo': '책 반납', 'note': '도서관'})
        self.client.get('/toggle/1')
        self.assertEqual(self.client.get('/api/todos/1').json,
                         {'id': 1, 'text': '책 반납', 'note': '도서관', 'done': True})


if __name__ == '__main__':
    unittest.main()
