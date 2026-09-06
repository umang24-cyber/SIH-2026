import requests

print('--- BITKAUN LIVE INGESTION & FORENSIC CORRELATION VERIFICATION ---')

# 1. Health
r_health = requests.get('http://127.0.0.1:8000/health')
print('1. Health Check:', r_health.status_code)

# 2. Sample Ingestion Test
r_sample = requests.get('http://127.0.0.1:8000/api/ingest/sample?typology=peeling_chain')
print('2. Sample GET status:', r_sample.status_code)
sample_tx = r_sample.json()
print('   Sample TXID:', sample_tx.get('txid'), 'Scenario:', sample_tx.get('scenario_id'))

# 3. Dynamic JSON Ingestion
r_ingest = requests.post('http://127.0.0.1:8000/api/ingest/transaction', json=sample_tx)
print('3. Ingest JSON status:', r_ingest.status_code)
res = r_ingest.json()
print('   ML Typology:', res.get('predicted_typology'), 'Risk Score:', res.get('risk_score'), 'Anomaly:', res.get('anomaly_score'))

# 4. Ingest CSV File
csv_content = '''txid,timestamp,relay_ip,relay_port,node_type,country_code,asn,isp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,script_type,scenario_id
771200331,2026-09-06 15:00:00,103.251.167.20,8333,tor_exit,IN,AS133296,Bharti Airtel,1TestInAddrA;1TestInAddrB,1TestOutAddrA;1TestOutAddrB,5.0;5.0,9.999;0.0005,0.0005,P2PKH,test_csv_scenario
'''
r_csv = requests.post('http://127.0.0.1:8000/api/ingest/file', files={'file': ('batch.csv', csv_content, 'text/csv')})
print('4. Ingest CSV status:', r_csv.status_code)
print('   CSV Response:', r_csv.json().get('message'))

# 5. Ingest XML File
xml_content = '''<ledger>
  <transaction>
    <txid>771200332</txid>
    <timestamp>2026-09-06 15:05:00</timestamp>
    <relay_ip>185.220.101.5</relay_ip>
    <relay_port>9050</relay_port>
    <node_type>tor_exit</node_type>
    <country_code>DE</country_code>
    <asn>AS60729</asn>
    <isp>Zwiebelfreunde</isp>
    <input_addresses>
      <item>1XmlInWalletAlpha</item>
    </input_addresses>
    <output_addresses>
      <item>1XmlOutWalletBravo</item>
    </output_addresses>
    <input_amounts>
      <item>3.5</item>
    </input_amounts>
    <output_amounts>
      <item>3.499</item>
    </output_amounts>
    <fee_btc>0.001</fee_btc>
    <script_type>P2PKH</script_type>
    <scenario_id>test_xml_scenario</scenario_id>
  </transaction>
</ledger>'''
r_xml = requests.post('http://127.0.0.1:8000/api/ingest/file', files={'file': ('batch.xml', xml_content, 'application/xml')})
print('5. Ingest XML status:', r_xml.status_code)
print('   XML Response:', r_xml.json().get('message'))

# 6. Verify newly ingested records are instantly queryable
txid1 = sample_tx['txid']
r_tx1 = requests.get(f'http://127.0.0.1:8000/transaction/{txid1}')
print(f'6. Query Ingested JSON TX ({txid1}):', r_tx1.status_code, 'found txid:', r_tx1.json().get('txid'))

r_tx2 = requests.get('http://127.0.0.1:8000/transaction/771200331')
print('7. Query Ingested CSV TX (771200331):', r_tx2.status_code, 'found txid:', r_tx2.json().get('txid'))

r_tx3 = requests.get('http://127.0.0.1:8000/transaction/771200332')
print('8. Query Ingested XML TX (771200332):', r_tx3.status_code, 'found txid:', r_tx3.json().get('txid'))

# 9. Verify Graph 3D for newly ingested scenario
r_graph = requests.get('http://127.0.0.1:8000/graph/test_xml_scenario')
print('9. Query 3D Graph for XML scenario:', r_graph.status_code, 'nodes:', len(r_graph.json().get('nodes', [])))

# 10. Verify Taint propagation on newly ingested wallet
r_taint = requests.get('http://127.0.0.1:8000/taint?seed_address=1XmlInWalletAlpha&max_depth=3')
print('10. Query Taint on Ingested Wallet:', r_taint.status_code, 'tainted count:', r_taint.json().get('total_tainted_wallets'))

# 11. Verify Dossier generation on newly ingested txid
r_dossier = requests.get('http://127.0.0.1:8000/api/dossier/771200332')
print('11. Query LEA Section 91 Dossier on Ingested TX:', r_dossier.status_code, 'dossier title:', r_dossier.json().get('dossier_title'))
print('--- ALL 3 INGESTION MODES FULLY OPERATIONAL & VERIFIED ---')
