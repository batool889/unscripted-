import sqlite3
import pytest
from fastapi import HTTPException
from app.auth import Accounts

@pytest.fixture
def db(tmp_path):return Accounts(tmp_path/"accounts.sqlite")
def test_passwords_hashed_and_sessions_opaque(db):
    db.register("demo_user","test-password-123")
    token,user=db.login("DEMO_USER","test-password-123")
    assert user["username"]=="demo_user" and user["study_year"] is None
    with db.connect() as con:
        row=con.execute("SELECT * FROM users").fetchone();session=con.execute("SELECT * FROM sessions").fetchone()
    assert row["password_hash"]!="test-password-123" and session["token_hash"]!=token
    assert db.current(token)["username"]=="demo_user"
def test_bad_password_and_fake_session(db):
    db.register("demo_user","test-password-123")
    for action in [lambda:db.login("demo_user","wrong-password"),lambda:db.current("fake")]:
        with pytest.raises(HTTPException) as e:action()
        assert e.value.status_code==401
def test_profile_persists_and_accounts_isolated(db):
    db.register("first","test-password-123");db.register("second","test-password-456")
    a,_=db.login("first","test-password-123");b,_=db.login("second","test-password-456")
    db.save(a,3,["10211101","10211101"])
    assert db.current(a)["completed"]==["10211101"] and db.current(a)["study_year"]==3
    assert db.current(b)["completed"]==[]
    db.logout(a)
    with pytest.raises(HTTPException):db.current(a)
def test_duplicate_account_rejected(db):
    db.register("demo_user","test-password-123")
    with pytest.raises(HTTPException) as e:db.register("DEMO_USER","test-password-123")
    assert e.value.status_code==409
