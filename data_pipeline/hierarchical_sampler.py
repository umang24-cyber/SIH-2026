import pandas as pd
import numpy as np

class HierarchicalSampler:
    """
    Standalone V7 Hierarchical Sampler for behavioral profile generation.
    Combines BitcoinHeist (Macro) and ORBITAAL (Micro) profiles conditionally.
    """
    def __init__(self, macro_profiles: pd.DataFrame, micro_profiles: pd.DataFrame, random_state: int = 42):
        self.rng = np.random.RandomState(random_state)
        
        # MACRO (BitcoinHeist)
        # Ensure required macro columns
        req_macro = ['lifespan_days', 'active_days', 'total_count', 'total_income', 'label']
        for c in req_macro:
            if c not in macro_profiles.columns:
                raise ValueError(f"Missing required macro column: {c}")
                
        self.macro = macro_profiles.copy()
        
        # MICRO (ORBITAAL)
        # Ensure required micro columns
        req_micro = ['activity_count', 'mean_transfer_amount', 'inter_event_delta_mean', 'burstiness_B']
        for c in req_micro:
            if c not in micro_profiles.columns:
                raise ValueError(f"Missing required micro column: {c}")
                
        self.micro = micro_profiles.copy()
        
        # Precompute buckets for conditional sampling
        self._fit_macro_buckets()
        self._fit_micro_buckets()
        
    def _fit_macro_buckets(self):
        # We bucket macro behavior primarily by lifespan and total_count
        self.bg_macro = self.macro[self.macro['label'] == 'white'].copy()
        self.rw_macro = self.macro[self.macro['label'] != 'white'].copy()
        
        # PHASE 2 AMENDMENT: Calculate GLOBAL quantiles to ensure common bucket boundaries
        self.global_l_q = self.macro['lifespan_days'].quantile([0.25, 0.5, 0.75]).to_dict()
        self.global_c_q = self.macro['total_count'].quantile([0.25, 0.5, 0.75]).to_dict()
        
        def assign_buckets(df):
            l_v = df['lifespan_days'].values
            c_v = df['total_count'].values
            l_b = np.where(l_v <= self.global_l_q[0.25], '0',
                  np.where(l_v <= self.global_l_q[0.5], '1',
                  np.where(l_v <= self.global_l_q[0.75], '2', '3')))
            c_b = np.where(c_v <= self.global_c_q[0.25], '0',
                  np.where(c_v <= self.global_c_q[0.5], '1',
                  np.where(c_v <= self.global_c_q[0.75], '2', '3')))
            # Need to create series of strings
            return pd.Series(l_b, index=df.index) + "_" + pd.Series(c_b, index=df.index)

        self.bg_macro['bucket'] = assign_buckets(self.bg_macro)
        self.bg_bucket_indices = self.bg_macro.groupby('bucket').indices
        
        def add_approx_year(df):
            if 'year' in df.columns:
                return df['year']
            elif 'first_day' in df.columns:
                return 2011 + (df['first_day'] // 365.25).astype(int)
            return 2014

        self.bg_macro['approx_year'] = add_approx_year(self.bg_macro)
        self.bg_bucket_year_indices = self.bg_macro.groupby(['bucket', 'approx_year']).indices
        
        if len(self.rw_macro) > 0:
            self.rw_macro['bucket'] = assign_buckets(self.rw_macro)
            self.rw_bucket_indices = self.rw_macro.groupby('bucket').indices
            
            # Identify bucket distribution of ransomware to force background to match it
            self.rw_bucket_dist = self.rw_macro['bucket'].value_counts(normalize=True).to_dict()
            
            # Family handling: identify tiny families (< 100 samples)
            fam_counts = self.rw_macro['label'].value_counts()
            self.tiny_families = fam_counts[fam_counts < 100].index.tolist()
            
    def _fit_micro_buckets(self):
        # We bucket micro behavior by activity_count (regime)
        self.m_c_q = self.micro['activity_count'].quantile([0.25, 0.5, 0.75]).to_dict()
        
        # Vectorized micro bucket assignment
        m_v = self.micro['activity_count'].values
        m_b = np.where(m_v <= self.m_c_q[0.25], 0,
              np.where(m_v <= self.m_c_q[0.5], 1,
              np.where(m_v <= self.m_c_q[0.75], 2, 3)))
        self.micro['activity_regime'] = m_b
        
        self.micro_bucket_indices = self.micro.groupby('activity_regime').indices
        
    def _get_1d_bucket(self, val, q_dict):
        if val <= q_dict[0.25]: return 0
        elif val <= q_dict[0.5]: return 1
        elif val <= q_dict[0.75]: return 2
        else: return 3
        
    def _get_bucket(self, l_val, c_val, l_q, c_q):
        b_l = self._get_1d_bucket(l_val, l_q)
        b_c = self._get_1d_bucket(c_val, c_q)
        return f"{b_l}_{b_c}"

    def sample(self, scenario_type="background", family=None, target_year=None):
        """
        Returns a behavioral profile dict.
        """
        # STEP 1: Macro Sampling
        if scenario_type in ["peeling_chain", "layering", "mixing", "background", "normal"]:
            # These use background behavioral prior
            pop = self.bg_macro
            
            # PHASE 3: Era Matching - restrict background to target year if specified
            if target_year is not None:
                if 'year' in pop.columns:
                    yr_pop = pop[pop['year'] == target_year]
                elif 'first_day' in pop.columns:
                    # Estimate year from first_day
                    approx_year = 2011 + (pop['first_day'] // 365.25).astype(int)
                    yr_pop = pop[approx_year == target_year]
                else:
                    yr_pop = pd.DataFrame()
                    
                if len(yr_pop) > 0:
                    pop = yr_pop
            
            # PHASE 2: Macro Regime Overlap - force background to use ransomware's bucket distribution
            if len(self.rw_macro) > 0:
                buckets = list(self.rw_bucket_dist.keys())
                probs = list(self.rw_bucket_dist.values())
                bucket = self.rng.choice(buckets, p=probs)
            else:
                # Fallback if no rw data (shouldn't happen in full dataset)
                bucket = self._get_bucket(
                    pop['lifespan_days'].sample(1, random_state=self.rng).iloc[0],
                    pop['total_count'].sample(1, random_state=self.rng).iloc[0],
                    self.global_l_q, self.global_c_q
                )
                
        elif scenario_type == "ransomware":
            if family and family not in self.tiny_families and family in self.rw_macro['label'].unique():
                pop = self.rw_macro[self.rw_macro['label'] == family]
            else:
                # Fallback to broader ransomware pool
                pop = self.rw_macro
                family = "pooled_ransomware"
                
            bucket = self._get_bucket(
                pop['lifespan_days'].sample(1, random_state=self.rng).iloc[0],
                pop['total_count'].sample(1, random_state=self.rng).iloc[0],
                self.global_l_q, self.global_c_q
            )
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
            
        # Conditionally sample macro from the bucket if it exists in population, else fallback to full pop
        # Optimize by checking if we're using the full population vs a filtered subset
        full_pop_check = False
        lookup_key = bucket
        is_bg = True
        
        if scenario_type in ["peeling_chain", "layering", "mixing", "background", "normal"]:
            full_pop_check = True
            is_bg = True
            if target_year is not None:
                indices_dict = self.bg_bucket_year_indices
                lookup_key = (bucket, target_year)
            else:
                indices_dict = self.bg_bucket_indices
                lookup_key = bucket
        elif scenario_type == "ransomware" and family == "pooled_ransomware":
            full_pop_check = True
            indices_dict = self.rw_bucket_indices
            lookup_key = bucket
            is_bg = False
            
        if full_pop_check:
            if lookup_key in indices_dict and len(indices_dict[lookup_key]) > 0:
                idx = self.rng.choice(indices_dict[lookup_key])
                sampled_macro = self.bg_macro.iloc[idx] if is_bg else self.rw_macro.iloc[idx]
                actual_bucket = bucket
            else:
                fallback_idx = self.rng.choice(len(self.bg_macro)) if is_bg else self.rng.choice(len(self.rw_macro))
                sampled_macro = self.bg_macro.iloc[fallback_idx] if is_bg else self.rw_macro.iloc[fallback_idx]
                actual_bucket = "fallback"
        else:
            bucket_pop = pop[pop['bucket'] == bucket]
            if len(bucket_pop) > 0:
                sampled_macro = bucket_pop.sample(n=1, random_state=self.rng).iloc[0]
                actual_bucket = bucket
            else:
                sampled_macro = pop.sample(n=1, random_state=self.rng).iloc[0]
                actual_bucket = "fallback"
            
        # STEP 2: Determine Activity Regime (Macro -> Micro bridge)
        # We use total_count per day as the bridge activity metric to query ORBITAAL
        daily_count = sampled_macro['total_count'] / max(1, sampled_macro['active_days'])
        target_regime = self._get_1d_bucket(daily_count, self.m_c_q)
        
        # We sample a node from ORBITAAL that matches the chosen activity regime bucket
        if target_regime in self.micro_bucket_indices and len(self.micro_bucket_indices[target_regime]) > 0:
            idx = self.rng.choice(self.micro_bucket_indices[target_regime])
            sampled_micro = self.micro.iloc[idx]
        else:
            fallback_idx = self.rng.choice(len(self.micro))
            sampled_micro = self.micro.iloc[fallback_idx]
        
        # STEP 4: Build Reconciliation and output
        # E.g., we record the discrepancy between ORBITAAL mean_transfer and Heist mean_income
        reconciliation = {
            "macro_total_income_satoshis": float(sampled_macro['total_income']),
            "micro_mean_transfer_satoshis": float(sampled_micro['mean_transfer_amount']),
            "note": "Generator must dictate exact amounts based on typology template; statistical sampler does not force hard equation."
        }
        
        # Compute approximate year if missing
        if 'year' in sampled_macro:
            out_year = int(sampled_macro['year'])
        elif 'first_day' in sampled_macro:
            out_year = int(2011 + sampled_macro['first_day'] / 365.25)
        else:
            out_year = 2014 # default
            
        return {
            "profile_type": scenario_type,
            "family": family,
            "macro": {
                "lifespan_days": float(sampled_macro['lifespan_days']),
                "active_days": float(sampled_macro['active_days']),
                "total_count": float(sampled_macro['total_count']),
                "total_income": float(sampled_macro['total_income']),
                "year": out_year,
                "actual_bucket": actual_bucket
            },
            "micro": {
                "inter_event_delta_mean": float(sampled_micro['inter_event_delta_mean']),
                "burstiness_B": float(sampled_micro['burstiness_B']),
                "mean_transfer_amount": float(sampled_micro['mean_transfer_amount']),
                "activity_count_observed_day": float(sampled_micro['activity_count'])
            },
            "source": {
                "macro": "BitcoinHeist",
                "micro": "ORBITAAL"
            },
            "reconciliation_metadata": reconciliation,
            "approximations": [
                "BitcoinHeist is Address-Day aggregated.",
                "ORBITAAL is transfer-edge level.",
                "No UTXO boundaries available; generator must enforce Typology semantics."
            ]
        }
