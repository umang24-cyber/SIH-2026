import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_ingest_correlate():
    ledger_csv = """txid,timestamp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,script_type
1001,2026-09-01 10:00:00,[],[],[],[],0.001,P2PKH
1002,2026-09-01 10:05:00,[],[],[],[],0.001,P2PKH
1003,2026-09-01 10:10:00,[],[],[],[],0.001,P2PKH
"""
    network_csv = """txid,relay_timestamp,relay_ip,relay_port,node_type,country_code
1002,2026-09-01 10:04:59,192.168.1.1,8333,residential,US
1003,2026-09-01 10:09:59,192.168.1.2,8333,residential,US
1004,2026-09-01 10:14:59,192.168.1.3,8333,residential,US
"""
    
    response = client.post(
        "/api/ingest/correlate",
        files={
            "ledger_file": ("ledger.csv", ledger_csv.encode('utf-8'), "text/csv"),
            "network_file": ("network.csv", network_csv.encode('utf-8'), "text/csv")
        }
    )
    
    assert response.status_code == 200, response.text
    data = response.json()
    
    assert data["ledger_records"] == 3
    assert data["network_records"] == 3
    assert data["matched_records"] == 2
    assert data["unmatched_ledger"] == 1
    assert data["unmatched_network"] == 1
    assert data["correlation_rate"] == 0.6667
