from x_agent.application.nl2sql import SqlKnowledgeBase
from x_agent.domain.nl2sql import SqlKnowledgeItem, SqlRetrievalPlanStep


class CompositeSqlKnowledgeBase:
    def __init__(self, *, knowledge_bases: tuple[SqlKnowledgeBase, ...]) -> None:
        self.knowledge_bases = knowledge_bases

    def search(self, step: SqlRetrievalPlanStep) -> tuple[SqlKnowledgeItem, ...]:
        items_by_id: dict[str, SqlKnowledgeItem] = {}
        for knowledge_base in self.knowledge_bases:
            for item in knowledge_base.search(step):
                items_by_id.setdefault(item.id, item)
        return tuple(items_by_id.values())
