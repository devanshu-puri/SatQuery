import os

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_model_integrity_reports_live_filesystem_state():
    response = client.get('/api/model-integrity')
    assert response.status_code == 200, response.text

    payload = response.json()
    real_risat_file = os.path.join(os.path.dirname(__file__), 'data', 'samples', 'eos04_sar_mrs_bengaluru.tif')
    real_risat_exists = os.path.exists(real_risat_file)

    assert 'rs_adaptation' in payload
    assert 'vrsbench_eval' in payload
    assert 'rsvqa_eval' in payload
    assert 'cdvqa_eval' in payload
    assert 'risat_data' in payload
    assert 'geochat_checkpoint' in payload
    assert 'change_model' in payload
    assert 'fusion_model' in payload

    assert payload['rs_adaptation']['status'] in {'PASS', 'PARTIAL', 'NOT_AVAILABLE'}
    assert payload['vrsbench_eval']['status'] in {'PASS', 'PARTIAL'}
    assert payload['rsvqa_eval']['status'] in {'PASS', 'PARTIAL'}
    assert payload['cdvqa_eval']['status'] in {'PASS', 'PARTIAL'}
    assert payload['risat_data']['status'] == ('PASS' if real_risat_exists else 'PARTIAL')
    assert payload['geochat_checkpoint']['status'] in {'PASS', 'PARTIAL', 'FAIL', 'NOT_AVAILABLE'}
    assert payload['change_model']['status'] in {'PASS', 'PARTIAL'}
    assert payload['fusion_model']['status'] in {'PASS', 'PARTIAL'}

    if real_risat_exists:
        assert 'EOS-04' in payload['risat_data']['note'] or 'RISAT' in payload['risat_data']['note']
    else:
        assert 'Sentinel-1 C-band SAR' in payload['risat_data']['note']
        assert 'RISAT-class proxy pending Bhoonidhi access' in payload['risat_data']['note']

    assert payload['rs_adaptation']['manifest'] is not None
    assert payload['vrsbench_eval']['result'] is not None
    assert payload['rsvqa_eval']['result'] is not None
    assert payload['cdvqa_eval']['result'] is not None
    assert payload['vrsbench_eval']['freshness_days'] >= 0
    assert payload['rsvqa_eval']['freshness_days'] >= 0
    assert payload['cdvqa_eval']['freshness_days'] >= 0
