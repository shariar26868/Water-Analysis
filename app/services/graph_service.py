

"""
Graph Service - Generate and modify water quality graphs
Uses Matplotlib + GPT-4 for prompt-based modifications
100% Dynamic - No hard-coded thresholds
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from openai import AsyncOpenAI
import boto3
from botocore.exceptions import ClientError

from app.db.mongo import db

logger = logging.getLogger(__name__)


class GraphService:
    """Generate dynamic water quality graphs"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        self.bucket_name = os.getenv("AWS_S3_BUCKET")
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = 300
    
    async def create_parameter_graph(
        self, 
        parameters: Dict[str, Any],
        chemical_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create parameter comparison bar graph with auto-colored bars
        
        Colors based on dynamic thresholds from database
        """
        try:
            logger.info("📊 Creating parameter comparison graph")
            
            # Get graph template from database
            template = await db.get_graph_template("parameter_comparison_bar")
            if not template:
                template = self._get_default_template()
            
            # Extract numeric parameters only
            numeric_params = {}
            for param_name, param_data in parameters.items():
                value = param_data.get("value")
                if isinstance(value, (int, float)):
                    numeric_params[param_name] = value
            
            if not numeric_params:
                raise Exception("No numeric parameters found for graphing")
            
            # Determine status and color for each parameter
            color_mapping = {}
            for param_name in numeric_params.keys():
                status = await self._get_parameter_status(param_name, numeric_params[param_name])
                color = await self._get_color_for_status(status, template)
                color_mapping[param_name] = color
            
            # Create graph
            fig, ax = plt.subplots(figsize=tuple(template['default_config']['figsize']))
            
            param_names = list(numeric_params.keys())
            values = list(numeric_params.values())
            colors = [color_mapping[name] for name in param_names]
            
            # Create bars
            bars = ax.bar(param_names, values, color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{value:.2f}',
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold'
                )
            
            # Styling
            ax.set_xlabel(
                template['default_config']['xlabel'],
                fontsize=12,
                fontweight='bold'
            )
            ax.set_ylabel(
                template['default_config']['ylabel'],
                fontsize=12,
                fontweight='bold'
            )
            ax.set_title(
                template['default_config']['title'],
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            
            # Rotate x-axis labels
            plt.xticks(rotation=template['default_config']['rotation'], ha='right', fontsize=10)
            
            # Grid
            if template['default_config']['grid']:
                ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            
            # Save to buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=template['default_config']['dpi'], bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)
            
            # Upload to S3
            graph_url = await self._upload_to_s3(buffer, "parameter_comparison")
            
            logger.info(f"✅ Graph created: {graph_url}")
            
            return {
                "graph_url": graph_url,
                "graph_type": "parameter_comparison_bar",
                "color_mapping": {
                    name: await self._get_parameter_status(name, numeric_params[name])
                    for name in param_names
                },
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"❌ Graph creation failed: {e}")
            raise Exception(f"Graph creation failed: {str(e)}")
    
    async def modify_with_prompt(
        self,
        report_id: str,
        parameters: Dict[str, Any],
        prompt: str
    ) -> Dict[str, Any]:
        """
        Modify graph colors using natural language prompt
        
        Example: "Make pH bar green and TDS bar red"
        """
        try:
            logger.info(f"🎨 Modifying graph with prompt: {prompt}")
            
            # Parse intent using GPT-4
            color_changes = await self._parse_color_intent(prompt, parameters.keys())
            
            # Get template
            template = await db.get_graph_template("parameter_comparison_bar")
            if not template:
                template = self._get_default_template()
            
            # Extract numeric parameters
            numeric_params = {}
            for param_name, param_data in parameters.items():
                value = param_data.get("value")
                if isinstance(value, (int, float)):
                    numeric_params[param_name] = value
            
            # Apply custom colors
            color_mapping = {}
            for param_name in numeric_params.keys():
                if param_name in color_changes:
                    # Use custom color from prompt
                    color_mapping[param_name] = self._resolve_color_name(
                        color_changes[param_name],
                        template
                    )
                else:
                    # Use auto color
                    status = await self._get_parameter_status(param_name, numeric_params[param_name])
                    color_mapping[param_name] = await self._get_color_for_status(status, template)
            
            # Create graph with custom colors
            fig, ax = plt.subplots(figsize=tuple(template['default_config']['figsize']))
            
            param_names = list(numeric_params.keys())
            values = list(numeric_params.values())
            colors = [color_mapping[name] for name in param_names]
            
            bars = ax.bar(param_names, values, color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
            
            # Add value labels
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{value:.2f}',
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold'
                )
            
            # Styling (same as before)
            ax.set_xlabel(template['default_config']['xlabel'], fontsize=12, fontweight='bold')
            ax.set_ylabel(template['default_config']['ylabel'], fontsize=12, fontweight='bold')
            ax.set_title(template['default_config']['title'], fontsize=14, fontweight='bold', pad=20)
            plt.xticks(rotation=template['default_config']['rotation'], ha='right', fontsize=10)
            
            if template['default_config']['grid']:
                ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            
            # Save
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=template['default_config']['dpi'], bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)
            
            # Upload to S3
            graph_url = await self._upload_to_s3(buffer, f"parameter_comparison_{report_id}_modified")
            
            logger.info(f"✅ Modified graph created: {graph_url}")
            
            return {
                "graph_url": graph_url,
                "graph_type": "parameter_comparison_bar",
                "color_mapping": color_mapping,
                "prompt_applied": prompt,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"❌ Graph modification failed: {e}")
            raise Exception(f"Graph modification failed: {str(e)}")
    
    async def _parse_color_intent(self, prompt: str, available_params: list) -> Dict[str, str]:
        """
        Use GPT-4 to parse natural language color modification request
        
        Returns:
            {"pH": "green", "TDS": "red", ...}
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Parse color modification request for water quality graph.
Available parameters: {list(available_params)}
Valid colors: red, green, blue, yellow, orange, purple, optimal, good, warning, critical

Return ONLY valid JSON: {{"parameter_name": "color_name"}}
Example: {{"pH": "green", "TDS": "red"}}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            color_changes = json.loads(content)
            
            logger.info(f"🎨 Parsed color changes: {color_changes}")
            
            return color_changes
            
        except Exception as e:
            logger.error(f"❌ Failed to parse color intent: {e}")
            return {}
    
    def _resolve_color_name(self, color_name: str, template: Dict) -> str:
        """
        Resolve color name to hex code
        
        Supports: "red", "green", "optimal", "warning", etc.
        """
        color_scheme = template.get('color_scheme', {})
        
        # Check if it's a status color
        if color_name in color_scheme:
            return color_scheme[color_name]
        
        # Check custom colors
        custom_colors = color_scheme.get('custom_colors', {})
        if color_name in custom_colors:
            return custom_colors[color_name]
        
        # Default
        return '#757575'  # Gray
    
    async def _get_parameter_status(self, param_name: str, value: float) -> str:
        """
        Get parameter status from database thresholds
        
        Returns: "optimal", "good", "warning", or "critical"
        """
        # Get parameter standard from database
        standard = await db.get_parameter_standard(param_name)
        
        if not standard:
            logger.warning(f"⚠️ No standard found for {param_name}, using 'good' as default")
            return "good"
        
        thresholds = standard.get('thresholds', {})
        
        # Check each level
        for level in ['optimal', 'good', 'warning', 'critical']:
            threshold = thresholds.get(level, {})
            
            min_val = threshold.get('min', float('-inf'))
            max_val = threshold.get('max', float('inf'))
            
            if min_val <= value <= max_val:
                return level
        
        return "unknown"
    
    async def _get_color_for_status(self, status: str, template: Dict) -> str:
        """Get hex color for status"""
        color_scheme = template.get('color_scheme', {})
        return color_scheme.get(status, '#757575')
    
    # =====================================================
    # 🔧 FIXED: S3 Upload without ACL + Pre-signed URL
    # =====================================================
    async def _upload_to_s3(self, buffer: BytesIO, filename_prefix: str) -> str:
        """
        Upload graph image to S3 and return pre-signed URL
        
        FIXED: Removed ACL (not supported), using pre-signed URLs instead
        
        Args:
            buffer: Image buffer
            filename_prefix: Prefix for filename
            
        Returns:
            Pre-signed URL (valid for 7 days)
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            key = f"graphs/{filename_prefix}_{timestamp}.png"
            
            # ✅ FIXED: Upload WITHOUT ACL parameter
            self.s3_client.upload_fileobj(
                buffer,
                self.bucket_name,
                key,
                ExtraArgs={
                    'ContentType': 'image/png'
                    # ❌ REMOVED: 'ACL': 'public-read'
                }
            )
            
            logger.info(f"✅ Uploaded to S3: {key}")
            
            # ✅ Generate pre-signed URL (valid for 7 days = 604800 seconds)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=604800  # 7 days
            )
            
            logger.info(f"✅ Generated pre-signed URL (expires in 7 days)")
            
            return url
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise Exception(f"S3 upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected S3 error: {e}")
            raise Exception(f"S3 upload error: {str(e)}")
    
    def _get_default_template(self) -> Dict:
        """Default graph template"""
        return {
            "graph_type": "parameter_comparison_bar",
            "default_config": {
                "figsize": [14, 7],
                "dpi": 300,
                "title": "Water Quality Parameter Comparison",
                "xlabel": "Parameters",
                "ylabel": "Concentration (mg/L)",
                "rotation": 45,
                "grid": True
            },
            "color_scheme": {
                "optimal": "#4CAF50",     # Green
                "good": "#8BC34A",        # Light Green
                "warning": "#FFC107",     # Yellow
                "critical": "#F44336",    # Red
                "unknown": "#757575",     # Gray
                "custom_colors": {
                    "red": "#F44336",
                    "green": "#4CAF50",
                    "blue": "#2196F3",
                    "yellow": "#FFC107",
                    "orange": "#FF9800",
                    "purple": "#9C27B0"
                }
            }
        }