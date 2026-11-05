import ast
from io import BytesIO
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from flask import Flask
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.services.ar_evaluation import calculate_basel_ar, evaluate_ar
from api.routes.ar_routes import ar_bp


def sample():
    return pd.DataFrame([
        ['000001', '202301', 'C', '2023-06-01'],
        ['000002', '202301', 'AAA', None],
        ['000001', '202302', 'AAA', '2023-06-01'],
        ['000002', '202302', 'C', None],
        ['000003', '202303', 'AAA', None],
    ], columns=['stkcd', 'ym', '信用评级', '首次违约日期'])


class ArTests(unittest.TestCase):
    def test_monthly_equal_weight_and_invalid_month(self):
        result = evaluate_ar(sample())
        self.assertEqual(result['summary']['overall_ar'], 0.)
        self.assertEqual(result['summary']['valid_months'], 2)
        self.assertEqual(result['summary']['total_months'], 3)
        self.assertEqual([m['AR_CAP'] for m in result['monthly']], [1., -1., None])
        self.assertIn('无未来一年违约', result['monthly'][-1]['reason'])

    def test_matches_original_cap_auc_with_ties(self):
        original = ROOT / 'file/ar_reference_20261021.py'
        tree = ast.parse(original.read_text(encoding='utf-8'))
        func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'calculate_basel_ar')
        # 原程序要求NumPy2；测试环境1.x提供相同积分函数。
        class NumpyCompat:
            def __getattr__(self, name):
                return np.trapz if name == 'trapezoid' and not hasattr(np, name) else getattr(np, name)
        namespace = dict(np=NumpyCompat(), roc_auc_score=roc_auc_score)
        exec(compile(ast.Module(body=[func], type_ignores=[]), str(original), 'exec'), namespace)
        rng = np.random.default_rng(7)
        for _ in range(12):
            data = pd.DataFrame({'risk_rank': rng.integers(1, 21, 200), 'default_1y': rng.integers(0, 2, 200)})
            expected = namespace['calculate_basel_ar'](data)
            actual = calculate_basel_ar(data)
            np.testing.assert_allclose(actual, expected[:2], atol=1e-12)
            self.assertAlmostEqual(actual[0], 2 * actual[1] - 1, places=12)

    def test_window_boundary_and_cleaning(self):
        data = pd.DataFrame([
            ['1', '2024-09', 'C', '2025-09-01'],  # 一年末违约，纳入
            ['2', '2024-09', 'AAA', '2025-09-02'],  # 一年后，不算违约
            ['2', '2024-09', 'AAA', '2025-09-02'],  # 相同重复
            ['3', '2024-10', 'AA', None],  # 窗口不足
            ['4', '2024-09', 'C', '2024-09-01'],  # 评级时已违约
            [None, '2024-09', 'AA', None],
        ], columns=sample().columns)
        result = evaluate_ar(data)
        self.assertEqual(result['summary']['overall_ar'], 1.)
        self.assertEqual(result['summary']['sample_count'], 2)
        self.assertEqual(result['cleaning'], dict(input_rows=6, missing_rows=1, duplicate_rows=1, already_defaulted_rows=1, incomplete_window_rows=1))

    def test_no_valid_ar_is_null(self):
        result = evaluate_ar(sample().tail(1))
        self.assertIsNone(result['summary']['overall_ar'])
        self.assertTrue(result['warnings'])
        self.assertIsNone(calculate_basel_ar(pd.DataFrame({'risk_rank': [1, 2], 'default_1y': [1, 1]}))[0])

    def test_no_complete_windows(self):
        result = evaluate_ar(sample(), data_end='2023-02-01')
        self.assertEqual(result['monthly'], [])
        self.assertIsNone(result['summary']['overall_ar'])

    def test_conflicts_and_bad_inputs(self):
        data = sample()
        with self.assertRaisesRegex(ValueError, '不同评级'):
            evaluate_ar(pd.concat([data, data.iloc[[0]].assign(信用评级='AAA')]))
        with self.assertRaisesRegex(ValueError, '违约日期不一致'):
            evaluate_ar(pd.concat([data, data.iloc[[0]].assign(首次违约日期='2023-07-01')]))
        with self.assertRaisesRegex(ValueError, '无法解析'):
            evaluate_ar(data.assign(首次违约日期='日期错误'))
        with self.assertRaisesRegex(ValueError, '不支持的评级'):
            evaluate_ar(data.assign(信用评级='未知'))
        with self.assertRaisesRegex(ValueError, '缺少必要字段'):
            evaluate_ar(data.drop(columns='首次违约日期'))

    def test_route_upload_and_error(self):
        app = Flask(__name__)
        app.register_blueprint(ar_bp)
        client = app.test_client()
        self.assertEqual(client.post('/ar/calculate').status_code, 400)
        data = sample().rename(columns={'信用评级': '预测信用评级'})
        response = client.post('/ar/calculate', data={
            'file': (BytesIO(data.to_csv(index=False).encode('utf-8-sig')), 'rating.csv'),
            'rating_col': '预测信用评级',
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        result = response.get_json()['data']
        self.assertEqual(result['summary']['overall_ar'], 0.)
        self.assertNotIn('NaN', response.get_data(as_text=True))
        invalid = client.post('/ar/calculate', data={'file': (BytesIO(b'model'), 'model.pkl')})
        self.assertEqual(invalid.status_code, 400)

    def test_excel_and_parquet_upload(self):
        app = Flask(__name__)
        app.register_blueprint(ar_bp)
        for suffix in ['xlsx', 'parquet']:
            content = BytesIO()
            if suffix == 'xlsx':
                sample().to_excel(content, index=False)
            else:
                sample().to_parquet(content, index=False)
            content.seek(0)
            response = app.test_client().post('/ar/calculate', data={'file': (content, f'rating.{suffix}')})
            self.assertEqual(response.status_code, 200, response.get_json())
            self.assertEqual(response.get_json()['data']['summary']['valid_months'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
