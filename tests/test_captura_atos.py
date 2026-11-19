import pytest

from monitor_normas.captura_atos import atos_da_norma, capturado, validar_pagina
from monitor_normas.captura_navegador import ErroNavegador

BASE = "https://leis.org/institucionais/br/aneel/lei"
CANONICO = {
    "data": "2021-12-07",
    "atos_vinculados": [
        {
            "descricao": "Resolução Normativa nº 1174/2026 de 27/10/2026 - Norma em vigor",
            "url": f"{BASE}/resolucao-normativa/2026/1174/resolucao-normativa-n-1174-2026-x",
            "tipo": "REN",
            "ano": "2026",
            "data": "2026-10-27",
        },
        {
            "descricao": "Despacho nº 2006/2024 de 08/07/2024 - Norma em vigor",
            "url": f"{BASE}/despacho/2024/2006/despacho-n-2006-2024-decide",
            "tipo": "DSP",
            "ano": "2024",
            "data": "2024-07-08",
        },
        {
            "descricao": "Resolução Normativa nº 414/2010 de 01/12/2010 - Norma revogada",
            "url": f"{BASE}/resolucao-normativa/2010/414/resolucao-normativa-n-414-2010-x",
            "tipo": "REN",
            "ano": "2010",
            "data": "2010-12-01",
        },
    ],
}


def test_atos_posteriores_em_ordem_com_id():
    atos = atos_da_norma(CANONICO)
    assert [a["id"] for a in atos] == ["dsp-2006-2024", "ren-1174-2026"]
    assert atos[1]["trecho_url"] == "/2026/1174/"
    assert atos[1]["numero"] == "1174"


def test_capturado(tmp_path):
    ato = {"id": "ren-1174-2026"}
    assert not capturado(ato, tmp_path)
    (tmp_path / "ren-1174-2026").mkdir()
    (tmp_path / "ren-1174-2026" / "20261119T100000-abc.html").write_text("x", encoding="utf-8")
    assert capturado(ato, tmp_path)


def test_validar_pagina():
    validar_pagina('<div id="law-content" class="aneel-content">Art. 1º</div>')
    with pytest.raises(ErroNavegador):
        validar_pagina("<title>Um momento…</title>")
