from datetime import datetime, timezone
from decimal import Decimal

from bson.decimal128 import Decimal128
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, ReturnDocument


def utcnow():
    return datetime.now(timezone.utc)


class CallRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.calls

    async def ensure_indexes(self):
        await self.collection.create_index("call_id", unique=True)
        await self.collection.create_index("provider_call_id", unique=True, sparse=True)
        await self.collection.create_index([("created_at", DESCENDING)])
        await self.collection.create_index([("stage_code", ASCENDING), ("status", ASCENDING)])
        await self.collection.create_index("customer.customer_id")

    async def create(self, document: dict):
        await self.collection.insert_one(document)

    async def update_trigger(self, call_id: str, provider_call_id: str):
        await self.collection.update_one(
            {"call_id": call_id},
            {"$set": {"provider_call_id": provider_call_id, "status": "triggered", "updated_at": utcnow()}},
        )

    async def mark_trigger_failed(self, call_id: str, reason: str):
        await self.collection.update_one(
            {"call_id": call_id},
            {"$set": {"status": "trigger_failed", "trigger_error": reason, "updated_at": utcnow()}},
        )

    async def apply_webhook(self, call_id: str, delivery_id: str, update: dict):
        return await self.collection.find_one_and_update(
            {"call_id": call_id, "webhook_ids": {"$ne": delivery_id}},
            {"$set": update, "$addToSet": {"webhook_ids": delivery_id}},
            return_document=ReturnDocument.AFTER,
        )

    async def get(self, call_id: str):
        return await self.collection.find_one({"call_id": call_id})

    async def list(self, filters: dict, limit: int, offset: int):
        query = {}
        if filters.get("stage_code"):
            query["stage_code"] = filters["stage_code"]
        if filters.get("status"):
            query["status"] = filters["status"]
        if filters.get("search"):
            search = filters["search"]
            query["$or"] = [
                {"customer.customer_name": {"$regex": search, "$options": "i"}},
                {"customer.customer_id": {"$regex": search, "$options": "i"}},
                {"emi.loan_account": {"$regex": search, "$options": "i"}},
            ]
        cursor = self.collection.find(query).sort("created_at", DESCENDING).skip(offset).limit(limit)
        return await cursor.to_list(length=limit), await self.collection.count_documents(query)

    async def summary(self):
        pipeline = [{"$group": {"_id": "$stage_code", "count": {"$sum": 1}, "amount": {"$sum": "$emi.amount"}}}]
        stages = {row["_id"]: row for row in await self.collection.aggregate(pipeline).to_list(None)}
        total = sum(row["count"] for row in stages.values())
        amount = sum(
            (row["amount"].to_decimal() if isinstance(row["amount"], Decimal128) else Decimal(str(row["amount"])))
            for row in stages.values()
        )
        return {"total_calls": total, "total_amount": amount, "stages": stages}
