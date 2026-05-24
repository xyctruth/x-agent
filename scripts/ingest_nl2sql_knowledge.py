import sys

from x_agent.core.config import get_settings
from x_agent.main import create_nl2sql_knowledge_ingest_service, create_nl2sql_knowledge_items


def main() -> int:
    settings = get_settings()
    items = create_nl2sql_knowledge_items(settings)
    service = create_nl2sql_knowledge_ingest_service(settings)
    result = service.ingest(items)
    sys.stdout.write(
        f"Ingested {result.item_count} NL2SQL knowledge items into "
        f"Qdrant collection {settings.qdrant_collection}\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
