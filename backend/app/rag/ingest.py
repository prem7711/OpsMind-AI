"""Seeds the Chroma knowledge base (+ Postgres KnowledgeBaseDoc metadata) with a representative
slice of operational guidance per technology. Full-corpus ingestion of the official docs is a
follow-up; this gives search_knowledge_base real, useful content to retrieve for the demo.

Run: python -m app.rag.ingest
"""
import hashlib

from app.db.base import Base, SessionLocal, engine
from app.db.models import KnowledgeBaseDoc
from app.rag.retriever import get_vectorstore

SEED_DOCS = [
    ("kubernetes", "CrashLoopBackOff means a container keeps crashing after start. Check `kubectl describe pod` "
        "for the last termination reason (often OOMKilled or a failing readiness/liveness probe) and "
        "`kubectl logs --previous` for the crash output before assuming a code bug."),
    ("kubernetes", "OOMKilled events mean the container exceeded its memory limit. Raise the memory limit, "
        "fix a leak, or reduce heap/cache size; check `kubectl top pod` for actual usage versus the configured limit."),
    ("kubernetes", "A Deployment with available replicas below desired usually means the pods are failing "
        "readiness checks or the rollout is stuck; check ReplicaSet events and pod status, not just Deployment status."),
    ("docker", "A container that exits immediately after start typically has its entrypoint process "
        "crashing; run `docker logs <id>` and check the exit code — 137 usually means it was OOM-killed by the host or cgroup limit."),
    ("docker", "High image build/pull latency during an incident can cause slow pod rollout; check registry "
        "reachability and image layer caching before assuming the app itself is slow to start."),
    ("postgresql", "A high number of active connections near max_connections causes new connections to be "
        "refused. Use a connection pooler (PgBouncer) and check for connection leaks in the app before raising max_connections."),
    ("postgresql", "Slow queries missing a WHERE clause or using SELECT * on large tables often cause full "
        "table scans; check `EXPLAIN ANALYZE` and add covering indexes on filtered/sorted columns."),
    ("postgresql", "Lock contention (many queries waiting on the same row/table) shows up as rising query "
        "latency with steady CPU; query `pg_locks` and `pg_stat_activity` to find the blocking transaction."),
    ("redis", "Sudden latency spikes in Redis are often caused by a large blocking command (KEYS, a big "
        "SORT, or a big DEL) or by hitting the maxmemory limit and triggering eviction; prefer SCAN over KEYS."),
    ("redis", "Redis maxmemory reached with an eviction policy of noeviction causes writes to fail outright; "
        "either raise maxmemory or switch policy, and check for unexpectedly large keys with `MEMORY USAGE`."),
    ("kafka", "Consumer lag that keeps growing means consumers are slower than producers; scale consumer "
        "instances (up to partition count) or investigate a slow downstream call inside the consumer loop."),
    ("kafka", "A crashed or rebalancing consumer group causes temporary lag spikes and duplicate processing; "
        "check consumer group state and session/heartbeat timeout configuration before assuming a data bug."),
    ("spring_boot", "A Spring Boot app failing readiness after a deploy is often a bean failing to initialize "
        "(bad DB URL, missing env var) — check the actuator /health endpoint and startup logs for the first stack trace, not the last."),
    ("spring_boot", "Thread pool exhaustion in a Spring Boot service (all Tomcat threads busy) shows as "
        "rising response time with steady CPU; check for a slow downstream call without a timeout holding threads."),
    ("go", "A goroutine leak (unbounded growth in `runtime.NumGoroutine()`) is often caused by a channel "
        "send/receive with no corresponding receiver/sender or a missing context cancellation; use pprof's goroutine profile to find the stuck stack."),
    ("go", "High GC pause times in a Go service usually mean excessive allocation; check pprof heap profile "
        "for allocation hotspots before tuning GOGC."),
    ("prometheus", "A metric plateauing at a fixed ceiling with the app otherwise unhealthy can mean the "
        "scrape itself is failing (target down) rather than the underlying value being flat — check `up{job=...}`."),
    ("prometheus", "Sudden gaps in a metric's timeseries usually indicate a scrape failure or target restart, "
        "not necessarily that the underlying system value dropped to zero."),
]


def ingest():
    Base.metadata.create_all(bind=engine)
    vectorstore = get_vectorstore()
    db = SessionLocal()
    try:
        texts, metadatas, ids = [], [], []
        for source_name, text in SEED_DOCS:
            chunk_id = hashlib.sha256(text.encode()).hexdigest()[:16]
            existing = db.query(KnowledgeBaseDoc).filter_by(chunk_id=chunk_id).first()
            if existing:
                continue
            texts.append(text)
            metadatas.append({"source_name": source_name, "doc_type": "operational_note"})
            ids.append(chunk_id)
            db.add(
                KnowledgeBaseDoc(
                    chunk_id=chunk_id, source_name=source_name, doc_type="operational_note", chunk_text=text
                )
            )
        if texts:
            vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        db.commit()
        print(f"Ingested {len(texts)} new chunks ({len(SEED_DOCS) - len(texts)} already present).")
    finally:
        db.close()


if __name__ == "__main__":
    ingest()
