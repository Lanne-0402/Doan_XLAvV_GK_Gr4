"""Kiểm tra hợp đồng tích hợp và hiệu quả trên ảnh kiểm soát.

Chạy: python denoise_images/test_denoise.py
"""
import ast
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import module_denoise as mod

FILTERS = [mod.apply_mean_filter, mod.apply_gaussian_filter,
           mod.apply_median_filter, mod.apply_bilateral_filter]


class DenoiseTests(unittest.TestCase):
    def test_shape_dtype_and_original_unchanged(self):
        rng = np.random.default_rng(5)
        for shape in [(31, 37), (31, 37, 3)]:
            original = rng.integers(0, 256, shape, dtype=np.uint8)
            # Bao gồm ảnh cắt không liên tục và ảnh chỉ đọc.
            src = original[:, ::2]
            src.setflags(write=False)
            before = src.copy()
            for fn in FILTERS:
                for k in range(3, 16, 2):
                    out = fn(src, **({'d': k} if fn==mod.apply_bilateral_filter else {'ksize': k}))
                    self.assertEqual(out.shape, src.shape)
                    self.assertEqual(out.dtype, np.uint8)
                    self.assertFalse(np.shares_memory(out, src))
                    np.testing.assert_array_equal(src, before)

    def test_none_and_invalid_images(self):
        for fn in FILTERS:
            self.assertIsNone(fn(None))
            for bad in [[], np.zeros((3,3), np.float32), np.zeros((3,3,4), np.uint8), np.zeros((0,3), np.uint8), np.zeros(3, np.uint8)]:
                with self.assertRaises((TypeError, ValueError)):
                    fn(bad)

    def test_parameters(self):
        img = np.zeros((15, 15), np.uint8)
        for fn in FILTERS:
            kw = 'd' if fn==mod.apply_bilateral_filter else 'ksize'
            for invalid in [True, 3.5, '5', float('nan')]:
                with self.assertRaises(TypeError):
                    fn(img, **{kw: invalid})
            np.testing.assert_array_equal(fn(img, **{kw: 4}), fn(img, **{kw: 5}))
            np.testing.assert_array_equal(fn(img, **{kw: -1}), fn(img, **{kw: 3}))
        for invalid in [-1, np.inf, np.nan]:
            with self.assertRaises(ValueError):
                mod.apply_gaussian_filter(img, sigma=invalid)
        for kw in ['sigma_color', 'sigma_space']:
            for invalid in [0, -1, np.inf, np.nan]:
                with self.assertRaises(ValueError):
                    mod.apply_bilateral_filter(img, **{kw: invalid})

    def test_constant_and_tiny_images(self):
        for shape in [(1,1), (2,2,3), (20,20,3)]:
            src = np.full(shape, 137, np.uint8)
            for fn in FILTERS:
                np.testing.assert_array_equal(fn(src), src)

    def test_median_removes_impulses(self):
        ref = np.full((100,100), 120, np.uint8)
        src = ref.copy()
        src[10::10, 10::10] = 255
        src[15::10, 15::10] = 0
        np.testing.assert_array_equal(mod.apply_median_filter(src, 3), ref)

    def test_gaussian_noise_reduction(self):
        rng = np.random.default_rng(42)
        ref = np.full((100,100), 128, np.uint8)
        src = np.clip(ref.astype(float)+rng.normal(0,20,ref.shape),0,255).astype(np.uint8)
        before = np.mean((src.astype(float)-ref)**2)
        for fn in FILTERS:
            after = np.mean((fn(src).astype(float)-ref)**2)
            self.assertLess(after, before*.5)

    def test_bilateral_preserves_step_edge(self):
        ref = np.full((100,100), 30, np.uint8)
        ref[:,50:] = 220
        mean = mod.apply_mean_filter(ref, 9)
        bilateral = mod.apply_bilateral_filter(ref, d=9, sigma_color=25, sigma_space=75)
        band = np.s_[:,46:54]
        self.assertLess(np.mean((bilateral[band].astype(float)-ref[band])**2),
                        np.mean((mean[band].astype(float)-ref[band])**2))

    def test_main_app_calls_without_loading_gui(self):
        # Kiểm tra trực tiếp các lời gọi mod2 có trong main_app thực tế.
        tree = ast.parse((ROOT.parent/'main_app.py').read_text(encoding='utf-8-sig'))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                 and n.func.value.id == 'mod2']
        self.assertGreaterEqual(len(calls), 7)
        src = np.full((20,20,3), 120, np.uint8)
        for call in calls:
            kwargs = {kw.arg: (5 if isinstance(kw.value, ast.Name) and kw.value.id=='ksize'
                               else ast.literal_eval(kw.value)) for kw in call.keywords}
            result = getattr(mod, call.func.attr)(src, **kwargs)
            self.assertEqual(result.shape, src.shape)


if __name__ == '__main__':
    unittest.main(verbosity=2)
