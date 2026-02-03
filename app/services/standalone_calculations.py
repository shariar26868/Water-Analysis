"""
Standalone Water Quality Calculations
All mathematical formulas provided by client
NO PHREEQC dependency - pure Python math
"""

import logging
import math
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class StandaloneCalculations:
    """All standalone water quality calculations"""
    
    # ========================================
    # LARSON-SKOLD CORROSION INDEX
    # ========================================
    
    @staticmethod
    def calculate_larson_skold(
        chloride_mg_l: float,
        sulfate_mg_l: float,
        bicarbonate_mg_l: float,
        carbonate_mg_l: float = 0.0
    ) -> Dict[str, Any]:
        """
        Larson-Skold Corrosion Index
        
        Formula: ([Cl-] + [SO4²-]) / ([HCO3-] + [CO3²-])
        Where all values are in meq/L
        
        Args:
            chloride_mg_l: Chloride in mg/L
            sulfate_mg_l: Sulfate in mg/L
            bicarbonate_mg_l: Bicarbonate in mg/L
            carbonate_mg_l: Carbonate in mg/L (optional)
        
        Returns:
            {
                "larson_skold_index": float,
                "risk_level": str,
                "interpretation": str
            }
        """
        try:
            # Convert mg/L to meq/L
            # Cl-: 1 meq/mole, MW=35.45
            cl_meq = chloride_mg_l / 35.45
            
            # SO4²-: 2 meq/mole, MW=96.06
            so4_meq = (sulfate_mg_l / 96.06) * 2
            
            # HCO3-: 1 meq/mole, MW=61.02
            hco3_meq = bicarbonate_mg_l / 61.02
            
            # CO3²-: 2 meq/mole, MW=60.01
            co3_meq = (carbonate_mg_l / 60.01) * 2
            
            # Calculate index
            numerator = cl_meq + so4_meq
            denominator = hco3_meq + co3_meq
            
            if denominator == 0:
                logger.warning("⚠️ Larson-Skold: Zero alkalinity - cannot calculate")
                return {
                    "larson_skold_index": None,
                    "risk_level": "Unknown",
                    "interpretation": "Cannot calculate - zero alkalinity"
                }
            
            ls_index = numerator / denominator
            
            # Determine risk level
            if ls_index < 0.8:
                risk_level = "Low Risk"
                interpretation = "Low corrosion risk"
            elif ls_index <= 1.2:
                risk_level = "Moderate Risk"
                interpretation = "Moderate corrosion risk - monitor system"
            else:
                risk_level = "High Risk"
                interpretation = "High corrosion risk - treatment recommended"
            
            logger.info(f"✅ Larson-Skold Index: {ls_index:.3f} ({risk_level})")
            
            return {
                "larson_skold_index": round(ls_index, 3),
                "risk_level": risk_level,
                "interpretation": interpretation
            }
            
        except Exception as e:
            logger.error(f"❌ Larson-Skold calculation failed: {e}")
            raise
    
    # ========================================
    # STIFF & DAVIS INDEX
    # ========================================
    
    @staticmethod
    def calculate_stiff_davis(
        ph: float,
        calcium_mg_l: float,
        alkalinity_mg_l: float,  # as CaCO3
        temperature_c: float,
        tds_mg_l: float
    ) -> Dict[str, Any]:
        """
        Stiff & Davis Stability Index
        
        Formula: S&D = pH - pCa - pAlk - K
        
        Where:
        - pCa = -log10[Ca²+] in moles/kg
        - pAlk = -log10[Alkalinity as HCO3-] in moles/kg
        - K = temperature/salinity coefficient
        
        Returns:
            {
                "stiff_davis_index": float,
                "interpretation": str,
                "scale_tendency": str
            }
        """
        try:
            # Calculate pCa (Ca²+ in moles/kg)
            # MW of Ca = 40.08
            ca_mol_kg = (calcium_mg_l / 1000) / 40.08
            p_ca = -math.log10(ca_mol_kg) if ca_mol_kg > 0 else 0
            
            # Calculate pAlk (Alkalinity as HCO3- in moles/kg)
            # Convert CaCO3 to HCO3-: 1 mg/L CaCO3 = 1.22 mg/L HCO3-
            # MW of HCO3- = 61.02
            hco3_mg_l = alkalinity_mg_l * 1.22
            alk_mol_kg = (hco3_mg_l / 1000) / 61.02
            p_alk = -math.log10(alk_mol_kg) if alk_mol_kg > 0 else 0
            
            # Calculate K coefficient
            ionic_strength = tds_mg_l / 1000
            
            if ionic_strength <= 1.2:
                # K = 2.022 × e^(1.737 × I) - 0.315 × T^0.3
                k = 2.022 * math.exp(1.737 * ionic_strength) - 0.315 * (temperature_c ** 0.3)
            else:
                # K = 1.7 × e^(2.1 × I) - 0.5 × T^0.4
                k = 1.7 * math.exp(2.1 * ionic_strength) - 0.5 * (temperature_c ** 0.4)
            
            # Calculate S&D Index
            sd_index = ph - p_ca - p_alk - k
            
            # Interpretation
            if sd_index > 0:
                tendency = "Supersaturated"
                interpretation = "Risk of CaCO3 scale formation"
            elif sd_index == 0:
                tendency = "Equilibrium"
                interpretation = "Balanced - no scale or corrosion tendency"
            else:
                tendency = "Undersaturated"
                interpretation = "No risk of CaCO3 scale - may be corrosive"
            
            logger.info(f"✅ Stiff & Davis Index: {sd_index:.3f} ({tendency})")
            
            return {
                "stiff_davis_index": round(sd_index, 3),
                "interpretation": interpretation,
                "scale_tendency": tendency,
                "components": {
                    "pH": round(ph, 2),
                    "pCa": round(p_ca, 3),
                    "pAlk": round(p_alk, 3),
                    "K": round(k, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Stiff & Davis calculation failed: {e}")
            raise
    
    # ========================================
    # LANGELIER SATURATION INDEX (LSI)
    # ========================================
    
    @staticmethod
    def calculate_lsi(
        ph: float,
        temperature_c: float,
        calcium_mg_l: float,  # as CaCO3
        alkalinity_mg_l: float,  # as CaCO3
        tds_mg_l: float
    ) -> Dict[str, Any]:
        """
        Langelier Saturation Index
        
        Formula: LSI = pH(actual) - pH(s)
        
        Where pH(s) = (9.3 + A + B) - (C + D)
        
        Returns:
            {
                "lsi": float,
                "ph_actual": float,
                "ph_saturated": float,
                "interpretation": str
            }
        """
        try:
            # Calculate A: (log10(TDS) - 1) / 10
            a = (math.log10(tds_mg_l) - 1) / 10 if tds_mg_l > 0 else 0
            
            # Calculate B: -13.12 × log10(T°C + 273) + 34.55
            b = -13.12 * math.log10(temperature_c + 273) + 34.55
            
            # Calculate C: log10(Ca as CaCO3) - 0.4
            c = math.log10(calcium_mg_l) - 0.4 if calcium_mg_l > 0 else 0
            
            # Calculate D: log10(M-Alkalinity as CaCO3)
            d = math.log10(alkalinity_mg_l) if alkalinity_mg_l > 0 else 0
            
            # Calculate pH(s)
            ph_s = (9.3 + a + b) - (c + d)
            
            # Calculate LSI
            lsi = ph - ph_s
            
            # Interpretation
            if lsi > 0.5:
                tendency = "Scaling"
                interpretation = "Water is supersaturated - scale formation likely"
            elif lsi >= -0.5:
                tendency = "Balanced"
                interpretation = "Water is near equilibrium - slight scale or corrosion"
            else:
                tendency = "Corrosive"
                interpretation = "Water is undersaturated - corrosive tendency"
            
            logger.info(f"✅ LSI: {lsi:.2f} ({tendency})")
            
            return {
                "lsi": round(lsi, 2),
                "ph_actual": round(ph, 2),
                "ph_saturated": round(ph_s, 2),
                "interpretation": interpretation,
                "tendency": tendency
            }
            
        except Exception as e:
            logger.error(f"❌ LSI calculation failed: {e}")
            raise
    
    # ========================================
    # RYZNAR STABILITY INDEX
    # ========================================
    
    @staticmethod
    def calculate_ryznar(
        ph: float,
        temperature_c: float,
        calcium_mg_l: float,
        alkalinity_mg_l: float,
        tds_mg_l: float
    ) -> Dict[str, Any]:
        """
        Ryznar Stability Index
        
        Formula: RI = 2 × pH(s) - pH(actual)
        
        Uses same pH(s) as LSI
        
        Returns:
            {
                "ryznar_index": float,
                "interpretation": str,
                "tendency": str
            }
        """
        try:
            # Calculate pH(s) using LSI method
            lsi_result = StandaloneCalculations.calculate_lsi(
                ph, temperature_c, calcium_mg_l, alkalinity_mg_l, tds_mg_l
            )
            
            ph_s = lsi_result["ph_saturated"]
            
            # Calculate Ryznar Index
            ri = 2 * ph_s - ph
            
            # Interpretation
            if ri < 5.5:
                tendency = "Heavy Scaling"
                interpretation = "Severe scale formation expected"
            elif ri < 6.2:
                tendency = "Light Scaling"
                interpretation = "Slight scale formation possible"
            elif ri <= 7.0:
                tendency = "Balanced"
                interpretation = "Near equilibrium - acceptable range"
            elif ri <= 7.5:
                tendency = "Slight Corrosion"
                interpretation = "Slightly corrosive"
            else:
                tendency = "Heavy Corrosion"
                interpretation = "Severe corrosion expected"
            
            logger.info(f"✅ Ryznar Index: {ri:.2f} ({tendency})")
            
            return {
                "ryznar_index": round(ri, 2),
                "interpretation": interpretation,
                "tendency": tendency
            }
            
        except Exception as e:
            logger.error(f"❌ Ryznar Index calculation failed: {e}")
            raise
    
    # ========================================
    # PUCKORIUS SCALING INDEX
    # ========================================
    
    @staticmethod
    def calculate_puckorius(
        temperature_c: float,
        calcium_mg_l: float,  # as CaCO3
        alkalinity_mg_l: float,  # as CaCO3
        tds_mg_l: float
    ) -> Dict[str, Any]:
        """
        Puckorius (Practical) Scaling Index
        
        Formula: PSI = 2 × pHs - pHeq
        
        Where:
        - pHs = (9.3 + A + B) - (C + D)
        - pHeq = 1.465 × log10(M-Alkalinity) + 4.54
        
        Returns:
            {
                "puckorius_index": float,
                "interpretation": str
            }
        """
        try:
            # Calculate A
            a = (math.log10(tds_mg_l) - 1) / 10 if tds_mg_l > 0 else 0
            
            # Calculate B
            b = -13.12 * math.log10(temperature_c + 273) + 34.55
            
            # Calculate C
            c = math.log10(calcium_mg_l) - 0.4 if calcium_mg_l > 0 else 0
            
            # Calculate D
            d = math.log10(alkalinity_mg_l) if alkalinity_mg_l > 0 else 0
            
            # Calculate pHs
            ph_s = (9.3 + a + b) - (c + d)
            
            # Calculate pHeq
            ph_eq = 1.465 * math.log10(alkalinity_mg_l) + 4.54 if alkalinity_mg_l > 0 else 0
            
            # Calculate PSI
            psi = 2 * ph_s - ph_eq
            
            # Interpretation
            if psi < 4.5:
                tendency = "Scaling"
                interpretation = "Scale formation likely"
            elif psi <= 6.5:
                tendency = "Optimal (Balanced)"
                interpretation = "Water is balanced - optimal range"
            else:
                tendency = "Corrosive"
                interpretation = "Corrosive tendency"
            
            logger.info(f"✅ Puckorius Index: {psi:.2f} ({tendency})")
            
            return {
                "puckorius_index": round(psi, 2),
                "interpretation": interpretation,
                "tendency": tendency
            }
            
        except Exception as e:
            logger.error(f"❌ Puckorius calculation failed: {e}")
            raise
    
    # ========================================
    # MILD STEEL CORROSION RATE ESTIMATION
    # ========================================
    
    @staticmethod
    def estimate_mild_steel_corrosion(
        ph: float,
        dissolved_oxygen_ppm: float,
        temperature_c: float,
        si_caco3: float,
        pma_ppm: float = 0.0,
        si_alsi: float = -999,
        si_snsi: float = -999,
        si_tcp: float = -999,
        si_zp: float = -999
    ) -> Dict[str, Any]:
        """
        Estimated Mild Steel Corrosion Rate
        
        Base Rate:
        CR_base = 0.1 × 10^(7.5-pH) × (DO/5) × 1.15^((T-25)/10) × f(SI_CC)
        
        Final Rate with inhibitors:
        CR_final = CR_base × (1 - total_inhibition)
        
        Returns:
            {
                "base_corrosion_rate_mpy": float,
                "final_corrosion_rate_mpy": float,
                "inhibition_percent": float,
                "interpretation": str
            }
        """
        try:
            # Base corrosion rate
            ph_factor = 10 ** (7.5 - ph)
            do_factor = dissolved_oxygen_ppm / 5.0
            temp_factor = 1.15 ** ((temperature_c - 25) / 10)
            
            # f(SI_CC) - CaCO3 protection
            if si_caco3 > 0.5:
                f_sicc = 0.7
            elif si_caco3 >= 0:
                f_sicc = 0.9
            else:
                f_sicc = 1.3
            
            cr_base = 0.1 * ph_factor * do_factor * temp_factor * f_sicc
            
            # Calculate inhibition factors
            inhibition_total = 0.0
            
            # PMA inhibition
            if pma_ppm >= 25:
                i_pma = 1.0
            elif pma_ppm >= 20:
                i_pma = 0.95
            elif pma_ppm >= 17:
                i_pma = 0.8
            elif pma_ppm >= 15:
                i_pma = 0.3
            else:
                i_pma = 0.0
            
            inhibition_total += 0.45 * i_pma
            
            # AlSi inhibition
            j_alsi = 1.0 if si_alsi > 0 else 0.0
            inhibition_total += 0.30 * j_alsi
            
            # SnSi inhibition
            k_snsi = 1.0 if si_snsi > 0 else 0.0
            inhibition_total += 0.28 * k_snsi
            
            # TCP inhibition
            if si_tcp > 0.2:
                g_tcp = 1.0
            elif si_tcp >= 0:
                g_tcp = 0.6
            else:
                g_tcp = 0.0
            inhibition_total += 0.35 * g_tcp
            
            # ZP inhibition
            if si_zp > 0.1:
                h_zp = 1.0
            elif si_zp >= 0:
                h_zp = 0.5
            else:
                h_zp = 0.0
            inhibition_total += 0.25 * h_zp
            
            # Cap inhibition at 90%
            inhibition_total = min(inhibition_total, 0.90)
            
            # Final corrosion rate
            cr_final = cr_base * (1 - inhibition_total)
            
            # Interpretation
            if cr_final < 2:
                rating = "Excellent"
            elif cr_final < 5:
                rating = "Good"
            elif cr_final < 10:
                rating = "Acceptable"
            elif cr_final < 20:
                rating = "Poor"
            else:
                rating = "Severe"
            
            logger.info(f"✅ Mild Steel Corrosion: {cr_final:.2f} mpy ({rating})")
            
            return {
                "base_corrosion_rate_mpy": round(cr_base, 2),
                "final_corrosion_rate_mpy": round(cr_final, 2),
                "inhibition_percent": round(inhibition_total * 100, 1),
                "interpretation": f"{rating} corrosion rate",
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"❌ Mild steel corrosion calculation failed: {e}")
            raise
    
    # ========================================
    # COPPER CORROSION RATE ESTIMATION
    # ========================================
    
    @staticmethod
    def estimate_copper_corrosion(
        ph: float,
        dissolved_oxygen_ppm: float,
        temperature_c: float,
        si_caco3: float,
        chloride_ppm: float,
        free_chlorine_ppm: float,
        total_chlorine_ppm: float,
        tta_ppm: float = 0.0,
        bta_ppm: float = 0.0,
        mbt_ppm: float = 0.0,
        copper_free_ppm: float = 0.0
    ) -> Dict[str, Any]:
        """
        Estimated Copper Corrosion Rate
        
        Base Rate:
        CR_base,Cu = 0.05 × 10^(7.5-pH) × (DO/5) × 1.15^((T-25)/10) × f(SI_CC) × m(Cl⁻) × p(Cl2_free) × q(Cl2_total)
        
        Final Rate with azoles:
        CR_Cu = CR_base × (1 - azole_inhibition)
        
        Returns:
            {
                "base_corrosion_rate_mpy": float,
                "final_corrosion_rate_mpy": float,
                "inhibition_percent": float,
                "interpretation": str
            }
        """
        try:
            # Base corrosion rate
            ph_factor = 10 ** (7.5 - ph)
            do_factor = dissolved_oxygen_ppm / 5.0
            temp_factor = 1.15 ** ((temperature_c - 25) / 10)
            
            # f(SI_CC)
            if si_caco3 > 0.4:
                f_sicc = 0.8
            elif si_caco3 >= 0:
                f_sicc = 0.95
            else:
                f_sicc = 1.4
            
            # m(Cl-)
            if chloride_ppm < 50:
                m_cl = 1.0
            elif chloride_ppm <= 200:
                m_cl = 1.2
            else:
                m_cl = 1.8
            
            # p(Cl2_free)
            if free_chlorine_ppm < 0.2:
                p_cl2_free = 1.0
            elif free_chlorine_ppm <= 0.5:
                p_cl2_free = 1.5
            else:
                p_cl2_free = 2.5
            
            # q(Cl2_total)
            if total_chlorine_ppm < 1.0:
                q_cl2_total = 1.0
            elif total_chlorine_ppm <= 2.0:
                q_cl2_total = 1.2
            else:
                q_cl2_total = 1.6
            
            cr_base = 0.05 * ph_factor * do_factor * temp_factor * f_sicc * m_cl * p_cl2_free * q_cl2_total
            
            # Chlorine-Azole deactivation d(Cl2)
            if free_chlorine_ppm < 0.1:
                r_free = 0.0
            elif free_chlorine_ppm <= 0.3:
                r_free = 0.4
            elif free_chlorine_ppm <= 0.5:
                r_free = 0.7
            else:
                r_free = 0.9
            
            if total_chlorine_ppm < 0.5:
                s_total = 0.0
            elif total_chlorine_ppm <= 1.5:
                s_total = 0.2
            else:
                s_total = 0.4
            
            d_cl2 = (1 - 0.8 * r_free) * (1 - 0.3 * s_total)
            
            # Azole:Copper ratio e(ratio)
            def get_e_ratio(azole_ppm, cu_free_ppm):
                if cu_free_ppm == 0:
                    return 1.0
                ratio = azole_ppm / cu_free_ppm
                if ratio >= 5:
                    return 1.0
                elif ratio >= 3:
                    return 0.7
                elif ratio >= 1:
                    return 0.4
                else:
                    return 0.2
            
            # TTA inhibition
            if tta_ppm >= 2:
                a_tta = 1.0
            elif tta_ppm >= 1:
                a_tta = 0.8
            else:
                a_tta = 0.3
            
            e_tta = get_e_ratio(tta_ppm, copper_free_ppm)
            tta_inhibition = 0.65 * a_tta * d_cl2 * e_tta
            
            # BTA inhibition
            if bta_ppm >= 3:
                b_bta = 1.0
            elif bta_ppm >= 1.5:
                b_bta = 0.7
            else:
                b_bta = 0.2
            
            e_bta = get_e_ratio(bta_ppm, copper_free_ppm)
            bta_inhibition = 0.55 * b_bta * d_cl2 * e_bta
            
            # MBT inhibition (not affected by chlorine)
            if mbt_ppm >= 2.5:
                c_mbt = 1.0
            elif mbt_ppm >= 1:
                c_mbt = 0.75
            else:
                c_mbt = 0.25
            
            e_mbt = get_e_ratio(mbt_ppm, copper_free_ppm)
            mbt_inhibition = 0.60 * c_mbt * e_mbt
            
            # Total inhibition (cap at 90%)
            total_inhibition = min(tta_inhibition + bta_inhibition + mbt_inhibition, 0.90)
            
            # Final corrosion rate
            cr_final = cr_base * (1 - total_inhibition)
            
            # Interpretation
            if cr_final < 0.2:
                rating = "Excellent"
            elif cr_final < 0.5:
                rating = "Good"
            elif cr_final < 1.0:
                rating = "Acceptable"
            elif cr_final < 2.0:
                rating = "Poor"
            else:
                rating = "Severe"
            
            logger.info(f"✅ Copper Corrosion: {cr_final:.2f} mpy ({rating})")
            
            return {
                "base_corrosion_rate_mpy": round(cr_base, 2),
                "final_corrosion_rate_mpy": round(cr_final, 2),
                "inhibition_percent": round(total_inhibition * 100, 1),
                "interpretation": f"{rating} corrosion rate",
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"❌ Copper corrosion calculation failed: {e}")
            raise
    
    # ========================================
    # ADMIRALTY BRASS CORROSION RATE
    # ========================================
    
    @staticmethod
    def estimate_admiralty_brass_corrosion(
        ph: float,
        dissolved_oxygen_ppm: float,
        temperature_c: float,
        si_caco3: float,
        chloride_ppm: float,
        ammonia_ppm: float,
        free_chlorine_ppm: float,
        total_chlorine_ppm: float,
        tta_ppm: float = 0.0,
        bta_ppm: float = 0.0,
        mbt_ppm: float = 0.0,
        copper_free_ppm: float = 0.0
    ) -> Dict[str, Any]:
        """
        Estimated Admiralty Brass Corrosion Rate
        
        Similar to copper but with ammonia factor n(NH3)
        
        Returns:
            {
                "base_corrosion_rate_mpy": float,
                "final_corrosion_rate_mpy": float,
                "inhibition_percent": float,
                "interpretation": str
            }
        """
        try:
            # Base corrosion rate
            ph_factor = 10 ** (7.8 - ph)
            do_factor = dissolved_oxygen_ppm / 5.0
            temp_factor = 1.12 ** ((temperature_c - 25) / 10)
            
            # f(SI_CC)
            if si_caco3 > 0.4:
                f_sicc = 0.75
            elif si_caco3 >= 0:
                f_sicc = 0.92
            else:
                f_sicc = 1.5
            
            # m(Cl-)
            if chloride_ppm < 50:
                m_cl = 1.0
            elif chloride_ppm <= 200:
                m_cl = 1.4
            else:
                m_cl = 2.2
            
            # n(NH3) - ammonia factor
            if ammonia_ppm < 0.5:
                n_nh3 = 1.0
            elif ammonia_ppm <= 2.0:
                n_nh3 = 1.5
            else:
                n_nh3 = 3.0
            
            # p(Cl2_free)
            if free_chlorine_ppm < 0.2:
                p_cl2_free = 1.0
            elif free_chlorine_ppm <= 0.5:
                p_cl2_free = 1.5
            else:
                p_cl2_free = 2.5
            
            # q(Cl2_total)
            if total_chlorine_ppm < 1.0:
                q_cl2_total = 1.0
            elif total_chlorine_ppm <= 2.0:
                q_cl2_total = 1.2
            else:
                q_cl2_total = 1.6
            
            cr_base = 0.08 * ph_factor * do_factor * temp_factor * f_sicc * m_cl * n_nh3 * p_cl2_free * q_cl2_total
            
            # Chlorine-Azole deactivation (same as copper)
            if free_chlorine_ppm < 0.1:
                r_free = 0.0
            elif free_chlorine_ppm <= 0.3:
                r_free = 0.4
            elif free_chlorine_ppm <= 0.5:
                r_free = 0.7
            else:
                r_free = 0.9
            
            if total_chlorine_ppm < 0.5:
                s_total = 0.0
            elif total_chlorine_ppm <= 1.5:
                s_total = 0.2
            else:
                s_total = 0.4
            
            d_cl2 = (1 - 0.8 * r_free) * (1 - 0.3 * s_total)
            
            # Azole:Copper ratio
            def get_e_ratio(azole_ppm, cu_free_ppm):
                if cu_free_ppm == 0:
                    return 1.0
                ratio = azole_ppm / cu_free_ppm
                if ratio >= 5:
                    return 1.0
                elif ratio >= 3:
                    return 0.7
                elif ratio >= 1:
                    return 0.4
                else:
                    return 0.2
            
            # TTA inhibition (higher effectiveness on brass)
            if tta_ppm >= 2:
                a_tta = 1.0
            elif tta_ppm >= 1:
                a_tta = 0.85
            else:
                a_tta = 0.35
            
            e_tta = get_e_ratio(tta_ppm, copper_free_ppm)
            tta_inhibition = 0.70 * a_tta * d_cl2 * e_tta
            
            # BTA inhibition
            if bta_ppm >= 3:
                b_bta = 1.0
            elif bta_ppm >= 1.5:
                b_bta = 0.75
            else:
                b_bta = 0.25
            
            e_bta = get_e_ratio(bta_ppm, copper_free_ppm)
            bta_inhibition = 0.60 * b_bta * d_cl2 * e_bta
            
            # MBT inhibition
            if mbt_ppm >= 2.5:
                c_mbt = 1.0
            elif mbt_ppm >= 1:
                c_mbt = 0.80
            else:
                c_mbt = 0.30
            
            e_mbt = get_e_ratio(mbt_ppm, copper_free_ppm)
            mbt_inhibition = 0.65 * c_mbt * e_mbt
            
            # Total inhibition (cap at 90%)
            total_inhibition = min(tta_inhibition + bta_inhibition + mbt_inhibition, 0.90)
            
            # Final corrosion rate
            cr_final = cr_base * (1 - total_inhibition)
            
            # Interpretation
            if cr_final < 0.2:
                rating = "Excellent"
            elif cr_final < 0.5:
                rating = "Good"
            elif cr_final < 1.0:
                rating = "Acceptable"
            elif cr_final < 2.0:
                rating = "Poor"
            else:
                rating = "Severe"
            
            logger.info(f"✅ Admiralty Brass Corrosion: {cr_final:.2f} mpy ({rating})")
            
            return {
                "base_corrosion_rate_mpy": round(cr_base, 2),
                "final_corrosion_rate_mpy": round(cr_final, 2),
                "inhibition_percent": round(total_inhibition * 100, 1),
                "interpretation": f"{rating} corrosion rate",
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"❌ Admiralty brass corrosion calculation failed: {e}")
            raise