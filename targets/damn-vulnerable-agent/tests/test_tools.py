import os

from app import tools


def test_read_file_reads_any_path(tmp_path):
    f = tmp_path / "secret.txt"
    f.write_text("contenido sensible")
    assert tools.read_file(str(f)) == "contenido sensible"


def test_run_command_executes_shell():
    out = tools.run_command("echo hola")
    assert "hola" in out
    assert "[exit 0]" in out


def test_query_sql_executes_arbitrary_sql(isolated_db):
    tools.query_sql("CREATE TABLE t (x INTEGER)")
    tools.query_sql("INSERT INTO t VALUES (42)")
    result = tools.query_sql("SELECT * FROM t")
    assert "42" in result


def test_dispatch_routes_to_correct_tool():
    registry = tools.get_registry()
    result = tools.dispatch("run_command", {"command": "echo dispatch-ok"}, registry)
    assert "dispatch-ok" in result


def test_dispatch_unknown_tool_returns_error():
    result = tools.dispatch("no_existe", {}, tools.get_registry())
    assert "no encontrada" in result
