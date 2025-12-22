from text2sql.orchestrator.graph import build_app


def test_graph_compiles():
    app = build_app()
    assert app is not None
