"""
backend/scripts/import_cases_to_neo4j.py

[역할]
- CSV를 읽어서 Neo4j Case 노드로 적재
- 필수 프로퍼티: case_code, clean_text, (선택) route_l2~l4, domain_l1 등

[주의]
- 임베딩 생성은 이 스크립트에서 하지 않고 embed_cases.py에서 별도 수행
"""