from importlib.metadata import version

import monitor_normas


def test_versao_do_pacote_igual_a_do_pyproject():
    assert monitor_normas.__version__ == version("monitor-normas-setor-eletrico")
