import unittest
import pandas as pd
import core_logic as core

class TestRankingLogic(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(core.norm("  Test  "), "test")
        self.assertEqual(core.norm("Phage T4"), "phage t4")

    def test_classify_synergy(self):
        # Strong synergy
        self.assertEqual(core.classify_synergy("", 90, 0, 0), "strong synergy")
        self.assertEqual(core.classify_synergy("", 0, 16, 0), "strong synergy")
        self.assertEqual(core.classify_synergy("", 0, 0, 4), "strong synergy")
        
        # PAS
        self.assertEqual(core.classify_synergy("PAS", 50, 2, 1), "PAS")
        
        # Antagonism
        self.assertEqual(core.classify_synergy("antagonism", 0, 0, 0), "antagonism")

    def test_ranking_eligibility_strict_mode(self):
        # Mock row
        row = pd.Series({
            "interpretation_id": 1,
            "antibiotic": "Ciprofloxacin",
            "record_status": "validated",
            "evidence_level": 3
        })
        
        # Mock patient with strict resistant mode
        patient = {
            "resistant": ["ciprofloxacin"],
            "resistant_mode": "strict"
        }
        
        # In core_logic, ranking_eligibility checks resistant_mode
        # Note: ranking_eligibility doesn't call validation_flags in a way that we can easily mock without a DB
        # But we can test the logic if we had a minimal DB
        pass

    def test_score_row_penalties(self):
        patient = {
            "pathogen": "Pseudomonas aeruginosa",
            "sensitive": ["ceftazidime"],
            "resistant": ["ciprofloxacin"],
            "resistant_mode": "soft"
        }
        
        row_sensitive = pd.Series({
            "pathogen": "Pseudomonas aeruginosa",
            "growth_state": "planktonic",
            "antibiotic": "Ceftazidime",
            "mdr_relevant": 0,
            "xdr_relevant": 0,
            "phage_active": 1,
            "antibiotic_active": 1,
            "direct_isolate_match": 1,
            "species_match": 1,
            "synergy_score": 80,
            "mic_fold_reduction": 8,
            "log_reduction": 2,
            "evidence_level": 4,
            "quality_score": 4,
            "n_strains_tested": 10,
            "phage_cocktail_size": 1,
            "host_range_score": 5,
            "toxicity_signal": 0,
            "interpretation_id": 1,
            "record_status": "validated"
        })
        
        score_soft = core.score_row(row_sensitive, patient)
        
        # Now test with resistant antibiotic in soft mode
        row_resistant = row_sensitive.copy()
        row_resistant["antibiotic"] = "Ciprofloxacin"
        
        score_res_soft = core.score_row(row_resistant, patient)
        
        # Score should be lower for resistant ATB even in soft mode
        self.assertTrue(score_res_soft < score_soft)

if __name__ == "__main__":
    unittest.main()
