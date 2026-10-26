import unittest
import numpy as np
from counterlift.monitoring import fit_reference, feature_shift

class ShiftChecks(unittest.TestCase):
    def test_reference_calibration_and_shift_detection(self):
        rng=np.random.default_rng(48)
        reference=fit_reference(rng.normal(size=(3000,12)))
        target=rng.normal(size=(1000,12))
        a=feature_shift(target,reference)
        self.assertFalse(a['shift_alert'])
        target[:,0]+=1
        self.assertTrue(feature_shift(target,reference)['shift_alert'])
        self.assertEqual(a['shift_threshold'], feature_shift(target,reference)['shift_threshold'])

    def test_changed_constant_feature_is_flagged(self):
        reference=fit_reference(np.zeros((100,12)))
        self.assertFalse(feature_shift(np.zeros((100,12)),reference)['shift_alert'])
        self.assertTrue(feature_shift(np.ones((100,12)),reference)['constant_feature_changed'])
