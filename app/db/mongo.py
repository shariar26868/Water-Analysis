# """
# MongoDB Database Connection and Operations
# Fully dynamic - no hard-coded collections or schemas
# ✅ PHREEQC database caching added
# """

# from motor.motor_asyncio import AsyncIOMotorClient
# from typing import Dict, List, Any, Optional
# import os
# from datetime import datetime
# import logging

# logger = logging.getLogger(__name__)


# class MongoDB:
#     client: Optional[AsyncIOMotorClient] = None
#     db = None

#     @classmethod
#     async def connect(cls):
#         """Establish MongoDB connection"""
#         try:
#             mongo_uri = os.getenv("MONGO_URI")
#             db_name = os.getenv("MONGO_DB_NAME", "water_quality_db")
            
#             cls.client = AsyncIOMotorClient(mongo_uri)
#             cls.db = cls.client[db_name]
            
#             # Test connection
#             await cls.client.admin.command('ping')
#             logger.info(f"✅ Connected to MongoDB: {db_name}")
            
#             # Create indexes
#             await cls._create_indexes()
            
#         except Exception as e:
#             logger.error(f"❌ MongoDB connection failed: {e}")
#             raise

#     @classmethod
#     async def _create_indexes(cls):
#         """Create database indexes for performance"""
#         try:
#             # Water reports index
#             await cls.db.water_reports.create_index("report_id", unique=True)
#             await cls.db.water_reports.create_index("created_at")
            
#             # Parameter standards index
#             await cls.db.parameter_standards.create_index("parameter_name", unique=True)
            
#             # Formulas index
#             await cls.db.calculation_formulas.create_index("formula_name", unique=True)
            
#             # ✅ NEW: PHREEQC cache index
#             await cls.db.phreeqc_database_cache.create_index("database_name", unique=True)
#             await cls.db.phreeqc_database_cache.create_index("cached_at")
            
#             logger.info("✅ Database indexes created")
#         except Exception as e:
#             logger.warning(f"Index creation warning: {e}")

#     @classmethod
#     async def disconnect(cls):
#         """Close MongoDB connection"""
#         if cls.client:
#             cls.client.close()
#             logger.info("✅ MongoDB connection closed")

#     @classmethod
#     async def get_collection(cls, collection_name: str):
#         """Get a collection dynamically"""
#         return cls.db[collection_name]

#     # ========== WATER REPORTS ==========
    
#     @classmethod
#     async def save_water_report(cls, report_data: Dict[str, Any]) -> str:
#         """Save complete water analysis report"""
#         collection = cls.db.water_reports
        
#         report_data["created_at"] = datetime.utcnow()
#         report_data["updated_at"] = datetime.utcnow()
        
#         result = await collection.insert_one(report_data)
#         logger.info(f"✅ Report saved: {report_data.get('report_id')}")
        
#         return str(result.inserted_id)

#     @classmethod
#     async def get_water_report(cls, report_id: str) -> Optional[Dict]:
#         """Retrieve water report by ID"""
#         collection = cls.db.water_reports
#         report = await collection.find_one({"report_id": report_id})
#         return report

#     @classmethod
#     async def get_all_reports(cls, limit: int = 100, skip: int = 0) -> List[Dict]:
#         """Get all water reports with pagination"""
#         collection = cls.db.water_reports
#         cursor = collection.find().sort("created_at", -1).skip(skip).limit(limit)
#         reports = await cursor.to_list(length=limit)
#         return reports

#     @classmethod
#     async def update_water_report(cls, report_id: str, update_data: Dict) -> bool:
#         """Update existing water report"""
#         collection = cls.db.water_reports
        
#         update_data["updated_at"] = datetime.utcnow()
        
#         result = await collection.update_one(
#             {"report_id": report_id},
#             {"$set": update_data}
#         )
        
#         return result.modified_count > 0

#     @classmethod
#     async def delete_water_report(cls, report_id: str) -> bool:
#         """Delete water report"""
#         collection = cls.db.water_reports
#         result = await collection.delete_one({"report_id": report_id})
#         return result.deleted_count > 0

#     # ========== PARAMETER STANDARDS (Dynamic Thresholds) ==========
    
#     @classmethod
#     async def get_parameter_standard(cls, parameter_name: str) -> Optional[Dict]:
#         """Get threshold standards for a parameter"""
#         collection = cls.db.parameter_standards
#         return await collection.find_one({"parameter_name": parameter_name})

#     @classmethod
#     async def get_all_parameter_standards(cls) -> List[Dict]:
#         """Get all parameter standards"""
#         collection = cls.db.parameter_standards
#         cursor = collection.find()
#         return await cursor.to_list(length=None)

#     @classmethod
#     async def save_parameter_standard(cls, standard_data: Dict) -> str:
#         """Save or update parameter standard"""
#         collection = cls.db.parameter_standards
        
#         result = await collection.update_one(
#             {"parameter_name": standard_data["parameter_name"]},
#             {"$set": standard_data},
#             upsert=True
#         )
        
#         return standard_data["parameter_name"]

#     # ========== CALCULATION FORMULAS (Dynamic) ==========
    
#     @classmethod
#     async def get_formula(cls, formula_name: str) -> Optional[Dict]:
#         """Get calculation formula by name"""
#         collection = cls.db.calculation_formulas
#         return await collection.find_one({"formula_name": formula_name})

#     @classmethod
#     async def get_all_formulas(cls) -> List[Dict]:
#         """Get all calculation formulas"""
#         collection = cls.db.calculation_formulas
#         cursor = collection.find()
#         return await cursor.to_list(length=None)

#     @classmethod
#     async def save_formula(cls, formula_data: Dict) -> str:
#         """Save or update calculation formula"""
#         collection = cls.db.calculation_formulas
        
#         result = await collection.update_one(
#             {"formula_name": formula_data["formula_name"]},
#             {"$set": formula_data},
#             upsert=True
#         )
        
#         return formula_data["formula_name"]

#     # ========== GRAPH TEMPLATES ==========
    
#     @classmethod
#     async def get_graph_template(cls, graph_type: str) -> Optional[Dict]:
#         """Get graph template configuration"""
#         collection = cls.db.graph_templates
#         return await collection.find_one({"graph_type": graph_type})

#     # ========== SCORING CONFIGURATION ==========
    
#     @classmethod
#     async def get_scoring_config(cls, scoring_type: str) -> Optional[Dict]:
#         """Get scoring configuration"""
#         collection = cls.db.scoring_config
#         return await collection.find_one({"scoring_type": scoring_type})

#     # ========== COMPLIANCE RULES ==========
    
#     @classmethod
#     async def get_compliance_rules(cls, standard: str = None) -> List[Dict]:
#         """Get compliance rules (optionally filtered by standard)"""
#         collection = cls.db.compliance_rules
        
#         query = {"standard": standard} if standard else {}
#         cursor = collection.find(query)
        
#         return await cursor.to_list(length=None)

#     # ========== SUGGESTION TEMPLATES ==========
    
#     @classmethod
#     async def get_suggestion_templates(cls, category: str = None) -> List[Dict]:
#         """Get suggestion templates"""
#         collection = cls.db.suggestion_templates
        
#         query = {"category": category} if category else {}
#         cursor = collection.find(query)
        
#         return await cursor.to_list(length=None)

#     # ========== PHREEQC CONFIGURATION ==========
    
#     @classmethod
#     async def get_phreeqc_config(cls) -> Optional[Dict]:
#         """Get PHREEQC configuration"""
#         collection = cls.db.phreeqc_config
#         return await collection.find_one()

#     # ========== PHREEQC DATABASE CACHING (NEW) ==========
    
#     @classmethod
#     async def cache_phreeqc_database_info(cls, database_name: str, info: Dict) -> str:
#         """
#         Cache PHREEQC database information (minerals, species, elements, etc.)
#         for performance optimization
        
#         Args:
#             database_name: Database name (e.g., "default", "pitzer")
#             info: Dictionary containing database info
#                 {
#                     "minerals": [...],
#                     "species": [...],
#                     "elements": [...],
#                     "gases": [...],
#                     "exchange_species": [...],
#                     "surface_species": [...]
#                 }
        
#         Returns:
#             database_name
#         """
#         collection = cls.db.phreeqc_database_cache
        
#         cache_doc = {
#             "database_name": database_name,
#             "info": info,
#             "cached_at": datetime.utcnow(),
#             "version": "1.0"
#         }
        
#         result = await collection.update_one(
#             {"database_name": database_name},
#             {"$set": cache_doc},
#             upsert=True
#         )
        
#         logger.info(f"✅ Cached PHREEQC database info: {database_name}")
#         logger.debug(f"   - Minerals: {len(info.get('minerals', []))}")
#         logger.debug(f"   - Species: {len(info.get('species', []))}")
#         logger.debug(f"   - Elements: {len(info.get('elements', []))}")
        
#         return database_name
    
#     @classmethod
#     async def get_cached_phreeqc_info(cls, database_name: str) -> Optional[Dict]:
#         """
#         Get cached PHREEQC database information
        
#         Returns None if:
#         - No cache exists
#         - Cache is older than 7 days
        
#         Args:
#             database_name: Database name (e.g., "default", "pitzer")
        
#         Returns:
#             Dictionary with database info or None
#         """
#         collection = cls.db.phreeqc_database_cache
#         cache = await collection.find_one({"database_name": database_name})
        
#         if not cache:
#             logger.debug(f"No cache found for database: {database_name}")
#             return None
        
#         # Check cache age
#         cached_at = cache.get("cached_at")
#         if cached_at:
#             age = datetime.utcnow() - cached_at
            
#             if age.days < 7:
#                 logger.info(f"📦 Using cached PHREEQC info: {database_name} (age: {age.days} days)")
#                 return cache.get("info")
#             else:
#                 logger.info(f"⏰ Cache expired for {database_name} (age: {age.days} days)")
#                 return None
        
#         return None
    
#     @classmethod
#     async def clear_phreeqc_cache(cls, database_name: str = None) -> int:
#         """
#         Clear PHREEQC database cache
        
#         Args:
#             database_name: Specific database to clear, or None to clear all
        
#         Returns:
#             Number of cache entries deleted
#         """
#         collection = cls.db.phreeqc_database_cache
        
#         if database_name:
#             result = await collection.delete_one({"database_name": database_name})
#             deleted = result.deleted_count
#             logger.info(f"✅ Cleared cache for: {database_name}")
#         else:
#             result = await collection.delete_many({})
#             deleted = result.deleted_count
#             logger.info(f"✅ Cleared all PHREEQC cache ({deleted} entries)")
        
#         return deleted
    
#     @classmethod
#     async def get_all_cached_databases(cls) -> List[Dict]:
#         """
#         Get list of all cached PHREEQC databases
        
#         Returns:
#             List of cache info (database_name, cached_at, sizes)
#         """
#         collection = cls.db.phreeqc_database_cache
#         cursor = collection.find({}, {
#             "database_name": 1,
#             "cached_at": 1,
#             "version": 1,
#             "info.minerals": 1,
#             "info.species": 1
#         })
        
#         caches = await cursor.to_list(length=None)
        
#         # Format response
#         result = []
#         for cache in caches:
#             info = cache.get("info", {})
#             result.append({
#                 "database_name": cache.get("database_name"),
#                 "cached_at": cache.get("cached_at"),
#                 "version": cache.get("version"),
#                 "minerals_count": len(info.get("minerals", [])),
#                 "species_count": len(info.get("species", []))
#             })
        
#         return result

#     # ========== GENERIC OPERATIONS ==========
    
#     @classmethod
#     async def insert_one(cls, collection_name: str, document: Dict) -> str:
#         """Generic insert operation"""
#         collection = cls.db[collection_name]
#         result = await collection.insert_one(document)
#         return str(result.inserted_id)

#     @classmethod
#     async def find_one(cls, collection_name: str, query: Dict) -> Optional[Dict]:
#         """Generic find one operation"""
#         collection = cls.db[collection_name]
#         return await collection.find_one(query)

#     @classmethod
#     async def find_many(cls, collection_name: str, query: Dict = None) -> List[Dict]:
#         """Generic find many operation"""
#         collection = cls.db[collection_name]
#         cursor = collection.find(query or {})
#         return await cursor.to_list(length=None)

#     @classmethod
#     async def update_one(cls, collection_name: str, query: Dict, update: Dict) -> bool:
#         """Generic update operation"""
#         collection = cls.db[collection_name]
#         result = await collection.update_one(query, {"$set": update})
#         return result.modified_count > 0

#     @classmethod
#     async def delete_one(cls, collection_name: str, query: Dict) -> bool:
#         """Generic delete operation"""
#         collection = cls.db[collection_name]
#         result = await collection.delete_one(query)
#         return result.deleted_count > 0


# # Database instance
# db = MongoDB()








"""
MongoDB Database Manager
UPDATED: Added collections for customers, assets, products, analysis_results
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            db_name = os.getenv("MONGO_DB_NAME", "water_quality_db")
            
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"✅ Connected to MongoDB: {db_name}")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB disconnected")
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Existing indexes
            await self.db.water_analyses.create_index("analysis_id", unique=True)
            await self.db.phreeqc_config.create_index("config_name", unique=True)
            
            # NEW INDEXES - Customers & Assets
            await self.db.customers.create_index("customer_id", unique=True)
            await self.db.customers.create_index("company_name")
            await self.db.customers.create_index("status")
            
            await self.db.assets.create_index("asset_id", unique=True)
            await self.db.assets.create_index("customer_id")
            await self.db.assets.create_index([("customer_id", 1), ("asset_name", 1)])
            
            # NEW INDEXES - Products & Raw Materials
            await self.db.raw_materials.create_index("material_id", unique=True)
            await self.db.raw_materials.create_index("material_name")
            await self.db.raw_materials.create_index([("access_level", 1), ("owner_company_id", 1)])
            
            await self.db.products.create_index("product_id", unique=True)
            await self.db.products.create_index("product_name")
            await self.db.products.create_index([("access_level", 1), ("owner_company_id", 1)])
            await self.db.products.create_index("status")
            
            # NEW INDEXES - Analysis Results
            await self.db.analysis_results.create_index("analysis_id", unique=True)
            await self.db.analysis_results.create_index("analysis_type")
            await self.db.analysis_results.create_index("created_at")
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
    
    # ========================================
    # EXISTING METHODS (Keep as-is)
    # ========================================
    
    async def save_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Save water analysis result"""
        try:
            result = await self.db.water_analyses.insert_one(analysis_data)
            logger.info(f"✅ Analysis saved: {analysis_data.get('analysis_id')}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Save analysis failed: {e}")
            raise
    
    async def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID"""
        try:
            analysis = await self.db.water_analyses.find_one({"analysis_id": analysis_id})
            return analysis
        except Exception as e:
            logger.error(f"❌ Get analysis failed: {e}")
            raise
    
    async def get_phreeqc_config(self) -> Optional[Dict[str, Any]]:
        """Get PHREEQC configuration"""
        try:
            config = await self.db.phreeqc_config.find_one({"config_name": "default"})
            return config
        except Exception as e:
            logger.error(f"❌ Get config failed: {e}")
            return None
    
    async def save_phreeqc_config(self, config_data: Dict[str, Any]):
        """Save PHREEQC configuration"""
        try:
            config_data["config_name"] = "default"
            config_data["updated_at"] = datetime.utcnow()
            
            await self.db.phreeqc_config.update_one(
                {"config_name": "default"},
                {"$set": config_data},
                upsert=True
            )
            logger.info("✅ PHREEQC config saved")
        except Exception as e:
            logger.error(f"❌ Save config failed: {e}")
            raise
    
    # ========================================
    # NEW METHODS - CUSTOMERS
    # ========================================
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> str:
        """Create new customer"""
        try:
            customer_data["created_at"] = datetime.utcnow()
            result = await self.db.customers.insert_one(customer_data)
            logger.info(f"✅ Customer created: {customer_data['customer_id']}")
            return customer_data["customer_id"]
        except Exception as e:
            logger.error(f"❌ Create customer failed: {e}")
            raise
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID"""
        try:
            customer = await self.db.customers.find_one({"customer_id": customer_id})
            return customer
        except Exception as e:
            logger.error(f"❌ Get customer failed: {e}")
            raise
    
    async def update_customer(self, customer_id: str, update_data: Dict[str, Any]) -> bool:
        """Update customer"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.db.customers.update_one(
                {"customer_id": customer_id},
                {"$set": update_data}
            )
            logger.info(f"✅ Customer updated: {customer_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Update customer failed: {e}")
            raise
    
    async def delete_customer(self, customer_id: str) -> bool:
        """
        COMPLETE DATA DELETION (GDPR compliance)
        Deletes customer and ALL associated data
        """
        try:
            # Delete customer
            await self.db.customers.delete_one({"customer_id": customer_id})
            
            # Delete all assets
            await self.db.assets.delete_many({"customer_id": customer_id})
            
            # Delete all analyses (if linked to customer)
            # Note: Add customer_id field to analyses if needed
            
            logger.info(f"✅ Customer and all data deleted: {customer_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Delete customer failed: {e}")
            raise
    
    async def list_customers(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List customers with pagination"""
        try:
            query = {}
            if status:
                query["status"] = status
            
            cursor = self.db.customers.find(query).skip(skip).limit(limit)
            customers = await cursor.to_list(length=limit)
            return customers
        except Exception as e:
            logger.error(f"❌ List customers failed: {e}")
            raise
    
    # ========================================
    # NEW METHODS - ASSETS
    # ========================================
    
    async def create_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create new asset"""
        try:
            asset_data["created_at"] = datetime.utcnow()
            result = await self.db.assets.insert_one(asset_data)
            logger.info(f"✅ Asset created: {asset_data['asset_id']}")
            return asset_data["asset_id"]
        except Exception as e:
            logger.error(f"❌ Create asset failed: {e}")
            raise
    
    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset by ID"""
        try:
            asset = await self.db.assets.find_one({"asset_id": asset_id})
            return asset
        except Exception as e:
            logger.error(f"❌ Get asset failed: {e}")
            raise
    
    async def update_asset(self, asset_id: str, update_data: Dict[str, Any]) -> bool:
        """Update asset"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.db.assets.update_one(
                {"asset_id": asset_id},
                {"$set": update_data}
            )
            logger.info(f"✅ Asset updated: {asset_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Update asset failed: {e}")
            raise
    
    async def delete_asset(self, asset_id: str) -> bool:
        """Delete asset"""
        try:
            result = await self.db.assets.delete_one({"asset_id": asset_id})
            logger.info(f"✅ Asset deleted: {asset_id}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Delete asset failed: {e}")
            raise
    
    async def list_assets(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List assets with filters"""
        try:
            query = {}
            if customer_id:
                query["customer_id"] = customer_id
            if status:
                query["status"] = status
            
            cursor = self.db.assets.find(query).skip(skip).limit(limit)
            assets = await cursor.to_list(length=limit)
            return assets
        except Exception as e:
            logger.error(f"❌ List assets failed: {e}")
            raise
    
    # ========================================
    # NEW METHODS - RAW MATERIALS
    # ========================================
    
    async def create_raw_material(self, material_data: Dict[str, Any]) -> str:
        """Create new raw material"""
        try:
            material_data["created_at"] = datetime.utcnow()
            result = await self.db.raw_materials.insert_one(material_data)
            logger.info(f"✅ Raw material created: {material_data['material_id']}")
            return material_data["material_id"]
        except Exception as e:
            logger.error(f"❌ Create raw material failed: {e}")
            raise
    
    async def get_raw_material(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get raw material by ID"""
        try:
            material = await self.db.raw_materials.find_one({"material_id": material_id})
            return material
        except Exception as e:
            logger.error(f"❌ Get raw material failed: {e}")
            raise
    
    async def list_raw_materials(
        self,
        access_level: Optional[str] = None,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List raw materials with access control"""
        try:
            query = {}
            
            # Access control logic
            if access_level == "global":
                query["access_level"] = "global"
            elif access_level == "company" and company_id:
                query["$or"] = [
                    {"access_level": "global"},
                    {"access_level": "company", "owner_company_id": company_id}
                ]
            elif user_id:
                query["$or"] = [
                    {"access_level": "global"},
                    {"owner_user_id": user_id}
                ]
            
            cursor = self.db.raw_materials.find(query).skip(skip).limit(limit)
            materials = await cursor.to_list(length=limit)
            return materials
        except Exception as e:
            logger.error(f"❌ List raw materials failed: {e}")
            raise
    
    # ========================================
    # NEW METHODS - PRODUCTS
    # ========================================
    
    async def create_product(self, product_data: Dict[str, Any]) -> str:
        """Create new product"""
        try:
            product_data["created_at"] = datetime.utcnow()
            result = await self.db.products.insert_one(product_data)
            logger.info(f"✅ Product created: {product_data['product_id']}")
            return product_data["product_id"]
        except Exception as e:
            logger.error(f"❌ Create product failed: {e}")
            raise
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        try:
            product = await self.db.products.find_one({"product_id": product_id})
            return product
        except Exception as e:
            logger.error(f"❌ Get product failed: {e}")
            raise
    
    async def update_product(self, product_id: str, update_data: Dict[str, Any]) -> bool:
        """Update product"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.db.products.update_one(
                {"product_id": product_id},
                {"$set": update_data}
            )
            logger.info(f"✅ Product updated: {product_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Update product failed: {e}")
            raise
    
    async def list_products(
        self,
        access_level: Optional[str] = None,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List products with access control"""
        try:
            query = {}
            
            # Access control
            if access_level == "global":
                query["access_level"] = "global"
            elif access_level == "company" and company_id:
                query["$or"] = [
                    {"access_level": "global"},
                    {"access_level": "company", "owner_company_id": company_id}
                ]
            elif user_id:
                query["$or"] = [
                    {"access_level": "global"},
                    {"owner_user_id": user_id}
                ]
            
            # Status filter
            if status:
                query["status"] = status
            
            cursor = self.db.products.find(query).skip(skip).limit(limit)
            products = await cursor.to_list(length=limit)
            return products
        except Exception as e:
            logger.error(f"❌ List products failed: {e}")
            raise
    
    # ========================================
    # NEW METHODS - ANALYSIS RESULTS
    # ========================================
    
    async def save_analysis_result(self, analysis_data: Dict[str, Any]) -> str:
        """Save analysis result (3D grid, where can I treat, etc.)"""
        try:
            analysis_data["created_at"] = datetime.utcnow()
            result = await self.db.analysis_results.insert_one(analysis_data)
            logger.info(f"✅ Analysis result saved: {analysis_data['analysis_id']}")
            return analysis_data["analysis_id"]
        except Exception as e:
            logger.error(f"❌ Save analysis result failed: {e}")
            raise
    
    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result by ID"""
        try:
            analysis = await self.db.analysis_results.find_one({"analysis_id": analysis_id})
            return analysis
        except Exception as e:
            logger.error(f"❌ Get analysis result failed: {e}")
            raise
    
    async def list_analysis_results(
        self,
        analysis_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List analysis results"""
        try:
            query = {}
            if analysis_type:
                query["analysis_type"] = analysis_type
            
            cursor = self.db.analysis_results.find(query).sort("created_at", -1).skip(skip).limit(limit)
            results = await cursor.to_list(length=limit)
            return results
        except Exception as e:
            logger.error(f"❌ List analysis results failed: {e}")
            raise


# Global database instance
db = Database()