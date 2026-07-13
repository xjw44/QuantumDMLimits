import pandas as pd

sigma_e_summary = {
    "SuperCDMS CPD 2021": {
        "baseline_sigma_e_obs": 3.86, # ev
        "nr_dm_mass_th_spin_ind_obs": 93*1e6, # MeV
        "sensor": "TES", # MeV
        "url": "https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.127.061801",
    },
    "CRESST 2024": {
        "baseline_sigma_e_obs": 1.0, # ev
        "nr_dm_mass_th_spin_ind_obs": 73*1e6, # MeV
        "sensor": "TES", # MeV
        "url": "https://arxiv.org/pdf/2405.06527",
    },
    "TESSERACT 2025": {
        "baseline_sigma_e_obs": 361.5*1e-3, # ev
        "nr_dm_mass_th_spin_ind_obs": 44*1e6, # MeV
        "sensor": "TES", # MeV
        "url": "https://arxiv.org/pdf/2503.03683",
    },
    "KIPM 2024": {
        "baseline_sigma_e_obs": 318, # ev
        "baseline_sigma_e_abs_obs": 2.1, # ev
        "total_eff": 0.007, # ev
        "nr_dm_mass_th_spin_ind_exp": False, # MeV
        "sensor": "MKID", # MeV
        "url": "https://journals.aps.org/prapplied/pdf/10.1103/PhysRevApplied.22.044045",
    },
    "BULLKID 2024": {
        "baseline_sigma_e_obs": 27, # ev
        "nr_dm_mass_th_spin_ind_exp": False, # MeV
        "sensor": "MKID", # MeV
        "url": "https://link.springer.com/article/10.1140/epjc/s10052-024-12714-9",
    },
    "PAA-KIPM 2027": {
        "baseline_sigma_e_exp": 10*1e-3, # ev
        "baseline_sigma_e_abs_exp": 6*1e-3, # ev
        "total_eff": 0.6, # ev
        "nr_dm_mass_th_spin_ind_exp": False, # MeV
        "sensor": "MKID", # MeV
    },
    "QUBIT 2027": {
        "baseline_sigma_e_exp": 1*1e-3, # ev
        # "baseline_sigma_e_abs_/exp": 6*1e-3, # ev
        # "total_eff": 0.6, # ev
        "nr_dm_mass_th_spin_ind_exp": False, # MeV
        "sensor": "QUBIT", # MeV
    },
}

def dm_mass_threshold_ev(sigma_e_dep_ev: float) -> float:
    """
    Estimate dark matter mass threshold in eV,
    given deposited energy resolution in eV.

    Formula:
        m_chi [eV] ≈ sigma_Edep [eV] * (1e6 eV / 0.010 eV)
    """
    return sigma_e_dep_ev * (1e6 / 0.010)

def update_exp_threshold(data, exp_name):
    """Update the 'nr_dm_mass_th_spin_ind_exp' field for an experiment."""
    if "baseline_sigma_e_obs" in data[exp_name]: 
        data[exp_name]["nr_dm_mass_th_spin_ind_exp"] = \
        dm_mass_threshold_ev(data[exp_name]["baseline_sigma_e_obs"])
    else:
        data[exp_name]["nr_dm_mass_th_spin_ind_exp"] = \
        dm_mass_threshold_ev(data[exp_name]["baseline_sigma_e_exp"])

# Example usage:
update_exp_threshold(sigma_e_summary, "KIPM 2024")  # set to 5 MeV
update_exp_threshold(sigma_e_summary, "BULLKID 2024")  # set to 5 MeV
update_exp_threshold(sigma_e_summary, "PAA-KIPM 2027")  # set to 5 MeV
update_exp_threshold(sigma_e_summary, "QUBIT 2027")  # set to 5 MeV

def convert_sigma_e_df(sigma_e_summary=sigma_e_summary):
    # --- Flatten dictionary into a DataFrame
    rows = []
    for exp, vals in sigma_e_summary.items():
        row = {"Experiment": exp}
        for k, v in vals.items():
            row[k] = v
        rows.append(row)

    df = pd.DataFrame(rows).set_index("Experiment")
    return df 
