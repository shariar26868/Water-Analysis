###########eta valo kaj koreee#############

# """
# Graph Service - 100% DYNAMIC VERSION
# ✅ NO hard-coded parameters
# ✅ AI determines status for unknown parameters
# ✅ Fallback to database first, then AI
# ✅ Production ready
# """

# import os
# import json
# import logging
# from typing import Dict, Any, Optional
# from datetime import datetime
# from io import BytesIO

# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
# import seaborn as sns
# import numpy as np
# from openai import AsyncOpenAI
# import boto3
# from botocore.exceptions import ClientError

# from app.db.mongo import db

# logger = logging.getLogger(__name__)


# class GraphService:
#     """Generate dynamic water quality graphs - 100% AI-powered"""
    
#     def __init__(self):
#         self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         self.s3_client = boto3.client(
#             's3',
#             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#             region_name=os.getenv("AWS_REGION")
#         )
#         self.bucket_name = os.getenv("AWS_S3_BUCKET")
        
#         # Set style
#         sns.set_style("whitegrid")
#         plt.rcParams['figure.dpi'] = 300
        
#         # ✅ Cache for AI-determined statuses (to avoid repeated API calls)
#         self._status_cache = {}
    
#     async def create_parameter_graph(
#         self, 
#         parameters: Dict[str, Any],
#         chemical_status: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """
#         Create parameter comparison bar graph
#         100% Dynamic - uses AI to determine colors
#         """
#         try:
#             logger.info("📊 Creating parameter comparison graph (AI-powered)")
            
#             # Get template
#             template = await db.get_graph_template("parameter_comparison_bar")
#             if not template:
#                 template = self._get_default_template()
            
#             # Extract numeric parameters
#             numeric_params = {}
#             for param_name, param_data in parameters.items():
#                 value = param_data.get("value")
#                 if isinstance(value, (int, float)):
#                     numeric_params[param_name] = value
            
#             if not numeric_params:
#                 raise Exception("No numeric parameters found")
            
#             # ✅ Determine status and color dynamically
#             logger.info(f"🤖 Evaluating {len(numeric_params)} parameters with AI...")
            
#             color_mapping = {}
#             status_mapping = {}
            
#             for param_name, value in numeric_params.items():
#                 status = await self._get_parameter_status_dynamic(param_name, value)
#                 color = self._get_color_for_status(status, template)
                
#                 color_mapping[param_name] = color
#                 status_mapping[param_name] = status
                
#                 logger.info(f"✅ {param_name} = {value} → {status} ({color})")
            
#             # Create graph
#             fig, ax = plt.subplots(figsize=tuple(template['default_config']['figsize']))
            
#             param_names = list(numeric_params.keys())
#             values = list(numeric_params.values())
#             colors = [color_mapping[name] for name in param_names]
            
#             # Create bars
#             bars = ax.bar(
#                 param_names, 
#                 values, 
#                 color=colors, 
#                 edgecolor='black', 
#                 linewidth=1.5, 
#                 alpha=0.85
#             )
            
#             # Add value labels
#             for bar, value in zip(bars, values):
#                 height = bar.get_height()
#                 ax.text(
#                     bar.get_x() + bar.get_width() / 2.,
#                     height,
#                     f'{value:.2f}',
#                     ha='center',
#                     va='bottom',
#                     fontsize=9,
#                     fontweight='bold'
#                 )
            
#             # Styling
#             ax.set_xlabel(
#                 template['default_config']['xlabel'],
#                 fontsize=12,
#                 fontweight='bold'
#             )
#             ax.set_ylabel(
#                 template['default_config']['ylabel'],
#                 fontsize=12,
#                 fontweight='bold'
#             )
#             ax.set_title(
#                 template['default_config']['title'],
#                 fontsize=14,
#                 fontweight='bold',
#                 pad=20
#             )
            
#             plt.xticks(rotation=template['default_config']['rotation'], ha='right', fontsize=10)
            
#             if template['default_config']['grid']:
#                 ax.grid(axis='y', alpha=0.3, linestyle='--')
            
#             plt.tight_layout()
            
#             # Save
#             buffer = BytesIO()
#             plt.savefig(buffer, format='png', dpi=template['default_config']['dpi'], bbox_inches='tight')
#             buffer.seek(0)
#             plt.close(fig)
            
#             # Upload to S3
#             graph_url = await self._upload_to_s3(buffer, "parameter_comparison")
            
#             logger.info(f"✅ Graph created: {graph_url}")
            
#             return {
#                 "graph_url": graph_url,
#                 "graph_type": "parameter_comparison_bar",
#                 "color_mapping": status_mapping,
#                 "created_at": datetime.utcnow()
#             }
            
#         except Exception as e:
#             logger.exception("❌ Graph creation failed")
#             raise Exception(f"Graph creation failed: {str(e)}")
    
#     async def modify_with_prompt(
#         self,
#         report_id: str,
#         parameters: Dict[str, Any],
#         prompt: str
#     ) -> Dict[str, Any]:
#         """
#         Modify graph colors using natural language prompt
#         """
#         try:
#             logger.info(f"🎨 Modifying graph with prompt: '{prompt}'")
            
#             # Parse intent
#             color_changes = await self._parse_color_intent(prompt, parameters.keys())
            
#             if not color_changes:
#                 logger.warning("⚠️ No color changes detected, using auto colors")
#             else:
#                 logger.info(f"✅ Color changes: {color_changes}")
            
#             # Get template
#             template = await db.get_graph_template("parameter_comparison_bar")
#             if not template:
#                 template = self._get_default_template()
            
#             # Extract numeric parameters
#             numeric_params = {}
#             for param_name, param_data in parameters.items():
#                 value = param_data.get("value")
#                 if isinstance(value, (int, float)):
#                     numeric_params[param_name] = value
            
#             # Apply colors
#             color_mapping = {}
            
#             for param_name, value in numeric_params.items():
#                 if param_name in color_changes:
#                     # Custom color from prompt
#                     color_mapping[param_name] = self._resolve_color_name(
#                         color_changes[param_name],
#                         template
#                     )
#                     logger.info(f"🎨 {param_name}: custom color '{color_changes[param_name]}'")
#                 else:
#                     # Auto color based on AI status
#                     status = await self._get_parameter_status_dynamic(param_name, value)
#                     color_mapping[param_name] = self._get_color_for_status(status, template)
#                     logger.info(f"🤖 {param_name}: auto color '{status}'")
            
#             # Create graph
#             fig, ax = plt.subplots(figsize=tuple(template['default_config']['figsize']))
            
#             param_names = list(numeric_params.keys())
#             values = list(numeric_params.values())
#             colors = [color_mapping[name] for name in param_names]
            
#             bars = ax.bar(
#                 param_names, 
#                 values, 
#                 color=colors, 
#                 edgecolor='black', 
#                 linewidth=1.5, 
#                 alpha=0.85
#             )
            
#             # Add value labels
#             for bar, value in zip(bars, values):
#                 height = bar.get_height()
#                 ax.text(
#                     bar.get_x() + bar.get_width() / 2.,
#                     height,
#                     f'{value:.2f}',
#                     ha='center',
#                     va='bottom',
#                     fontsize=9,
#                     fontweight='bold'
#                 )
            
#             # Styling
#             ax.set_xlabel(template['default_config']['xlabel'], fontsize=12, fontweight='bold')
#             ax.set_ylabel(template['default_config']['ylabel'], fontsize=12, fontweight='bold')
#             ax.set_title(template['default_config']['title'], fontsize=14, fontweight='bold', pad=20)
#             plt.xticks(rotation=template['default_config']['rotation'], ha='right', fontsize=10)
            
#             if template['default_config']['grid']:
#                 ax.grid(axis='y', alpha=0.3, linestyle='--')
            
#             plt.tight_layout()
            
#             # Save
#             buffer = BytesIO()
#             plt.savefig(buffer, format='png', dpi=template['default_config']['dpi'], bbox_inches='tight')
#             buffer.seek(0)
#             plt.close(fig)
            
#             # Upload
#             graph_url = await self._upload_to_s3(buffer, f"parameter_comparison_{report_id}_modified")
            
#             logger.info(f"✅ Modified graph created")
            
#             return {
#                 "graph_url": graph_url,
#                 "graph_type": "parameter_comparison_bar",
#                 "color_mapping": color_mapping,
#                 "prompt_applied": prompt,
#                 "created_at": datetime.utcnow()
#             }
            
#         except Exception as e:
#             logger.exception("❌ Graph modification failed")
#             raise Exception(f"Graph modification failed: {str(e)}")
    
#     # =====================================================
#     # 🤖 AI-POWERED DYNAMIC STATUS DETERMINATION
#     # =====================================================
#     async def _get_parameter_status_dynamic(self, param_name: str, value: float) -> str:
#         """
#         ✅ 100% DYNAMIC - No hard-coding
        
#         Strategy:
#         1. Try database first
#         2. If not in DB, ask AI
#         3. Cache result to avoid repeated API calls
        
#         Returns: "optimal", "good", "warning", "critical"
#         """
#         # Check cache first
#         cache_key = f"{param_name}:{value}"
#         if cache_key in self._status_cache:
#             logger.debug(f"📦 Cache hit: {param_name}")
#             return self._status_cache[cache_key]
        
#         # Strategy 1: Try database
#         standard = await db.get_parameter_standard(param_name)
        
#         if standard:
#             logger.debug(f"💾 Database standard found for {param_name}")
#             status = self._evaluate_with_thresholds(value, standard.get('thresholds', {}))
#             self._status_cache[cache_key] = status
#             return status
        
#         # Strategy 2: Ask AI
#         logger.info(f"🤖 No DB standard for {param_name}, asking AI...")
#         status = await self._ai_determine_status(param_name, value)
        
#         # Cache the result
#         self._status_cache[cache_key] = status
        
#         return status
    
#     def _evaluate_with_thresholds(self, value: float, thresholds: Dict) -> str:
#         """Evaluate value against threshold ranges"""
#         for level in ['optimal', 'good', 'warning', 'critical']:
#             threshold = thresholds.get(level, {})
            
#             if not threshold:
#                 continue
            
#             min_val = threshold.get('min', float('-inf'))
#             max_val = threshold.get('max', float('inf'))
            
#             if min_val <= value <= max_val:
#                 return level
        
#         return "good"  # Default
    
#     async def _ai_determine_status(self, param_name: str, value: float) -> str:
#         """
#         ✅ Ask GPT-4o to determine parameter status
        
#         Returns: "optimal", "good", "warning", or "critical"
#         """
#         try:
#             response = await self.client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": """You are a water quality expert. Evaluate water quality parameters for drinking water safety.

# Return ONLY one word from: optimal, good, warning, critical

# Definitions:
# - optimal: Ideal/best quality for drinking water
# - good: Acceptable/safe for drinking water
# - warning: Concerning/needs attention
# - critical: Dangerous/unsafe for drinking water

# Base your judgment on WHO, EPA, and international drinking water standards."""
#                     },
#                     {
#                         "role": "user",
#                         "content": f"Parameter: {param_name}\nValue: {value} mg/L\n\nStatus?"
#                     }
#                 ],
#                 temperature=0,
#                 max_tokens=10
#             )
            
#             status = response.choices[0].message.content.strip().lower()
            
#             # Validate response
#             valid_statuses = ['optimal', 'good', 'warning', 'critical']
            
#             if status not in valid_statuses:
#                 logger.warning(f"⚠️ AI returned invalid status '{status}', using 'good'")
#                 status = 'good'
            
#             logger.info(f"🤖 AI: {param_name}={value} → {status}")
            
#             return status
            
#         except Exception as e:
#             logger.error(f"❌ AI status determination failed: {e}")
#             return "good"  # Safe fallback
    
#     # =====================================================
#     # COLOR INTENT PARSING
#     # =====================================================
#     async def _parse_color_intent(self, prompt: str, available_params: list) -> Dict[str, str]:
#         """
#         Parse natural language color modification request
        
#         Returns: {"pH": "green", "TDS": "red", ...}
#         """
#         try:
#             logger.info(f"🔍 Parsing prompt: '{prompt}'")
            
#             response = await self.client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": f"""You are a color parser for water quality graphs.

# Available parameters: {', '.join(list(available_params))}

# Valid colors:
# - Status: optimal, good, warning, critical
# - Named: red, green, blue, yellow, orange, purple, pink, brown, gray

# Parse the user's request and return ONLY a JSON object.

# Rules:
# 1. Return ONLY valid JSON, no explanation
# 2. Use exact parameter names
# 3. If unclear, return empty: {{}}

# Examples:
# "make pH green" → {{"pH": "green"}}
# "color TDS red and Calcium blue" → {{"TDS": "red", "Calcium": "blue"}}
# "make a bar chart" → {{}}
# """
#                     },
#                     {
#                         "role": "user",
#                         "content": prompt
#                     }
#                 ],
#                 temperature=0,
#                 max_tokens=500
#             )
            
#             content = response.choices[0].message.content
            
#             if not content:
#                 return {}
            
#             logger.debug(f"GPT: {content}")
            
#             # Clean response
#             content = content.strip()
            
#             # Remove markdown
#             if "```json" in content:
#                 content = content.split("```json")[1].split("```")[0].strip()
#             elif "```" in content:
#                 content = content.split("```")[1].split("```")[0].strip()
            
#             # Find JSON
#             if not content.startswith("{"):
#                 import re
#                 match = re.search(r'\{[^}]+\}', content)
#                 if match:
#                     content = match.group(0)
#                 else:
#                     return {}
            
#             # Parse
#             color_changes = json.loads(content)
            
#             if not isinstance(color_changes, dict):
#                 return {}
            
#             logger.info(f"✅ Parsed: {color_changes}")
#             return color_changes
            
#         except Exception as e:
#             logger.error(f"❌ Parse failed: {e}")
#             return {}
    
#     def _resolve_color_name(self, color_name: str, template: Dict) -> str:
#         """Resolve color name to hex code"""
#         color_scheme = template.get('color_scheme', {})
        
#         color_name = color_name.lower().strip()
        
#         # Check status colors
#         if color_name in color_scheme:
#             return color_scheme[color_name]
        
#         # Check custom colors
#         custom_colors = color_scheme.get('custom_colors', {})
#         if color_name in custom_colors:
#             return custom_colors[color_name]
        
#         # Common colors
#         common = {
#             'red': '#F44336',
#             'green': '#4CAF50',
#             'blue': '#2196F3',
#             'yellow': '#FFC107',
#             'orange': '#FF9800',
#             'purple': '#9C27B0',
#             'pink': '#E91E63',
#             'brown': '#795548',
#             'gray': '#757575',
#             'grey': '#757575'
#         }
        
#         return common.get(color_name, '#757575')
    
#     def _get_color_for_status(self, status: str, template: Dict) -> str:
#         """Get hex color for status"""
#         color_scheme = template.get('color_scheme', {})
#         return color_scheme.get(status, '#757575')
    
#     # =====================================================
#     # S3 UPLOAD
#     # =====================================================
#     async def _upload_to_s3(self, buffer: BytesIO, filename_prefix: str) -> str:
#         """Upload to S3 and return pre-signed URL (7 days)"""
#         try:
#             timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
#             key = f"graphs/{filename_prefix}_{timestamp}.png"
            
#             self.s3_client.upload_fileobj(
#                 buffer,
#                 self.bucket_name,
#                 key,
#                 ExtraArgs={'ContentType': 'image/png'}
#             )
            
#             logger.info(f"✅ S3: {key}")
            
#             url = self.s3_client.generate_presigned_url(
#                 'get_object',
#                 Params={'Bucket': self.bucket_name, 'Key': key},
#                 ExpiresIn=604800  # 7 days
#             )
            
#             return url
            
#         except Exception as e:
#             logger.error(f"❌ S3 failed: {e}")
#             raise Exception(f"S3 upload failed: {str(e)}")
    
#     # =====================================================
#     # DEFAULT TEMPLATE
#     # =====================================================
#     def _get_default_template(self) -> Dict:
#         """Default graph template"""
#         return {
#             "graph_type": "parameter_comparison_bar",
#             "default_config": {
#                 "figsize": [14, 7],
#                 "dpi": 300,
#                 "title": "Water Quality Parameter Comparison",
#                 "xlabel": "Parameters",
#                 "ylabel": "Concentration (mg/L)",
#                 "rotation": 45,
#                 "grid": True
#             },
#             "color_scheme": {
#                 "optimal": "#4CAF50",     # Green - Best
#                 "good": "#8BC34A",        # Light Green - Safe
#                 "warning": "#FFC107",     # Yellow - Caution
#                 "critical": "#F44336",    # Red - Danger
#                 "unknown": "#757575",     # Gray - Unknown
#                 "custom_colors": {
#                     "red": "#F44336",
#                     "green": "#4CAF50",
#                     "blue": "#2196F3",
#                     "yellow": "#FFC107",
#                     "orange": "#FF9800",
#                     "purple": "#9C27B0",
#                     "pink": "#E91E63",
#                     "brown": "#795548",
#                     "gray": "#757575"
#                 }
#             }
#         }







"""
Graph Service - Enhanced
EXISTING: 2D SI bar chart
NEW:
  - 3D surface plot (PNG via matplotlib)
  - 3D JSON data export (for frontend Plotly.js)
  - Multi-salt support (switch salt without recalc)
  - Green/Yellow/Red zone overlay on 3D surface
"""

import logging
import base64
import io
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class GraphService:
    """Graph generation for water quality analysis"""

    # ========================================
    # EXISTING: 2D SI BAR CHART (keep as-is)
    # ========================================

    def generate_si_bar_chart(self, saturation_indices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate 2D bar chart of Saturation Indices
        Returns base64 PNG
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            if not saturation_indices:
                logger.warning("⚠️ No SI data for bar chart")
                return {"image_base64": None, "error": "No data"}

            minerals = [si["mineral_name"] for si in saturation_indices]
            values   = [si["si_value"]     for si in saturation_indices]

            # Color coding
            colors = []
            for v in values:
                if v > 0.5:
                    colors.append("#e74c3c")   # red
                elif v > 0.0:
                    colors.append("#f39c12")   # yellow/orange
                else:
                    colors.append("#2ecc71")   # green

            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(minerals, values, color=colors, edgecolor="white", linewidth=0.8)

            # Zero line
            ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-")
            ax.axhline(y=0.5, color="#e74c3c", linewidth=0.6, linestyle="--", alpha=0.6)

            ax.set_ylabel("Saturation Index (SI)", fontsize=11)
            ax.set_title("Saturation Indices", fontsize=14, fontweight="bold")
            ax.tick_params(axis="x", rotation=35)
            ax.grid(axis="y", alpha=0.3)
            fig.tight_layout()

            # Encode
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150)
            plt.close(fig)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")

            return {"image_base64": img_b64, "minerals": minerals, "values": values}

        except Exception as e:
            logger.error(f"❌ SI bar chart failed: {e}")
            raise

    # ========================================
    # NEW: PREPARE 3D GRAPH JSON DATA
    # ========================================

    def prepare_3d_graph_data(
        self,
        results: List[Dict[str, Any]],
        salt_name: str,
        x_axis: str = "pH",
        y_axis: str = "CoC"
    ) -> Dict[str, Any]:
        """
        Transform stored grid results into structured JSON
        ready for frontend Plotly.js 3D surface rendering.

        Args:
            results:   List of grid-point results from analysis_engine
            salt_name: Which mineral SI to plot (e.g. "Calcite")
            x_axis:    "pH" | "CoC" | "temp"
            y_axis:    "pH" | "CoC" | "temp"

        Returns:
            {
                "x": [...],          // unique sorted x values
                "y": [...],          // unique sorted y values
                "z": [[...], ...],   // 2D matrix  z[yi][xi] = SI
                "color_zones": [[...]], // "green"|"yellow"|"red"
                "salt_name": str,
                "x_axis_label": str,
                "y_axis_label": str,
                "available_salts": [...]  // all salts in dataset (for dropdown)
            }
        """
        try:
            # Axis key mapping from result dicts
            axis_key_map = {"pH": "pH", "CoC": "CoC", "temp": "temperature_C"}
            x_key = axis_key_map.get(x_axis, "pH")
            y_key = axis_key_map.get(y_axis, "CoC")

            # Collect all (x, y, SI) triples
            x_set, y_set = set(), set()
            point_map = {}           # (x_round, y_round) → SI
            available_salts = set()

            for r in results:
                if "error" in r:
                    continue

                x_val = r.get(x_key)
                y_val = r.get(y_key)
                if x_val is None or y_val is None:
                    continue

                x_r = round(x_val, 2)
                y_r = round(y_val, 2)
                x_set.add(x_r)
                y_set.add(y_r)

                for si in r.get("saturation_indices", []):
                    available_salts.add(si["mineral_name"])
                    if si["mineral_name"] == salt_name:
                        point_map[(x_r, y_r)] = si["si_value"]

            # Sort axes
            x_sorted = sorted(x_set)
            y_sorted = sorted(y_set)

            # Build 2D z-matrix  and  color-zone matrix
            from app.utils.salt_data_table import classify_si_value

            z_matrix     = []
            color_matrix = []

            for y_val in y_sorted:
                z_row     = []
                color_row = []
                for x_val in x_sorted:
                    si = point_map.get((x_val, y_val))
                    z_row.append(si if si is not None else None)
                    color_row.append(
                        classify_si_value(salt_name, si) if si is not None else "unknown"
                    )
                z_matrix.append(z_row)
                color_matrix.append(color_row)

            # Axis labels
            label_map = {"pH": "pH", "CoC": "Cycles of Concentration", "temp": "Temperature (°C)"}

            logger.info(f"✅ 3D JSON prepared: {salt_name}, {len(x_sorted)}×{len(y_sorted)} grid")

            return {
                "x":              x_sorted,
                "y":              y_sorted,
                "z":              z_matrix,
                "color_zones":    color_matrix,
                "salt_name":      salt_name,
                "x_axis_label":   label_map.get(x_axis, x_axis),
                "y_axis_label":   label_map.get(y_axis, y_axis),
                "z_axis_label":   "Saturation Index (SI)",
                "available_salts": sorted(available_salts)
            }

        except Exception as e:
            logger.error(f"❌ 3D JSON prep failed: {e}")
            raise

    # ========================================
    # NEW: GENERATE 3D SURFACE PNG (matplotlib)
    # ========================================

    def generate_3d_surface_png(
        self,
        results: List[Dict[str, Any]],
        salt_name: str,
        x_axis: str = "pH",
        y_axis: str = "CoC"
    ) -> str:
        """
        Generate server-side 3D surface plot as base64 PNG.
        Uses matplotlib Axes3D with colour-mapped SI values.

        Returns:
            base64-encoded PNG string
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from matplotlib import cm
            from matplotlib.colors import BoundaryNorm

            # Reuse JSON prep to get the matrix
            graph_data = self.prepare_3d_graph_data(results, salt_name, x_axis, y_axis)

            x_vals = np.array(graph_data["x"])
            y_vals = np.array(graph_data["y"])
            z_raw  = graph_data["z"]

            if not x_vals.size or not y_vals.size:
                raise ValueError("No data points for 3D plot")

            # Build meshgrid
            X, Y = np.meshgrid(x_vals, y_vals)

            # Fill Z (replace None → NaN)
            Z = np.array([
                [v if v is not None else np.nan for v in row]
                for row in z_raw
            ], dtype=float)

            # --- Colour map: green < 0 < yellow < 0.5 < red ---
            cmap   = cm.RdYlGn_r                        # red-yellow-green reversed
            bounds = [-2.0, -0.5, 0.0, 0.5, 1.0, 3.0]
            norm   = BoundaryNorm(bounds, cmap.N)

            # --- Plot ---
            fig = plt.figure(figsize=(12, 7))
            ax  = fig.add_subplot(111, projection="3d")

            surf = ax.plot_surface(
                X, Y, Z,
                cmap=cmap, norm=norm,
                rstride=1, cstride=1,
                alpha=0.85, edgecolor="none"
            )

            # SI = 0 reference plane (transparent)
            ax.plot_surface(
                X, Y, np.zeros_like(Z),
                alpha=0.08, color="black"
            )

            # Labels
            label_map = {"pH": "pH", "CoC": "Cycles of Concentration", "temp": "Temperature (°C)"}
            ax.set_xlabel(label_map.get(x_axis, x_axis), fontsize=10, labelpad=10)
            ax.set_ylabel(label_map.get(y_axis, y_axis), fontsize=10, labelpad=10)
            ax.set_zlabel("SI", fontsize=10, labelpad=8)
            ax.set_title(f"3D Saturation Index — {salt_name}", fontsize=13, fontweight="bold")

            # Colour bar
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=15, pad=0.1, label="SI")

            # View angle
            ax.view_init(elev=25, azim=-60)
            fig.tight_layout()

            # Encode
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150)
            plt.close(fig)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")

        except Exception as e:
            logger.error(f"❌ 3D surface PNG failed: {e}")
            raise

    # ========================================
    # NEW: MULTI-SALT COMPARISON (2D heatmap)
    # ========================================

    def generate_multi_salt_heatmap(
        self,
        results: List[Dict[str, Any]],
        salt_names: List[str],
        x_axis: str = "pH",
        y_axis: str = "CoC"
    ) -> str:
        """
        Side-by-side 2D heatmaps for multiple salts.
        Useful when user switches salt via dropdown — each
        sub-plot pre-rendered in one image.

        Returns:
            base64 PNG
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib import cm
            from matplotlib.colors import BoundaryNorm

            n_salts = len(salt_names)
            if n_salts == 0:
                raise ValueError("No salts provided")

            cols = min(n_salts, 3)
            rows = (n_salts + cols - 1) // cols

            fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
            if n_salts == 1:
                axes = [axes]
            else:
                axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

            cmap   = cm.RdYlGn_r
            bounds = [-2.0, -0.5, 0.0, 0.5, 1.0, 3.0]
            norm   = BoundaryNorm(bounds, cmap.N)

            label_map = {"pH": "pH", "CoC": "CoC", "temp": "Temp (°C)"}

            for idx, salt in enumerate(salt_names):
                if idx >= len(axes):
                    break
                ax = axes[idx]

                gd = self.prepare_3d_graph_data(results, salt, x_axis, y_axis)
                x_vals = np.array(gd["x"])
                y_vals = np.array(gd["y"])
                Z = np.array([
                    [v if v is not None else np.nan for v in row]
                    for row in gd["z"]
                ], dtype=float)

                im = ax.imshow(
                    Z, origin="lower", aspect="auto",
                    extent=[x_vals.min(), x_vals.max(), y_vals.min(), y_vals.max()],
                    cmap=cmap, norm=norm
                )
                ax.set_xlabel(label_map.get(x_axis, x_axis))
                ax.set_ylabel(label_map.get(y_axis, y_axis))
                ax.set_title(salt, fontweight="bold")
                fig.colorbar(im, ax=ax, shrink=0.8, label="SI")

            # Hide unused subplots
            for idx in range(n_salts, len(axes)):
                axes[idx].set_visible(False)

            fig.suptitle("Multi-Salt Saturation Heatmaps", fontsize=14, fontweight="bold", y=1.02)
            fig.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            logger.info(f"✅ Multi-salt heatmap generated: {salt_names}")
            return base64.b64encode(buf.read()).decode("utf-8")

        except Exception as e:
            logger.error(f"❌ Multi-salt heatmap failed: {e}")
            raise

    # ========================================
    # NEW: GREEN/YELLOW/RED ZONE SUMMARY
    # ========================================

    @staticmethod
    def summarize_zones(
        results: List[Dict[str, Any]],
        salt_name: str
    ) -> Dict[str, Any]:
        """
        Count green / yellow / red points for a salt across all grid results.
        """
        from app.utils.salt_data_table import classify_si_value

        counts = {"green": 0, "yellow": 0, "red": 0, "unknown": 0}

        for r in results:
            if "error" in r:
                counts["unknown"] += 1
                continue
            for si in r.get("saturation_indices", []):
                if si["mineral_name"] == salt_name:
                    zone = classify_si_value(salt_name, si["si_value"])
                    counts[zone] = counts.get(zone, 0) + 1

        total = sum(counts.values())
        pct   = {k: round((v / total * 100), 1) if total else 0 for k, v in counts.items()}

        return {"counts": counts, "percentages": pct, "total_points": total}