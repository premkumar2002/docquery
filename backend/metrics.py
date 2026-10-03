from prometheus_client import Counter, Histogram


DOCUMENT_UPLOADS = Counter(
    "docuquery_document_uploads_total",
    "Number of document upload attempts.",
    ["status"],
)

CHUNKS_CREATED = Counter(
    "docuquery_chunks_created_total",
    "Number of document chunks created successfully.",
)

QUERIES = Counter(
    "docuquery_queries_total",
    "Number of document query attempts.",
    ["status"],
)

QUERY_LATENCY = Histogram(
    "docuquery_query_latency_seconds",
    "Time spent answering document queries.",
)
