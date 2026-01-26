"""
backend/app/api/routes/step2_graph.py

[역할]
- Step2(Leaf 확정 이후) Graph 확장 API
- seed_case_id(=case_code) 기준으로
  가감요소/관련법규/판례/what-if 후보를 그래프에서 확장해 제공

[입력]
- Step2GraphRequest (schemas/step2_graph.py)

[출력]
- Step2GraphResponse (schemas/step2_graph.py)

[주의]
- Graph는 반드시 Leaf 확정 이후에만 사용
- Step2에서 seed 확정(판단)하지 않음 (이미 확정된 case_code만 받음)
"""