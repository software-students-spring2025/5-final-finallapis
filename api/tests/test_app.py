"""
test_app.py

Unit tests for the Flask application using pytest.
Contains tests for authentication, agreement workflows, and view functions.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
# pylint: disable=unused-argument,redefined-outer-name,no-member,line-too-long,useless-return,trailing-newlines,too-few-public-methods

from datetime import datetime

import pytest
from flask import session, url_for
from bson.objectid import ObjectId

from api import app



class DummyCursor:
    """A dummy cursor that supports sort() and iteration over docs."""
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(self.docs)


class DummyCollection:
    """A dummy collection that records inserts and updates."""
    def __init__(self):
        self.docs = []
        self.updated = []

    def find_one(self, query):
        return None

    def insert_one(self, doc):
        class Result:
            inserted_id = ObjectId()
        self.docs.append(doc)
        return Result()

    def find(self, query=None):
        return DummyCursor(self.docs)

    def update_one(self, filter_query, update):
        self.updated.append((filter_query, update))
        return None


@pytest.fixture(autouse=True)
def dummy_db_and_templates(monkeypatch):
    """Patch MongoDB collections and stub out render_template."""
    dummy_users = DummyCollection()
    dummy_agreements = DummyCollection()
    monkeypatch.setattr(app, 'users_coll', dummy_users)
    monkeypatch.setattr(app, 'agreements_coll', dummy_agreements)
    monkeypatch.setattr(app, 'render_template', lambda template, **kwargs: f"<html>{template}</html>")
    yield


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client


@pytest.fixture
def ctx():
    """Provide a Flask request context."""
    with app.app.test_request_context():
        yield


def test_login_required_redirect(ctx):
    @app.login_required
    def secret():
        """Hidden view."""
        return "ok"

    session.clear()
    resp = secret()
    assert resp.status_code == 302
    loc = resp.headers['Location']
    assert '/auth/login' in loc and 'next=' in loc


def test_login_required_allows_access(ctx):
    @app.login_required
    def secret():
        """Hidden view."""
        return "allowed"

    session['user_id'] = 'dummy'
    assert secret() == "allowed"


def test_login_required_metadata(ctx):
    @app.login_required
    def view_func():
        """Docstring"""
        return "x"

    assert view_func.__wrapped__.__name__ == "view_func"
    assert view_func.__wrapped__.__doc__ == "Docstring"


def test_current_user_none(ctx):
    session.clear()
    assert app.current_user() is None


def test_current_user_found(ctx, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'alice'}
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: fake)
    session['user_id'] = str(fake['_id'])
    assert app.current_user() == fake


def test_current_user_cached(ctx, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'bob'}
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: fake)
    session['user_id'] = str(fake['_id'])
    first = app.current_user()
    second = app.current_user()
    assert first is second


def test_register_get(client):
    assert client.get('/auth/register').status_code == 200


def test_register_post_success(client, monkeypatch):
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: None)
    resp = client.post(
        '/auth/register',
        data={'username': 'u', 'email': 'e@x.com', 'password': 'pw'},
        follow_redirects=False
    )
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('home'))


def test_register_post_duplicate(client, monkeypatch):
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: {'_id': ObjectId()})
    resp = client.post(
        '/auth/register',
        data={'username': 'u', 'email': 'e@x.com', 'password': 'pw'},
        follow_redirects=False
    )
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('register'))


def test_login_get(client):
    assert client.get('/auth/login').status_code == 200


def test_login_post_success(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u', 'password_hash': 'h'}
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: fake)
    monkeypatch.setattr(app, 'check_password_hash', lambda h, p: True)
    resp = client.post(
        '/auth/login',
        data={'username_or_email': 'u', 'password': 'pw'},
        follow_redirects=False
    )
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('home'))


def test_login_post_failure(client, monkeypatch):
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: None)
    resp = client.post(
        '/auth/login',
        data={'username_or_email': 'x', 'password': 'pw'},
        follow_redirects=False
    )
    assert resp.status_code == 200


def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess['user_id'] = '123'
    resp = client.get('/auth/logout', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('login'))
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_home_requires_login(client):
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_home_empty_agreements(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 200
    assert b'home.html' in resp.data


def test_home_with_agreements(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr1 = {'party1': {'user_id': fake['_id']}, 'created_at': datetime.utcnow(), 'response_status': 'pending'}
    agr2 = {'party2': {'user_id': fake['_id']}, 'created_at': datetime.utcnow(), 'response_status': 'agreed'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    app.agreements_coll.docs[:] = [agr1, agr2]
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 200


def test_step1_requires_login(client):
    resp = client.get('/agreements/new/step1', follow_redirects=False)
    assert resp.status_code == 302


def test_step1_get_initial(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    assert client.get('/agreements/new/step1').status_code == 200


def test_step1_post_failure_and_success(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    target = {'_id': ObjectId(), 'username': 'v'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    # failure
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: None)
    res_fail = client.post(
        '/agreements/new/step1',
        data={'title': 'T', 'party2_username': 'x'},
        follow_redirects=False
    )
    assert res_fail.status_code == 302
    assert res_fail.headers['Location'].endswith(url_for('step1'))
    # success
    monkeypatch.setattr(app.users_coll, 'find_one', lambda q: target)
    res_succ = client.post(
        '/agreements/new/step1',
        data={'title': 'T', 'party2_username': 'v'},
        follow_redirects=False
    )
    assert res_succ.status_code == 302
    assert res_succ.headers['Location'].endswith(url_for('step2'))


def test_step2_requires_login(client):
    resp = client.get('/agreements/new/step2', follow_redirects=False)
    assert resp.status_code == 302


def test_step2_get_and_post(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
        sess['agreement_data'] = {}
    # GET
    assert client.get('/agreements/new/step2').status_code == 200
    # POST
    data = {
        'sexual_content': 'yes',
        'contraception': 'no',
        'std_check': 'yes',
        'record_allowed': 'no'
    }
    resp_post = client.post(
        '/agreements/new/step2',
        data=data,
        follow_redirects=False
    )
    assert resp_post.status_code == 302
    assert resp_post.headers['Location'].endswith(url_for('signature_page'))


def test_signature_requires_login(client):
    resp = client.get('/agreements/new/signature', follow_redirects=False)
    assert resp.status_code == 302


def test_signature_get_and_post(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    target = {'_id': ObjectId(), 'username': 'v'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
        sess['agreement_data'] = {
            'party1': {'user_id': sess['user_id']},
            'party2': {'user_id': str(target['_id'])}
        }
    # GET
    assert client.get('/agreements/new/signature').status_code == 200
    # POST
    resp_post = client.post(
        '/agreements/new/signature',
        data={'signature_data': 'sig'},
        follow_redirects=False
    )
    assert resp_post.status_code == 302
    assert '/agreements/' in resp_post.headers['Location']


def test_view_agreement_requires_login(client):
    resp = client.get('/agreements/123', follow_redirects=False)
    assert resp.status_code == 302


def test_view_agreement_unauthorized(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr = {
        '_id': ObjectId(),
        'party2': {'user_id': ObjectId()},
        'party1': {'user_id': 'x', 'name': 'x'}
    }
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find_one', lambda q: agr)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.get(f"/agreements/{agr['_id']}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('home'))


def test_view_agreement_authorized(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr = {
        '_id': ObjectId(),
        'party2': {'user_id': fake['_id']},
        'party1': {'user_id': 'x', 'name': 'x'}
    }
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find_one', lambda q: agr)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    assert client.get(f"/agreements/{agr['_id']}").status_code == 200


def test_search_agreements_requires_login(client):
    resp = client.get('/agreements/search', follow_redirects=False)
    assert resp.status_code == 302


def test_search_agreements_get(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    assert client.get('/agreements/search').status_code == 200


def test_search_agreements_post(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find', lambda q: DummyCursor([
        {'title': 'T', 'party1': {'name': 'x'}, 'party2': {'name': 'v'}}
    ]))
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    assert client.post('/agreements/search', data={'keyword': 'x'}).status_code == 200


def test_respond_agreement_requires_login(client):
    resp = client.post('/agreements/123/respond', follow_redirects=False)
    assert resp.status_code == 302


def test_respond_agreement_unauthorized(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr = {'_id': ObjectId(), 'party2': {'user_id': ObjectId()}, 'response_status': 'pending'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find_one', lambda q: agr)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.post(
        f"/agreements/{agr['_id']}/respond",
        data={'response': 'agreed'},
        follow_redirects=False
    )
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('home'))


def test_respond_agreement_success(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr = {'_id': ObjectId(), 'party2': {'user_id': fake['_id']}, 'response_status': 'pending'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find_one', lambda q: agr)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.post(
        f"/agreements/{agr['_id']}/respond",
        data={'response': 'agreed'},
        follow_redirects=False
    )
    assert app.agreements_coll.updated
    assert resp.status_code == 302


def test_edit_agreement_requires_login(client):
    resp = client.get('/agreements/123/edit', follow_redirects=False)
    assert resp.status_code == 302


def test_edit_agreement_unauthorized(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr = {'_id': ObjectId(), 'party1': {'user_id': ObjectId()}, 'response_status': 'rejected'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find_one', lambda q: agr)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.get(f"/agreements/{agr['_id']}/edit", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('home'))


def test_edit_agreement_wrong_status(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr = {'_id': ObjectId(), 'party1': {'user_id': fake['_id']}, 'response_status': 'agreed'}
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find_one', lambda q: agr)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.get(f"/agreements/{agr['_id']}/edit", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('home'))


def test_edit_agreement_success(client, monkeypatch):
    fake = {'_id': ObjectId(), 'username': 'u'}
    agr = {
        '_id': ObjectId(),
        'party1': {'user_id': fake['_id'], 'name': 'u'},
        'party2': {'user_id': ObjectId(), 'name': 'v'},
        'title': 'Agreement Title',
        'content': {'sexual_content': 'yes'},
        'response_status': 'rejected'
    }
    monkeypatch.setattr(app, 'current_user', lambda: fake)
    monkeypatch.setattr(app.agreements_coll, 'find_one', lambda q: agr)
    with client.session_transaction() as sess:
        sess['user_id'] = str(fake['_id'])
    resp = client.get(f"/agreements/{agr['_id']}/edit", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(url_for('step2'))
