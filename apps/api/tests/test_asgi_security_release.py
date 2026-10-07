"""Exercise repaired runtime exposure instead of relying on an audit count alone."""
import asyncio
import pytest
from starlette.requests import Request
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

def test_static_unc_rejected_before_filesystem_resolution(tmp_path,monkeypatch):
    files=StaticFiles(directory=tmp_path)
    def no_io(_path):raise AssertionError('UNC path must not reach realpath/SMB')
    monkeypatch.setattr('starlette.staticfiles.os.path.realpath',no_io)
    assert files.lookup_path('\\\\attacker.invalid\\share')==('',None)

def test_unvalidated_path_cannot_replace_url_authority():
    scope={'type':'http','scheme':'https','server':('localhost',443),'headers':[(b'host',b'localhost')],'path':'@attacker.invalid/','query_string':b''}
    request=Request(scope)
    assert request.url.hostname=='localhost'

def test_urlencoded_form_limits_enforced():
    scope={'type':'http','app':object(),'method':'POST','path':'/','headers':[(b'content-type',b'application/x-www-form-urlencoded')]}
    async def receive():return {'type':'http.request','body':b'a=1&b=2','more_body':False}
    async def parse():
        with pytest.raises(HTTPException) as result:await Request(scope,receive).form(max_fields=1)
        assert result.value.status_code==400
    asyncio.run(parse())
